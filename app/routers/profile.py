"""User profile and account settings router."""

from typing import Optional
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.auth import hash_password, login_required, verify_password
from app.database import get_db_connection, get_user_by_username
from app.templates import templates

router = APIRouter(prefix="/profile", tags=["Profile"], dependencies=[Depends(login_required)])


@router.get("", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Render user profile page."""
    username = request.session.get("username")
    user = get_user_by_username(username) if username else None
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": user,
            "success": None,
            "error": None,
        },
    )


@router.post("/password")
async def update_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    """Change the current user's password."""
    username = request.session.get("username")
    user = get_user_by_username(username) if username else None
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    if not verify_password(old_password, bytes(user["salt"]), bytes(user["password_hash"])):
        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={
                "user": user,
                "success": None,
                "error": "Le mot de passe actuel est incorrect.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if len(new_password) < 6:
        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={
                "user": user,
                "success": None,
                "error": "Le nouveau mot de passe doit contenir au moins 6 caractères.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if new_password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={
                "user": user,
                "success": None,
                "error": "Les deux nouveaux mots de passe ne correspondent pas.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Hash and save
    pwd_hash, salt = hash_password(new_password)
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
                (pwd_hash, salt, user["id"]),
            )
    finally:
        conn.close()

    updated_user = get_user_by_username(username)
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": updated_user,
            "success": "Votre mot de passe a été mis à jour avec succès.",
            "error": None,
        },
    )


@router.post("/details")
async def update_details(
    request: Request,
    email: Optional[str] = Form(None),
):
    """Update profile email."""
    username = request.session.get("username")
    user = get_user_by_username(username) if username else None
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE users SET email = ? WHERE id = ?",
                (email.strip() if email else None, user["id"]),
            )
    finally:
        conn.close()

    updated_user = get_user_by_username(username)
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": updated_user,
            "success": "Informations mises à jour avec succès.",
            "error": None,
        },
    )
