"""Energy router for tracking electricity, water, gas, and wood consumption."""

from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from app.database import get_db_connection
from app.templates import templates

router = APIRouter(prefix="/energy", tags=["Energy"])


@router.get("", response_class=HTMLResponse)
async def energy_list_view(request: Request, property_id: Optional[int] = None):
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

        prop_filter = "WHERE property_id = ?" if property_id else ""
        params = [property_id] if property_id else []

        cur.execute(f"SELECT * FROM energy_readings {prop_filter} ORDER BY reading_date DESC", params)
        readings = [dict(r) for r in cur.fetchall()]

        # Totals by type
        totals = {}
        for r in readings:
            etype = r["energy_type"]
            totals[etype] = totals.get(etype, 0.0) + (r["reading_value"] or 0.0)

        return templates.TemplateResponse(
            request=request,
            name="energy/list.html",
            context={
                "properties": properties,
                "active_property": active_property,
                "readings": readings,
                "totals": totals,
            },
        )
    finally:
        conn.close()


@router.post("/readings")
async def add_energy_reading(
    property_id: int = Form(...),
    energy_type: str = Form("Électricité"),
    reading_date: str = Form(...),
    reading_value: float = Form(...),
    unit: str = Form("kWh"),
    cost: Optional[float] = Form(None),
    notes: Optional[str] = Form(None),
):
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO energy_readings (property_id, energy_type, reading_date, reading_value, unit, cost, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (property_id, energy_type, reading_date, reading_value, unit, cost, notes),
            )
        return RedirectResponse(url=f"/energy?property_id={property_id}", status_code=status.HTTP_303_SEE_OTHER)
    finally:
        conn.close()


@router.post("/readings/{reading_id}/delete")
async def delete_energy_reading(reading_id: int):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT property_id FROM energy_readings WHERE id = ?", (reading_id,))
        row = cur.fetchone()
        prop_id = row["property_id"] if row else None

        with conn:
            conn.execute("DELETE FROM energy_readings WHERE id = ?", (reading_id,))

        redirect_url = f"/energy?property_id={prop_id}" if prop_id else "/energy"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    finally:
        conn.close()
