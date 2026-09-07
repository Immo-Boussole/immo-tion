"""Integration and unit tests for Property Taxes & Fiscal module."""

import io
import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.auth import hash_password
from app.database import get_db_connection
from app.timeline import get_property_timeline

client = TestClient(app)


def setup_module():
    """Ensure test user exists and authenticate client."""
    conn = get_db_connection()
    try:
        with conn:
            pwd_hash, salt = hash_password("TaxTestPwd123!")
            conn.execute(
                "INSERT OR IGNORE INTO users (username, password_hash, salt, role) VALUES ('taxtester', ?, ?, 'admin')",
                (pwd_hash, salt),
            )
    finally:
        conn.close()

    client.post("/login", data={"username": "taxtester", "password": "TaxTestPwd123!"})


def test_taxes_unauthenticated():
    """Verify unauthenticated access to /taxes redirects to /login."""
    anon_client = TestClient(app)
    response = anon_client.get("/taxes", follow_redirects=False)
    assert response.status_code == 303
    assert "/login" in response.headers["location"]


def test_taxes_lifecycle_and_timeline():
    """Test creating a tax record, PDF upload, YoY calculation, timeline event, and deletion."""
    conn = get_db_connection()
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO properties (name, address, city) VALUES ('Tax Test House', '12 Rue Fiscale', 'Paris')"
            )
            prop_id = cur.lastrowid
    finally:
        conn.close()

    # 1. Render empty taxes dashboard for this property
    res = client.get(f"/taxes?property_id={prop_id}")
    assert res.status_code == 200
    assert "Fiscalité &amp; Taxes Foncières" in res.text or "Fiscalité" in res.text

    # 2. Add tax record for 2024 (1000 €, TEOM 150 €)
    res = client.post(
        "/taxes",
        data={
            "property_id": prop_id,
            "tax_year": 2024,
            "tax_type": "Taxe Foncière",
            "amount": 1000.0,
            "teom_amount": 150.0,
            "due_date": "2024-10-15",
            "status": "Payé",
            "reference_number": "ROLE-2024-001",
            "notes": "Avis foncier 2024 payé",
        },
        follow_redirects=False,
    )
    assert res.status_code == 303

    # 3. Add tax record for 2025 (1150 €, TEOM 180 €) with simulated PDF file
    fake_pdf = io.BytesIO(b"%PDF-1.4 test tax notice content")
    fake_pdf.name = "tax_notice_2025.pdf"

    res = client.post(
        "/taxes",
        data={
            "property_id": prop_id,
            "tax_year": 2025,
            "tax_type": "Taxe Foncière",
            "amount": 1150.0,
            "teom_amount": 180.0,
            "due_date": "2025-10-15",
            "status": "Payé",
            "reference_number": "ROLE-2025-002",
            "notes": "Avis foncier 2025 avec TEOM",
        },
        files={"document": ("tax_notice_2025.pdf", fake_pdf, "application/pdf")},
        follow_redirects=False,
    )
    assert res.status_code == 303

    # 4. Verify dashboard rendering with YoY (+15%) and TEOM
    res = client.get(f"/taxes?property_id={prop_id}")
    assert res.status_code == 200
    assert "1 150" in res.text or "1150" in res.text
    assert "+15.0%" in res.text
    assert "180" in res.text
    assert "ROLE-2025-002" in res.text
    assert "tax_notice_2025.pdf" in res.text or "PDF" in res.text

    # 5. Verify auto-registration in documents table
    conn = get_db_connection()
    try:
        doc = conn.execute(
            "SELECT * FROM documents WHERE property_id = ? AND category = 'Fiscalité'",
            (prop_id,),
        ).fetchone()
        assert doc is not None
        assert "Avis Taxe Foncière 2025" in doc["title"]
    finally:
        conn.close()

    # 6. Verify timeline aggregation includes category 'tax'
    timeline = get_property_timeline(prop_id)
    tax_events = [ev for ev in timeline["items"] if ev.get("category") == "tax"]
    assert len(tax_events) == 2
    assert any("Taxe Foncière 2024" in ev["title"] for ev in tax_events)
    assert any("Taxe Foncière 2025" in ev["title"] for ev in tax_events)
    assert any(c["id"] == "tax" for c in timeline["categories"])

    # 7. Delete one tax notice
    conn = get_db_connection()
    try:
        tax_to_del = conn.execute("SELECT id FROM taxes WHERE property_id = ? AND tax_year = 2024", (prop_id,)).fetchone()
        tax_id = tax_to_del["id"]
    finally:
        conn.close()

    del_res = client.post(
        f"/taxes/{tax_id}/delete",
        data={"property_id": prop_id},
        follow_redirects=False,
    )
    assert del_res.status_code == 303

    # Verify deleted
    conn = get_db_connection()
    try:
        remaining = conn.execute("SELECT COUNT(*) as cnt FROM taxes WHERE property_id = ?", (prop_id,)).fetchone()
        assert remaining["cnt"] == 1
    finally:
        conn.close()
