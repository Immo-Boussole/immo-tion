"""Properties router for managing tracked homes."""

import sqlite3
from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.database import get_db_connection, seed_standard_maintenance_tasks

router = APIRouter(prefix="/properties", tags=["Properties"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent.parent / "templates"))


@router.get("", response_class=HTMLResponse)
async def list_properties_view(request: Request):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.*, 
                (SELECT COUNT(*) FROM maintenance_tasks WHERE property_id = p.id) as tasks_count,
                (SELECT COUNT(*) FROM renovations WHERE property_id = p.id) as renovations_count,
                (SELECT COUNT(*) FROM inventory WHERE property_id = p.id) as inventory_count
            FROM properties p ORDER BY p.name ASC
        """)
        properties = [dict(r) for r in cur.fetchall()]
        return templates.TemplateResponse(request=request, name="properties/list.html", context={"properties": properties})
    finally:
        conn.close()


@router.get("/new", response_class=HTMLResponse)
async def new_property_view(request: Request):
    return templates.TemplateResponse(request=request, name="properties/form.html", context={"property": None})


@router.post("", response_class=HTMLResponse)
async def create_property(
    request: Request,
    name: str = Form(...),
    address: str = Form(...),
    postal_code: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    surface_m2: Optional[float] = Form(None),
    land_surface_m2: Optional[float] = Form(None),
    cadastral_reference: Optional[str] = Form(None),
    dpe_rating: Optional[str] = Form(None),
    ges_rating: Optional[str] = Form(None),
    acquisition_date: Optional[str] = Form(None),
    acquisition_price: Optional[float] = Form(None),
    notes: Optional[str] = Form(None),
    seed_tasks: bool = Form(True),
):
    conn = get_db_connection()
    try:
        with conn:
            cur = conn.execute(
                """
                INSERT INTO properties (
                    name, address, postal_code, city, surface_m2, land_surface_m2,
                    cadastral_reference, dpe_rating, ges_rating, acquisition_date,
                    acquisition_price, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name, address, postal_code, city, surface_m2, land_surface_m2,
                    cadastral_reference, dpe_rating, ges_rating, acquisition_date,
                    acquisition_price, notes
                ),
            )
            prop_id = cur.lastrowid
        if seed_tasks and prop_id:
            seed_standard_maintenance_tasks(prop_id)
        return RedirectResponse(url=f"/properties/{prop_id}", status_code=status.HTTP_303_SEE_OTHER)
    finally:
        conn.close()


@router.get("/{prop_id}", response_class=HTMLResponse)
async def property_detail_view(request: Request, prop_id: int):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM properties WHERE id = ?", (prop_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Property not found")
        prop = dict(row)

        cur.execute("SELECT * FROM maintenance_tasks WHERE property_id = ? ORDER BY next_due_date ASC", (prop_id,))
        tasks = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT * FROM renovations WHERE property_id = ? ORDER BY created_at DESC", (prop_id,))
        renovations = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT * FROM inventory WHERE property_id = ? ORDER BY name ASC", (prop_id,))
        inventory = [dict(r) for r in cur.fetchall()]

        return templates.TemplateResponse(
            request=request,
            name="properties/detail.html",
            context={
                "property": prop,
                "tasks": tasks,
                "renovations": renovations,
                "inventory": inventory,
            },
        )
    finally:
        conn.close()


@router.post("/{prop_id}/delete")
async def delete_property(prop_id: int):
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("DELETE FROM properties WHERE id = ?", (prop_id,))
        return RedirectResponse(url="/properties", status_code=status.HTTP_303_SEE_OTHER)
    finally:
        conn.close()
