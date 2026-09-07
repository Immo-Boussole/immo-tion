"""Unit tests for Cloudflare Tunnel origin security and header enforcement."""

import pytest
from starlette.testclient import TestClient

from app.main import app
from app.config import settings


def test_header_enforcement_disabled_by_default():
    """When REQUIRED_HEADERS is empty, requests pass through normally."""
    orig_headers = settings.REQUIRED_HEADERS
    try:
        settings.REQUIRED_HEADERS = ""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    finally:
        settings.REQUIRED_HEADERS = orig_headers


def test_header_enforcement_exempts_healthcheck():
    """Healthcheck endpoint must remain accessible for internal Docker probes."""
    orig_headers = settings.REQUIRED_HEADERS
    orig_exempt = settings.REQUIRED_HEADERS_EXEMPT_LOCALHOST
    try:
        settings.REQUIRED_HEADERS = "X-Origin-Verify:mysecret,CF-Ray"
        settings.REQUIRED_HEADERS_EXEMPT_LOCALHOST = False
        client = TestClient(app)
        # /health must be exempted regardless of caller host or missing headers
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    finally:
        settings.REQUIRED_HEADERS = orig_headers
        settings.REQUIRED_HEADERS_EXEMPT_LOCALHOST = orig_exempt


def test_header_enforcement_blocks_missing_or_invalid_headers():
    """Non-exempt requests lacking required headers or with wrong values get 403."""
    orig_headers = settings.REQUIRED_HEADERS
    orig_exempt = settings.REQUIRED_HEADERS_EXEMPT_LOCALHOST
    try:
        settings.REQUIRED_HEADERS = "X-Origin-Verify:supersecret,CF-Ray"
        settings.REQUIRED_HEADERS_EXEMPT_LOCALHOST = False
        client = TestClient(app)

        # 1. Missing headers entirely -> 403
        response = client.get("/api/v1/meta", headers={"host": "tion.example.com"})
        assert response.status_code == 403
        assert "Direct origin connection prohibited" in response.json()["detail"]

        # 2. Only CF-Ray present, missing X-Origin-Verify -> 403
        response = client.get("/api/v1/meta", headers={"CF-Ray": "123456789"})
        assert response.status_code == 403

        # 3. Invalid secret value -> 403
        response = client.get(
            "/api/v1/meta",
            headers={"CF-Ray": "123456789", "X-Origin-Verify": "wrongsecret"},
        )
        assert response.status_code == 403

        # 4. Correct headers and values -> 200
        response = client.get(
            "/api/v1/meta",
            headers={"CF-Ray": "123456789", "X-Origin-Verify": "supersecret"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Immo-Tion"
    finally:
        settings.REQUIRED_HEADERS = orig_headers
        settings.REQUIRED_HEADERS_EXEMPT_LOCALHOST = orig_exempt


def test_header_enforcement_localhost_exemption():
    """When REQUIRED_HEADERS_EXEMPT_LOCALHOST is True, local requests pass."""
    orig_headers = settings.REQUIRED_HEADERS
    orig_exempt = settings.REQUIRED_HEADERS_EXEMPT_LOCALHOST
    try:
        settings.REQUIRED_HEADERS = "X-Origin-Verify:supersecret"
        settings.REQUIRED_HEADERS_EXEMPT_LOCALHOST = True
        client = TestClient(app)

        # TestClient client.host is 'testclient', which is considered loopback/local
        response = client.get("/api/v1/meta")
        assert response.status_code == 200
    finally:
        settings.REQUIRED_HEADERS = orig_headers
        settings.REQUIRED_HEADERS_EXEMPT_LOCALHOST = orig_exempt
