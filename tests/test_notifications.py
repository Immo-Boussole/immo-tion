"""Comprehensive test suite for Immo-Tion notifications system."""

import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.auth import hash_password
from app.database import (
    get_db_connection,
    create_notification,
    get_notifications,
    get_unread_notifications_count,
    mark_notification_read,
    mark_notification_unread,
    mark_all_notifications_read,
    delete_notification,
    is_event_already_notified,
    cleanup_expired_notifications,
)
from app.notifier import dispatch_notification, send_test_notification, _send_via_apprise
from app.scheduler import run_deadline_evaluations_and_notify

client = TestClient(app)
TEST_USERNAME = "notiftester"
TEST_PASSWORD = "NotifPassword123!"


def setup_module():
    """Create test admin user and log in client."""
    conn = get_db_connection()
    try:
        with conn:
            pwd_hash, salt = hash_password(TEST_PASSWORD)
            conn.execute(
                """
                INSERT OR IGNORE INTO users (username, password_hash, salt, role, apprise_url, auto_read_after_days)
                VALUES (?, ?, ?, 'admin', 'discord://12345/abcdef', 15)
                """,
                (TEST_USERNAME, pwd_hash, salt),
            )
    finally:
        conn.close()

    client.post("/login", data={"username": TEST_USERNAME, "password": TEST_PASSWORD})


def test_notification_database_crud():
    """Test database helper functions for notifications."""
    conn = get_db_connection()
    try:
        with conn:
            cur = conn.execute("INSERT INTO properties (name, address) VALUES ('Notif Prop', '10 Rue des Alertes')")
            prop_id = cur.lastrowid
    finally:
        conn.close()

    # 1. Create notification
    notif_id = create_notification(
        title="Test Entretien",
        message="Chaudière à vérifier",
        category="maintenance",
        property_id=prop_id,
        link_url="/maintenance",
        event_key=f"test:crud:{prop_id}",
    )
    assert notif_id > 0

    # 2. Check deduplication helper
    assert is_event_already_notified(f"test:crud:{prop_id}") is True
    assert is_event_already_notified("non_existent_key") is False

    # 3. Retrieve notifications
    notifs = get_notifications(category="maintenance")
    assert any(n["id"] == notif_id for n in notifs)

    # 4. Check unread count
    cnt = get_unread_notifications_count()
    assert cnt >= 1

    # 5. Mark as read
    assert mark_notification_read(notif_id) is True
    notifs_after = get_notifications(unread_only=True)
    assert not any(n["id"] == notif_id for n in notifs_after)

    # 6. Mark as unread
    assert mark_notification_unread(notif_id) is True
    notifs_unread = get_notifications(unread_only=True)
    assert any(n["id"] == notif_id for n in notifs_unread)

    # 7. Mark all as read
    marked = mark_all_notifications_read(category="maintenance")
    assert marked >= 1

    # 8. Delete notification
    assert delete_notification(notif_id) is True


def test_notification_deduplication():
    """Verify that dispatching with an existing event_key does not create duplicates."""
    event_key = f"unique_event_{datetime.datetime.now().timestamp()}"

    # First dispatch
    notif_id1 = create_notification(
        title="First", message="Message 1", category="system", event_key=event_key
    )
    assert notif_id1 > 0

    # Second check
    assert is_event_already_notified(event_key) is True


def test_apprise_test_and_mocked_dispatch():
    """Verify Apprise dispatcher logic with mocks."""
    with patch("apprise.Apprise") as MockApprise:
        mock_instance = MagicMock()
        mock_instance.notify.return_value = True
        MockApprise.return_value = mock_instance

        # Test _send_via_apprise
        res = _send_via_apprise("discord://12345/token", "Test Title", "Test Body")
        assert res is True
        mock_instance.add.assert_called_with("discord://12345/token")
        mock_instance.notify.assert_called_with(title="Test Title", body="Test Body")

        # Test empty URL returns False
        assert _send_via_apprise("", "Title", "Body") is False


