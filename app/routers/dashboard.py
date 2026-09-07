"""Dashboard router rendering the executive overview."""

from typing import Optional
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from app.database import get_db_connection
from app.scheduler import get_dashboard_summary
from app.timeline import get_property_timeline
from app.templates import templates

router = APIRouter(tags=["Dashboard"])


@router.get("/", response_class=HTMLResponse)
async def dashboard_view(request: Request, property_id: Optional[int] = None):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM properties ORDER BY name ASC")
        properties = [dict(r) for r in cur.fetchall()]

        active_property = None
        if property_id:
            for p in properties:
                if p["id"] == property_id:
                    active_property = p
                    break
        elif properties:
            active_property = properties[0]
            property_id = active_property["id"]

        summary = get_dashboard_summary(property_id=property_id)
        timeline = get_property_timeline(property_id=property_id) if property_id else None

        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "properties": properties,
                "active_property": active_property,
                "summary": summary,
                "timeline": timeline,
            },
        )
    finally:
        conn.close()

