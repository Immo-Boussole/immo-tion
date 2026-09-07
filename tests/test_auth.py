"""Tests for authentication, first-launch setup wizard, i18n, and Bearer token security."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db_connection, get_bridge_api_token, get_user_count

client = TestClient(app, follow_redirects=False)


def setup_module():
    """Ensure a clean database state for auth test suite."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("DELETE FROM users")
            conn.execute("DELETE FROM properties")
            conn.execute("DELETE FROM app_settings")
    finally:
        conn.close()


def test_first_launch_redirects_to_setup():
    """When no users exist, any protected page must redirect to /setup."""
    assert get_user_count() == 0
    res = client.get("/")
    assert res.status_code == 303
    assert res.headers["location"] == "/setup"

    res_alias = client.get("/setup-admin")
    assert res_alias.status_code == 307
    assert res_alias.headers["location"] == "/setup"

    res_setup = client.get("/setup")
    assert res_setup.status_code == 200
    assert "Configuration Initiale" in res_setup.text
    assert "admin_username" in res_setup.text or "Identifiant administrateur" in res_setup.text


def test_setup_step1_and_step2():
    """Complete step 1 and step 2 of initial setup."""
    # Step 1: Create local admin
    step1_data = {
        "username": "superadmin",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "email": "admin@immo-tion.local",
        "default_language": "fr",
    }
    res_s1 = client.post("/setup/step1", data=step1_data)
    assert res_s1.status_code == 303
    assert res_s1.headers["location"] == "/setup?step=2"

    # Step 2: Create initial property
    step2_data = {
        "property_name": "Maison Setup",
        "property_city": "Lyon",
        "property_address": "10 Rue de la Paix",
    }
    res_s2 = client.post("/setup/step2", data=step2_data)
    assert res_s2.status_code == 303
    assert res_s2.headers["location"] == "/"

    # Now users exist
    assert get_user_count() == 1

    # Session is authenticated, / renders 200
    dash_res = client.get("/")
    assert dash_res.status_code == 200
    assert "Maison Setup" in dash_res.text


def test_logout_and_protected_redirection():
    """Logging out must redirect to login, and unauthenticated access redirects to /login."""
    logout_res = client.get("/logout")
    assert logout_res.status_code == 303
    assert logout_res.headers["location"] == "/login"

    # Now accessing / should redirect to /login
    protected_res = client.get("/")
    assert protected_res.status_code == 303
    assert "/login" in protected_res.headers["location"]


def test_login_validation():
    """Verify login authentication flow."""
    # Wrong password
    bad_res = client.post("/login", data={"username": "superadmin", "password": "WrongPassword"})
    assert bad_res.status_code == 401
    assert "incorrect" in bad_res.text.lower()

    # Valid credentials
    good_res = client.post("/login", data={"username": "superadmin", "password": "Password123!"})
    assert good_res.status_code == 303
    assert good_res.headers["location"] == "/"

    # Follow to dashboard
    dash_res = client.get("/")
    assert dash_res.status_code == 200
    assert "superadmin" in dash_res.text


def test_language_switch():
    """Verify switching language via /lang/en and /lang/fr."""
    # Switch to English
    lang_en = client.get("/lang/en", headers={"referer": "/"})
    assert lang_en.status_code == 303

    # Check that dashboard now has English translations
    en_dash = client.get("/")
    assert en_dash.status_code == 200
    assert "Dashboard" in en_dash.text or "Welcome" in en_dash.text

    # Switch back to French
    lang_fr = client.get("/lang/fr", headers={"referer": "/"})
    assert lang_fr.status_code == 303

    fr_dash = client.get("/")
    assert fr_dash.status_code == 200
    assert "Tableau de bord" in fr_dash.text or "Bienvenue" in fr_dash.text


def test_bridge_api_token_security():
    """Verify Bridge endpoint requires Bearer token."""
    token = get_bridge_api_token()
    assert token is not None and len(token) > 10

    payload = {
        "title": "Bien Sécurisé Bridge",
        "address": "1 Avenue de la Gare",
        "city": "Marseille",
        "surface_m2": 85.0,
    }

    # 1. Without token -> 401
    unauth_res = client.post("/api/v1/bridge/import-listing", json=payload)
    assert unauth_res.status_code == 401

    # 2. With wrong token -> 401
    bad_token_res = client.post(
        "/api/v1/bridge/import-listing",
        json=payload,
        headers={"Authorization": "Bearer bad-token-12345"},
    )
    assert bad_token_res.status_code == 401

    # 3. With correct token -> 201 Created
    good_res = client.post(
        "/api/v1/bridge/import-listing",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert good_res.status_code == 201
    assert good_res.json()["status"] == "success"


def test_profile_and_admin_pages():
    """Verify profile and admin settings render with active session."""
    prof_res = client.get("/profile")
    assert prof_res.status_code == 200
    assert "Mon Profil" in prof_res.text
    assert "superadmin" in prof_res.text

    admin_res = client.get("/admin/settings")
    assert admin_res.status_code == 200
    assert "Administration" in admin_res.text
    assert "adminBridgeToken" in admin_res.text


def test_admin_user_creation_and_duplicate_prevention():
    """Verify user creation, duplicate error handling, and self-deletion prevention."""
    # 1. GET /admin/users/create redirects to /admin/settings
    get_res = client.get("/admin/users/create", follow_redirects=False)
    assert get_res.status_code == 303
    assert get_res.headers["location"] == "/admin/settings"

    # 2. Create user with short username -> error redirect
    short_res = client.post(
        "/admin/users/create",
        data={"username": "ab", "password": "password123", "role": "user"},
        follow_redirects=False,
    )
    assert short_res.status_code == 303
    assert "error=" in short_res.headers["location"]

    # 3. Create a valid user -> success redirect
    create_res = client.post(
        "/admin/users/create",
        data={"username": "testagent", "password": "agentpassword123", "role": "user", "email": "agent@test.com"},
        follow_redirects=False,
    )
    assert create_res.status_code == 303
    assert "success=" in create_res.headers["location"]

    # 4. Attempt to create the same user again -> handles UNIQUE constraint and redirects with error (no 500!)
    dup_res = client.post(
        "/admin/users/create",
        data={"username": "testagent", "password": "differentpass123", "role": "user"},
        follow_redirects=False,
    )
    assert dup_res.status_code == 303
    assert "error=" in dup_res.headers["location"]
    assert "existe" in dup_res.headers["location"]

    # 5. Prevent deleting logged-in admin
    conn = get_db_connection()
    try:
        admin_user = conn.execute("SELECT id FROM users WHERE username = 'superadmin'").fetchone()
        agent_user = conn.execute("SELECT id FROM users WHERE username = 'testagent'").fetchone()
    finally:
        conn.close()

    self_del_res = client.post(f"/admin/users/{admin_user['id']}/delete", follow_redirects=False)
    assert self_del_res.status_code == 303
    assert "error=" in self_del_res.headers["location"]

    # 6. Delete testagent user -> success
    del_res = client.post(f"/admin/users/{agent_user['id']}/delete", follow_redirects=False)
    assert del_res.status_code == 303
    assert "success=" in del_res.headers["location"]



def teardown_module():
    """Clean up users and properties so the development database remains ready for setup."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("DELETE FROM users")
            conn.execute("DELETE FROM properties")
            conn.execute("DELETE FROM app_settings")
    finally:
        conn.close()
