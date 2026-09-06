"""Main FastAPI application entrypoint for Immo-Tion."""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import init_db
from app.routers import (
    dashboard,
    properties,
    maintenance,
    renovations,
    inventory,
    documents,
    energy,
    cil,
    bridge,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for database initialization and cleanup."""
    init_db()
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Immo-Tion: Home lifecycle management companion for Immo-Boussole (T.I.O.N. = Tracking, Inventory, Operations & Notifications).",
    version="0.1.0",
    lifespan=lifespan,
)

BASE_DIR = Path(__file__).resolve().parent.parent

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Mount uploads securely for local image display
app.mount("/media", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="media")

# Include functional routers
app.include_router(dashboard.router)
app.include_router(properties.router)
app.include_router(maintenance.router)
app.include_router(renovations.router)
app.include_router(inventory.router)
app.include_router(documents.router)
app.include_router(energy.router)
app.include_router(cil.router)
app.include_router(bridge.router)


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
