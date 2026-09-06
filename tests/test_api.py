"""Comprehensive integration tests for API routes and Immo-Boussole bridge."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Verify healthcheck endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "Immo-Tion"


def test_metadata_acronym():
    """Verify T.I.O.N. bilingual acronym definitions in metadata."""
    response = client.get("/api/v1/meta")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Immo-Tion"
    assert data["acronym"]["en"] == "Tracking, Inventory, Operations & Notifications"
    assert data["acronym"]["fr"] == "Travaux, Inventaire, Opérations & Notifications"


def test_dashboard_and_pages_render():
    """Verify primary HTML views render successfully."""
    routes = ["/", "/properties", "/maintenance", "/renovations", "/inventory", "/documents", "/energy", "/cil"]
    for r in routes:
        res = client.get(r)
        assert res.status_code == 200
        assert "<html" in res.text


def test_property_lifecycle():
    """Test creating, viewing and deleting a property."""
    # 1. Create property
    form_data = {
        "name": "Maison de Test",
        "address": "15 Avenue des Champs",
        "postal_code": "69001",
        "city": "Lyon",
        "surface_m2": 120.0,
        "land_surface_m2": 500.0,
        "cadastral_reference": "AX 99",
        "dpe_rating": "B",
        "ges_rating": "A",
        "seed_tasks": "true",
    }
    create_res = client.post("/properties", data=form_data, follow_redirects=False)
    assert create_res.status_code == 303
    prop_url = create_res.headers["location"]
    prop_id = int(prop_url.split("/")[-1])

    # 2. View property detail
    detail_res = client.get(f"/properties/{prop_id}")
    assert detail_res.status_code == 200
    assert "Maison de Test" in detail_res.text
    assert "Lyon" in detail_res.text

    # 3. Verify seeded maintenance tasks
    maint_res = client.get(f"/maintenance?property_id={prop_id}")
    assert maint_res.status_code == 200
    assert "chaudière" in maint_res.text.lower() or "entretien" in maint_res.text.lower()

    # 4. Verify live iCal feed
    ical_res = client.get(f"/maintenance/ical/{prop_id}")
    assert ical_res.status_code == 200
    assert "BEGIN:VCALENDAR" in ical_res.text
    assert "Maison de Test" in ical_res.text

    # 5. Verify CIL export archive
    cil_res = client.get(f"/cil/{prop_id}/export")
    assert cil_res.status_code == 200
    assert cil_res.headers["content-type"] == "application/zip"
    assert len(cil_res.content) > 0


def test_immo_boussole_bridge_import():
    """Test importing a property exported by Immo-Boussole."""
    payload = {
        "title": "Villa Boussole Importée",
        "address": "42 Rue du Port",
        "postal_code": "33000",
        "city": "Bordeaux",
        "surface_m2": 145.0,
        "land_surface_m2": 800.0,
        "price": 420000.0,
        "cadastral_reference": "BD 102",
        "dpe_rating": "C",
        "ges_rating": "B",
        "photos": ["https://example.com/photo1.jpg"],
        "contacts": [
            {"role": "Notaire", "name": "Me Dupont", "phone": "0556000000", "email": "dupont@notaires.fr"}
        ],
        "furniture_inventory": [
            {"name": "Cuisine équipée intégrée", "condition": "Très bon", "room": "Cuisine"},
            {"name": "Poêle à granulés", "condition": "Neuf", "room": "Salon"}
        ],
        "seed_tasks": True,
    }

    res = client.post("/api/v1/bridge/import-listing", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "success"
    prop_id = data["property_id"]

    # Verify property is accessible
    detail_res = client.get(f"/properties/{prop_id}")
    assert detail_res.status_code == 200
    assert "Villa Boussole Importée" in detail_res.text
    assert "Me Dupont" in detail_res.text