def test_notifications_http_endpoints():
    """Test all notification-related web and API routes."""
    # 1. Access notifications list page
    res = client.get("/notifications")
    assert res.status_code == 200
    assert "Centre de Notifications" in res.text or "Notifications" in res.text

    # 2. Filter by category
    res = client.get("/notifications?category=maintenance")
    assert res.status_code == 200

    # 3. Create a test notification in DB for API actions
    notif_id = create_notification(
        title="API Test",
        message="Testing HTTP routes",
        category="system",
        event_key=f"api_test_{datetime.datetime.now().timestamp()}",
    )

    # 4. Mark read via API
    res = client.post(f"/api/v1/notifications/{notif_id}/read")
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 5. Mark unread via API
    res = client.post(f"/api/v1/notifications/{notif_id}/unread")
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 6. Unread count endpoint
    res = client.get("/api/v1/notifications/unread-count")
    assert res.status_code == 200
    assert "unread_count" in res.json()

    # 7. Read all via API
    res = client.post("/api/v1/notifications/read-all", data={"category": "system"})
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 8. Delete via API
    res = client.post(f"/api/v1/notifications/{notif_id}/delete")
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 9. Test Apprise endpoint with mock
    with patch("app.notifier._send_via_apprise", return_value=True):
        res = client.post("/api/v1/notifications/test", data={"apprise_url": "discord://test/123"})
        assert res.status_code == 200
        assert res.json()["success"] is True

    # 10. Admin trigger-check endpoint
    res = client.post("/api/v1/notifications/trigger-check")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert "results" in res.json()


def test_scheduled_deadline_evaluations_and_milestones():
    """Verify that run_deadline_evaluations_and_notify identifies due dates correctly."""
    conn = get_db_connection()
    today = datetime.date.today()
    in_5_days = (today + datetime.timedelta(days=5)).isoformat()
    overdue_3_days = (today - datetime.timedelta(days=3)).isoformat()

    try:
        with conn:
            cur = conn.execute("INSERT INTO properties (name, address) VALUES ('Scheduler Test Prop', '1 Rue du Test')")
            prop_id = cur.lastrowid

            # Maintenance task due in 5 days (J-7 milestone)
            conn.execute(
                """
                INSERT INTO maintenance_tasks (property_id, title, category, next_due_date)
                VALUES (?, 'Vérification Extincteur', 'Sécurité', ?)
                """,
                (prop_id, in_5_days),
            )

            # Tax overdue by 3 days
            conn.execute(
                """
                INSERT INTO taxes (property_id, tax_year, tax_type, amount, due_date, status)
                VALUES (?, 2026, 'Taxe Foncière', 1200.0, ?, 'À payer')
                """,
                (prop_id, overdue_3_days),
            )
    finally:
        conn.close()

    # Trigger scanner
    res = client.post("/api/v1/notifications/trigger-check")
    assert res.status_code == 200
    results = res.json()["results"]
    assert results["maintenance"] >= 1
    assert results["taxes"] >= 1

    # Second immediate run should be deduplicated (0 new notifications for same milestones)
    res2 = client.post("/api/v1/notifications/trigger-check")
    results2 = res2.json()["results"]
    assert results2["maintenance"] == 0
    assert results2["taxes"] == 0


def test_profile_notifications_settings_update():
    """Test updating user's Apprise URL and auto-read threshold via /profile/details."""
    res = client.post(
        "/profile/details",
        data={
            "email": "user@notif.local",
            "apprise_url": "tgram://my_bot_token/my_chat_id",
            "auto_read_after_days": 14,
        },
    )
    assert res.status_code == 200

    conn = get_db_connection()
    try:
        u = conn.execute("SELECT * FROM users WHERE username = ?", (TEST_USERNAME,)).fetchone()
        assert u["email"] == "user@notif.local"
        assert u["apprise_url"] == "tgram://my_bot_token/my_chat_id"
        assert u["auto_read_after_days"] == 14
    finally:
        conn.close()
