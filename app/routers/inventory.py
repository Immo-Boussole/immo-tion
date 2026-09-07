"""Inventory router for equipment, appliances, and warranty tracking."""

from typing import Optional
from fastapi import APIRouter, Request, Form, UploadFile, File, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from app.database import get_db_connection
from app.scheduler import evaluate_task_status
from app.templates import templates

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("", response_class=HTMLResponse)
async def inventory_list_view(request: Request, property_id: Optional[int] = None):
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

        cur.execute(f"SELECT * FROM inventory {prop_filter} ORDER BY name ASC", params)
        raw_items = [dict(r) for r in cur.fetchall()]

        items = []
        for it in raw_items:
            exp = it.get("warranty_expiry_date")
            if exp:
                it["warranty_status"] = evaluate_task_status(exp)
            else:
                it["warranty_status"] = None
            items.append(it)

        return templates.TemplateResponse(
            request=request,
            name="inventory/list.html",
            context={
                "properties": properties,
                "active_property": active_property,
                "items": items,
            },
        )
    finally:
        conn.close()


@router.post("")
async def create_inventory_item(
    property_id: int = Form(...),
    name: str = Form(...),
    brand: Optional[str] = Form(None),
    model_number: Optional[str] = Form(None),
    serial_number: Optional[str] = Form(None),
    category: str = Form("Autre"),
    purchase_date: Optional[str] = Form(None),
    purchase_price: Optional[float] = Form(None),
    warranty_expiry_date: Optional[str] = Form(None),
    vendor: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
):
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO inventory (
                    property_id, name, brand, model_number, serial_number, category,
                    purchase_date, purchase_price, warranty_expiry_date, vendor, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    property_id, name, brand, model_number, serial_number, category,
                    purchase_date, purchase_price, warranty_expiry_date, vendor, notes
                ),
            )
        return RedirectResponse(url=f"/inventory?property_id={property_id}", status_code=status.HTTP_303_SEE_OTHER)
    finally:
        conn.close()


@router.post("/{item_id}/delete")
async def delete_inventory_item(item_id: int):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT property_id FROM inventory WHERE id = ?", (item_id,))
        row = cur.fetchone()
        prop_id = row["property_id"] if row else None

        with conn:
            conn.execute("DELETE FROM inventory WHERE id = ?", (item_id,))

        redirect_url = f"/inventory?property_id={prop_id}" if prop_id else "/inventory"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    finally:
        conn.close()
