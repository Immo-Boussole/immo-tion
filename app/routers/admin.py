"""Administration, system health, Bridge token and user management router."""

import os
import platform
import sys
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from app.auth import admin_required, hash_password
from app.config import settings
from app.database import (
    get_db_connection,
    get_bridge_api_token,
    regenerate_bridge_api_token,
)
from app.templates import templates

router = APIRouter(prefix="/admin", tags=["Administration"], dependencies=[Depends(admin_required)])


@router.get("/settings", response_class=HTMLResponse)
async def admin_settings_page(request: Request):
    """Render administration and settings dashboard."""
    bridge_token = get_bridge_api_token()

    # System metrics
    db_path = settings.DB_PATH
    db_size_kb = round(db_path.stat().st_size / 1024, 1) if db_path.exists() else 0.0

    conn = get_db_connection()
    try:
        users = conn.execute("SELECT id, username, role, email, created_at FROM users ORDER BY id ASC").fetchall()
        properties_count = conn.execute("SELECT COUNT(*) AS cnt FROM properties").fetchone()["cnt"]
    finally:
        conn.close()

    system_info = {
        "python_version": f"{sys.version.split()[0]} ({platform.system()} {platform.release()})",
        "app_env": settings.APP_ENV,
        "app_port": settings.APP_PORT,
        "db_size": f"{db_size_kb} KB",
        "properties_count": properties_count,
        "users_count": len(users),
    }

    return templates.TemplateResponse(
        request=request,
        name="admin/settings.html",
        context={
            "bridge_token": bridge_token,
            "system_info": system_info,
            "users": users,
            "success": None,
            "error": None,
        },
    )


@router.post("/token/regenerate")
async def regenerate_token(request: Request):
    """Regenerate the Bridge API token."""
    new_token = regenerate_bridge_api_token()
    return RedirectResponse(url="/admin/settings", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/users/create")
async def create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("user"),
    email: Optional[str] = Form(None),
):
    """Create a new local user account."""
    if len(username.strip()) < 3 or len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identifiant (min 3 car.) ou mot de passe (min 6 car.) invalide.",
        )

    pwd_hash, salt = hash_password(password)
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, salt, role, email)
                VALUES (?, ?, ?, ?, ?)
                """,
                (username.strip(), pwd_hash, salt, role if role in ("admin", "user") else "user", email.strip() if email else None),
            )
    finally:
        conn.close()

    return RedirectResponse(url="/admin/settings", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/users/{user_id}/delete")
async def delete_user(request: Request, user_id: int):
    """Delete a user account, preventing an admin from deleting themselves."""
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        if user and user["username"] == request.session.get("username"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vous ne pouvez pas supprimer votre propre compte administrateur.",
            )

        with conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    finally:
        conn.close()

    return RedirectResponse(url="/admin/settings", status_code=status.HTTP_303_SEE_OTHER)
