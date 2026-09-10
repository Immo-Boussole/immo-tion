"""Main FastAPI application entrypoint for Immo-Tion."""

import logging
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import init_db, get_user_count
from app.auth import is_authenticated
from app.translations import load_translations
from app.templates import templates
from app.routers import (
    auth,
    profile,
    admin,
    dashboard,
    properties,
    maintenance,
    renovations,
    inventory,
    documents,
    energy,
    cil,
    bridge,
    taxes,
    notifications,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for database initialization and cleanup."""
    import asyncio
    from app.scheduler import run_deadline_evaluations_and_notify

    init_db()
    load_translations()
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Launch background worker for periodic deadline evaluations and notification dispatch
    async def scheduled_notification_worker():
        await asyncio.sleep(2)
        while True:
            try:
                await run_deadline_evaluations_and_notify()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logging.getLogger("immo-tion.scheduler").error("Error in scheduled notification worker: %s", exc)
            await asyncio.sleep(86400)

    worker_task = asyncio.create_task(scheduled_notification_worker())
    try:
        yield
    finally:
        worker_task.cancel()


app = FastAPI(
    title=settings.APP_NAME,
    description="Immo-Tion: Home lifecycle management companion for Immo-Boussole (T.I.O.N. = Tracking, Inventory, Operations & Notifications).",
    version="0.1.0",
    lifespan=lifespan,
)

from starlette.middleware.base import BaseHTTPMiddleware


class AuthAndSetupMiddleware(BaseHTTPMiddleware):
    """Global access control middleware enforcing setup wizard and authentication."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Always allow static files, media, health check, metadata, and bridge API
        is_public = (
            path.startswith("/static")
            or path.startswith("/media")
            or path == "/health"
            or path == "/api/v1/meta"
            or path.startswith("/api/v1/bridge")
            or path.startswith("/lang/")
        )

        if is_public:
            return await call_next(request)

        user_count = get_user_count()

        # If no user exists, enforce redirect to /setup
        if user_count == 0:
            if not path.startswith("/setup") and not path.startswith("/setup-admin"):
                return RedirectResponse(url="/setup", status_code=303)
            return await call_next(request)

        # When users exist, /setup and /setup-admin are only allowed for authenticated admin
        if path.startswith("/setup") or path.startswith("/setup-admin"):
            if not is_authenticated(request):
                return RedirectResponse(url="/login", status_code=303)
            return await call_next(request)

        if path == "/login":
            return await call_next(request)

        if not is_authenticated(request):
            if path.startswith("/api/"):
                return JSONResponse(status_code=401, content={"detail": "Authentication required"})
            return RedirectResponse(url=f"/login?next={quote(path, safe='')}", status_code=303)

        return await call_next(request)


logger = logging.getLogger("immo-tion.security")


class HeaderEnforcementMiddleware(BaseHTTPMiddleware):
    """Enforces the presence and validity of required HTTP headers (e.g. from Cloudflare Tunnel).

    Protects against direct origin bypass when exposed behind Cloudflared or a reverse proxy.
    Exempts internal healthchecks, CORS preflights, and optionally localhost callers.
    """

    async def dispatch(self, request: Request, call_next):
        required_headers = settings.parsed_required_headers
        if not required_headers:
            return await call_next(request)

        # 1. Exempt CORS preflight (OPTIONS)
        if request.method == "OPTIONS":
            return await call_next(request)

        # 2. Exempt container health check endpoints
        path = request.url.path
        if path in ("/health", "/api/health"):
            return await call_next(request)

        # 3. Exempt localhost / loopback calls if configured
        if settings.REQUIRED_HEADERS_EXEMPT_LOCALHOST:
            client_host = request.client.host if request.client else ""
            if client_host in ("127.0.0.1", "::1", "localhost", "testclient"):
                return await call_next(request)

        # 4. Enforce presence and expected values
        client_ip = request.client.host if request.client else "unknown"
        for req_header, expected_val in required_headers.items():
            actual_val = request.headers.get(req_header)
            if actual_val is None:
                logger.warning(
                    f"[Security] Blocked direct request from {client_ip} to {path}: missing required header '{req_header}'"
                )
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Access Denied: Direct origin connection prohibited"},
                )
            if expected_val is not None:
                if not secrets.compare_digest(actual_val, expected_val):
                    logger.warning(
                        f"[Security] Blocked direct request from {client_ip} to {path}: invalid value for header '{req_header}'"
                    )
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Access Denied: Direct origin connection prohibited"},
                    )

        return await call_next(request)


# Inner middleware: Auth access control
app.add_middleware(AuthAndSetupMiddleware)

# Outer middleware: SessionMiddleware executes before AuthAndSetupMiddleware
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="immotion_session",
    max_age=86400 * 30,  # 30 days
    same_site="lax",
    https_only=False,
)

# Outermost middleware: Cloudflare Tunnel Header enforcement executes FIRST
app.add_middleware(HeaderEnforcementMiddleware)


# Include authentication, profile and administration routers
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(admin.router)

# Include core functional routers
app.include_router(dashboard.router)
app.include_router(properties.router)
app.include_router(maintenance.router)
app.include_router(renovations.router)
app.include_router(inventory.router)
app.include_router(documents.router)
app.include_router(energy.router)
app.include_router(cil.router)
app.include_router(bridge.router)
app.include_router(taxes.router)
app.include_router(notifications.router)

# Static assets and media files mount
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

if settings.UPLOAD_DIR.exists():
    app.mount("/media", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="media")


@app.get("/health", tags=["Health"])
async def health_check():
    """Liveness probe for Docker and orchestrator monitoring."""
    return {"status": "ok", "app": settings.APP_NAME, "version": "0.1.0"}


@app.get("/api/v1/meta", tags=["Meta"])
async def metadata():
    """System metadata and acronym reference."""
    return {
        "name": "Immo-Tion",
        "acronym": {
            "en": "Tracking, Inventory, Operations & Notifications",
            "fr": "Travaux, Inventaire, Opérations & Notifications",
        },
        "organization": "https://github.com/Immo-Boussole",
    }
