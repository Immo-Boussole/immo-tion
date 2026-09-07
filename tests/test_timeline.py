"""Unit tests for property timeline aggregation and temporal compression."""

import datetime
from app.timeline import (
    parse_date,
    format_french_date,
    get_relative_time_label,
    format_gap_label,
    get_property_timeline,
)
from app.database import get_db_connection


def test_timeline_date_parsers():
    """Verify parsing and formatting helpers."""
    d = datetime.date(2025, 6, 15)
    assert parse_date("2025-06-15") == d
    assert parse_date("2025-06-15T14:30:00Z") == d
    assert parse_date(d) == d
    assert parse_date(None) is None
    assert parse_date("invalid") is None

    assert "15" in format_french_date(d)
    assert "2025" in format_french_date(d)


def test_relative_time_labels():
    """Verify relative time formatting."""
    today = datetime.date(2026, 9, 7)
    assert get_relative_time_label(today, today) == "Aujourd'hui"
    assert get_relative_time_label(today + datetime.timedelta(days=1), today) == "Demain"
    assert get_relative_time_label(today - datetime.timedelta(days=1), today) == "Hier"
    assert "Dans 10 jours" in get_relative_time_label(today + datetime.timedelta(days=10), today)
    assert "Il y a 10 jours" in get_relative_time_label(today - datetime.timedelta(days=10), today)
    assert "Dans 3 mois" in get_relative_time_label(today + datetime.timedelta(days=90), today)
    assert "Il y a 3 mois" in get_relative_time_label(today - datetime.timedelta(days=90), today)


def test_gap_compression_labels():
    """Verify gap compression calculation."""
    assert format_gap_label(75) == "+2 mois"
    assert format_gap_label(180) == "+6 mois"
    assert "+1 an" in format_gap_label(400)


def test_get_property_timeline_empty_property():
    """Ensure an empty or non-existent property still generates a valid timeline with the 'Now' node."""
    res = get_property_timeline(999999)
    assert "items" in res
    assert res["total_events"] == 0
    # Must contain at least the 'now' node
    assert any(item["type"] == "now" for item in res["items"])


def test_get_property_timeline_with_events():
    """Verify timeline populates past and future events, injects 'now', and compresses gaps."""
    conn = get_db_connection()
    try:
        with conn:
            # Create a test property
            cur = conn.execute(
                """
                INSERT INTO properties (name, address, city, acquisition_date, acquisition_price)
                VALUES ('Villa Test', '10 Rue de la Paix', 'Nice', '2024-01-15', 350000)
                """
            )
            prop_id = cur.lastrowid

            # Past maintenance task + log
            task_cur = conn.execute(
                """
                INSERT INTO maintenance_tasks (property_id, title, category, next_due_date)
                VALUES (?, 'Ramonage cheminée', 'Chauffage', '2027-01-15')
                """,
                (prop_id,),
            )
            task_id = task_cur.lastrowid

            conn.execute(
                """
                INSERT INTO maintenance_logs (task_id, property_id, performed_date, performed_by, cost)
                VALUES (?, ?, '2024-06-20', 'Ramonage Express', 120.0)
                """,
                (task_id, prop_id),
            )

            # Renovation project
            conn.execute(
                """
                INSERT INTO renovations (property_id, title, category, status, start_date, end_date, actual_cost)
                VALUES (?, 'Isolation Combles', 'Isolation', 'Terminé', '2025-02-01', '2025-02-15', 4500.0)
                """,
                (prop_id,),
            )

            # Equipment item with warranty
            conn.execute(
                """
                INSERT INTO inventory (property_id, name, brand, purchase_date, warranty_expiry_date)
                VALUES (?, 'Pompe à chaleur', 'Daikin', '2024-03-01', '2029-03-01')
                """,
                (prop_id,),
            )

        timeline = get_property_timeline(prop_id)

        assert timeline["total_events"] >= 5
        assert timeline["past_count"] >= 3
        assert timeline["future_count"] >= 2

        # Check 'now' node
        now_items = [i for i in timeline["items"] if i.get("type") == "now"]
        assert len(now_items) == 1
        assert now_items[0]["title"] == "Aujourd'hui"

        # Check gap compression: since 2024 to 2025 to 2026 to 2027/2029 has gaps > 60 days
        gap_items = [i for i in timeline["items"] if i.get("type") == "gap"]
        assert len(gap_items) >= 1
        assert all("+" in g["label"] for g in gap_items)

        # Check categories
        cat_ids = [c["id"] for c in timeline["categories"]]
        assert "all" in cat_ids
        assert "maintenance" in cat_ids
        assert "renovation" in cat_ids
        assert "inventory" in cat_ids
        assert "property" in cat_ids

    finally:
        # Cleanup
        with conn:
            conn.execute("DELETE FROM properties WHERE id = ?", (prop_id,))
        conn.close()
