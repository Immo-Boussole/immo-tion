"""Administration, system health, Bridge token and user management router."""

import os
import platform
import sqlite3
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import quote
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
    success = request.query_params.get("success")
    error = request.query_params.get("error")

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
            "success": success,
            "error": error,
        },
    )


@router.post("/token/regenerate")
async def regenerate_token(request: Request):
    """Regenerate the Bridge API token."""
    new_token = regenerate_bridge_api_token()
    return RedirectResponse(
        url="/admin/settings?success=" + quote("Le jeton Bridge a été régénéré avec succès."),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/users/create")
async def get_create_user():
    """Redirect accidental direct GET requests on user creation back to settings."""
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
    clean_username = username.strip()
    clean_role = role.strip().lower() if role else "user"
    if clean_role not in ("admin", "user"):
        clean_role = "user"
    clean_email = email.strip() if email and email.strip() else None

    if len(clean_username) < 3:
        return RedirectResponse(
            url="/admin/settings?error=" + quote("L'identifiant doit contenir au moins 3 caractères."),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if len(password) < 6:
        return RedirectResponse(
            url="/admin/settings?error=" + quote("Le mot de passe doit contenir au moins 6 caractères."),
            status_code=status.HTTP_303_SEE_OTHER,
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
                (clean_username, pwd_hash, salt, clean_role, clean_email),
            )
    except sqlite3.IntegrityError:
        return RedirectResponse(
            url="/admin/settings?error=" + quote(f"L'identifiant '{clean_username}' existe déjà."),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    finally:
        conn.close()

    return RedirectResponse(
        url="/admin/settings?success=" + quote(f"L'utilisateur '{clean_username}' a été créé avec succès."),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/users/{user_id}/delete")
async def delete_user(request: Request, user_id: int):
    """Delete a user account, preventing an admin from deleting themselves."""
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return RedirectResponse(
                url="/admin/settings?error=" + quote("Utilisateur introuvable."),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        current_username = request.session.get("username")
        if user["username"] == current_username:
            return RedirectResponse(
                url="/admin/settings?error=" + quote("Vous ne pouvez pas supprimer votre propre compte administrateur."),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        with conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    finally:
        conn.close()

    return RedirectResponse(
        url="/admin/settings?success=" + quote(f"L'utilisateur '{user['username']}' a été supprimé avec succès."),
        status_code=status.HTTP_303_SEE_OTHER,
    )

