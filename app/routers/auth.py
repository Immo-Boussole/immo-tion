"""Authentication and initial setup wizard router."""

from typing import Optional
from urllib.parse import quote
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from app.templates import templates
from app.auth import hash_password, verify_password, is_authenticated
from app.database import (
    get_db_connection,
    get_user_count,
    get_user_by_username,
    get_bridge_api_token,
    seed_standard_maintenance_tasks,
)

router = APIRouter(tags=["Authentication & Setup"])


@router.get("/setup", response_class=HTMLResponse)
async def setup_wizard(request: Request, step: int = 1):
    """First launch setup wizard."""
    user_count = get_user_count()
    if user_count > 0 and (step == 1 or not is_authenticated(request)):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    bridge_token = get_bridge_api_token()
    return templates.TemplateResponse(
        request=request,
        name="setup.html",
        context={
            "step": step,
            "bridge_token": bridge_token,
            "error": None,
        },
    )


@router.post("/setup/step1")
async def setup_step1(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    email: Optional[str] = Form(None),
    default_language: str = Form("fr"),
):
    """Process step 1 of setup: create local admin account and set default language."""
    user_count = get_user_count()
    if user_count > 0:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    if len(username.strip()) < 3:
        return templates.TemplateResponse(
            request=request,
            name="setup.html",
            context={
                "step": 1,
                "error": "L'identifiant doit contenir au moins 3 caractères.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if len(password) < 6:
        return templates.TemplateResponse(
            request=request,
            name="setup.html",
            context={
                "step": 1,
                "error": "Le mot de passe doit contenir au moins 6 caractères.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="setup.html",
            context={
                "step": 1,
                "error": "Les deux mots de passe ne correspondent pas.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Hash password & persist admin user
    pwd_hash, salt = hash_password(password)
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, salt, role, email)
                VALUES (?, ?, ?, 'admin', ?)
                """,
                (username.strip(), pwd_hash, salt, email.strip() if email else None),
            )
    finally:
        conn.close()

    # Log user in
    request.session["authenticated"] = True
    request.session["username"] = username.strip()
    request.session["role"] = "admin"
    request.session["lang"] = default_language if default_language in ("fr", "en") else "fr"

    return RedirectResponse(url="/setup?step=2", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/setup/step2")
async def setup_step2(
    request: Request,
    property_name: Optional[str] = Form(None),
    property_city: Optional[str] = Form(None),
    property_address: Optional[str] = Form(None),
):
    """Process step 2 of setup: optional initial property creation."""
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    if property_name and property_name.strip():
        conn = get_db_connection()
        property_id = None
        try:
            with conn:
                cur = conn.execute(
                    """
                    INSERT INTO properties (name, city, address)
                    VALUES (?, ?, ?)
                    """,
                    (
                        property_name.strip(),
                        property_city.strip() if property_city else None,
                        property_address.strip() if property_address else (property_city.strip() if property_city else "Non renseignée"),
                    ),
                )
                property_id = cur.lastrowid
        finally:
            conn.close()

        if property_id:
            seed_standard_maintenance_tasks(property_id)
            request.session["active_property_id"] = property_id

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: Optional[str] = None):
    """Render login page."""
    if get_user_count() == 0:
        return RedirectResponse(url="/setup", status_code=status.HTTP_303_SEE_OTHER)

    if is_authenticated(request):
        target = next if next and next.startswith("/") else "/"
        return RedirectResponse(url=target, status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "next": next or "/",
            "error": None,
        },
    )


@router.post("/login")
async def process_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: Optional[str] = Form(None),
):
    """Validate user credentials and create session."""
    user = get_user_by_username(username.strip())
    if not user:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "next": next or "/",
                "error": "Identifiant ou mot de passe incorrect.",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not verify_password(password, bytes(user["salt"]), bytes(user["password_hash"])):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "next": next or "/",
                "error": "Identifiant ou mot de passe incorrect.",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Establish session
    request.session["authenticated"] = True
    request.session["username"] = user["username"]
    request.session["role"] = user["role"]

    target = next if next and next.startswith("/") and not next.startswith("//") else "/"
    return RedirectResponse(url=target, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/logout")
async def logout(request: Request):
    """Clear session data and redirect to login."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/lang/{lang_code}")
async def switch_language(request: Request, lang_code: str):
    """Switch active interface language."""
    if lang_code in ("fr", "en"):
        request.session["lang"] = lang_code

    referer = request.headers.get("referer", "/")
    return RedirectResponse(url=referer, status_code=status.HTTP_303_SEE_OTHER)
