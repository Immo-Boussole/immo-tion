"""Notifications management router for Immo-Tion."""

from typing import Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.auth import login_required, get_current_user
from app.config import settings
from app.database import (
    get_db_connection,
    get_notifications,
    get_unread_notifications_count,
    mark_notification_read,
    mark_notification_unread,
    mark_all_notifications_read,
    delete_notification,
)
from app.notifier import send_test_notification
from app.scheduler import run_deadline_evaluations_and_notify
from app.templates import templates

router = APIRouter(tags=["Notifications"])


@router.get("/notifications", response_class=HTMLResponse, dependencies=[Depends(login_required)])
async def list_notifications(
    request: Request,
    category: Optional[str] = "all",
    unread_only: bool = False,
    page: int = 1,
):
    """Render the in-app notification center with category and status filtering."""
    user = get_current_user(request)
    user_id = user["id"] if user else None
    role = user["role"] if user else "user"

    limit = 30
    offset = (page - 1) * limit

    notifications = get_notifications(
        user_id=user_id,
        role=role,
        category=category,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )
    unread_count = get_unread_notifications_count(user_id=user_id, role=role)

    # Load properties for topbar picker
    conn = get_db_connection()
    try:
        properties = [dict(r) for r in conn.execute("SELECT * FROM properties ORDER BY name ASC").fetchall()]
    finally:
        conn.close()

    active_prop_id = request.session.get("active_property_id")
    active_property = None
    if active_prop_id:
        for p in properties:
            if p["id"] == active_prop_id:
                active_property = p
                break
    elif properties:
        active_property = properties[0]

    return templates.TemplateResponse(
        request=request,
        name="notifications/list.html",
        context={
            "notifications": notifications,
            "unread_count": unread_count,
            "selected_category": category or "all",
            "unread_only": unread_only,
            "page": page,
            "properties": properties,
            "active_property": active_property,
        },
    )


# ── API Endpoints ─────────────────────────────────────────────────────────────

@router.post("/api/v1/notifications/{notification_id}/read", dependencies=[Depends(login_required)])
async def api_mark_read(request: Request, notification_id: int):
    """Mark a notification as read."""
    user = get_current_user(request)
    user_id = user["id"] if user else None
    role = user["role"] if user else "user"

    ok = mark_notification_read(notification_id, user_id=user_id, role=role)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")
    unread_count = get_unread_notifications_count(user_id=user_id, role=role)
    return {"success": True, "unread_count": unread_count}


@router.post("/api/v1/notifications/{notification_id}/unread", dependencies=[Depends(login_required)])
async def api_mark_unread(request: Request, notification_id: int):
    """Mark a notification as unread."""
    user = get_current_user(request)
    user_id = user["id"] if user else None
    role = user["role"] if user else "user"

    ok = mark_notification_unread(notification_id, user_id=user_id, role=role)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")
    unread_count = get_unread_notifications_count(user_id=user_id, role=role)
    return {"success": True, "unread_count": unread_count}


@router.post("/api/v1/notifications/read-all", dependencies=[Depends(login_required)])
async def api_mark_all_read(
    request: Request,
    category: Optional[str] = Form(None),
):
    """Mark all notifications matching category as read."""
    user = get_current_user(request)
    user_id = user["id"] if user else None
    role = user["role"] if user else "user"

    updated = mark_all_notifications_read(user_id=user_id, role=role, category=category)
    return {"success": True, "updated": updated, "unread_count": 0}


@router.post("/api/v1/notifications/{notification_id}/delete", dependencies=[Depends(login_required)])
async def api_delete_notification(request: Request, notification_id: int):
    """Delete a notification."""
    user = get_current_user(request)
    user_id = user["id"] if user else None
    role = user["role"] if user else "user"

    ok = delete_notification(notification_id, user_id=user_id, role=role)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")
    unread_count = get_unread_notifications_count(user_id=user_id, role=role)
    return {"success": True, "unread_count": unread_count}


@router.get("/api/v1/notifications/unread-count", dependencies=[Depends(login_required)])
async def api_get_unread_count(request: Request):
    """Return count of unread notifications for badge polling/refresh."""
    user = get_current_user(request)
    user_id = user["id"] if user else None
    role = user["role"] if user else "user"
    return {"unread_count": get_unread_notifications_count(user_id=user_id, role=role)}


@router.post("/api/v1/notifications/test", dependencies=[Depends(login_required)])
async def api_test_notification(
    request: Request,
    apprise_url: str = Form(...),
):
    """Send a live test notification via Apprise."""
    if not apprise_url or not apprise_url.strip():
        raise HTTPException(status_code=400, detail="Apprise URL is required")

    success = await send_test_notification(apprise_url.strip())
    if not success:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Échec de l'envoi de test. Vérifiez le format de l'URL Apprise."},
        )
    return {"success": True, "message": "Notification de test envoyée avec succès !"}


@router.post("/api/v1/notifications/trigger-check", dependencies=[Depends(login_required)])
async def api_trigger_notifications_check(request: Request):
    """Admin-only endpoint to immediately evaluate deadlines and dispatch alerts."""
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")

    results = await run_deadline_evaluations_and_notify()
    return {"success": True, "results": results}
