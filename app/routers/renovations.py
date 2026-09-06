"""Renovations router for tracking works, contractors, quotes, and expenses."""

from typing import Optional
from fastapi import APIRouter, Request, Form, UploadFile, File, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import shutil
import uuid
from app.database import get_db_connection
from app.config import settings

router = APIRouter(prefix="/renovations", tags=["Renovations"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent.parent / "templates"))


@router.get("", response_class=HTMLResponse)
async def renovations_list_view(request: Request, property_id: Optional[int] = None):
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

        prop_filter = "WHERE r.property_id = ?" if property_id else ""
        params = [property_id] if property_id else []

        cur.execute(f"""
            SELECT r.*,
                (SELECT COALESCE(SUM(amount), 0) FROM renovation_expenses WHERE renovation_id = r.id) as computed_cost,
                (SELECT COUNT(*) FROM renovation_photos WHERE renovation_id = r.id) as photos_count
            FROM renovations r
            {prop_filter}
            ORDER BY r.created_at DESC
        """, params)
        renovations = [dict(r) for r in cur.fetchall()]

        return templates.TemplateResponse(
            request=request,
            name="renovations/list.html",
            context={
                "properties": properties,
                "active_property": active_property,
                "renovations": renovations,
            },
        )
    finally:
        conn.close()


@router.post("")
async def create_renovation_project(
    property_id: int = Form(...),
    title: str = Form(...),
    category: str = Form("Général"),
    status_str: str = Form("Planifié"),
    estimated_budget: Optional[float] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    contractor_name: Optional[str] = Form(None),
    contractor_siret: Optional[str] = Form(None),
    contractor_phone: Optional[str] = Form(None),
    contractor_email: Optional[str] = Form(None),
    warranty_decennale_expiry: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
):
    conn = get_db_connection()
    try:
        with conn:
            cur = conn.execute(
                """
                INSERT INTO renovations (
                    property_id, title, category, status, estimated_budget,
                    start_date, end_date, contractor_name, contractor_siret,
                    contractor_phone, contractor_email, warranty_decennale_expiry, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    property_id, title, category, status_str, estimated_budget,
                    start_date, end_date, contractor_name, contractor_siret,
                    contractor_phone, contractor_email, warranty_decennale_expiry, notes
                ),
            )
            renov_id = cur.lastrowid
        return RedirectResponse(url=f"/renovations/{renov_id}", status_code=status.HTTP_303_SEE_OTHER)
    finally:
        conn.close()


@router.get("/{renov_id}", response_class=HTMLResponse)
async def renovation_detail_view(request: Request, renov_id: int):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT r.*, p.name as property_name FROM renovations r JOIN properties p ON r.property_id = p.id WHERE r.id = ?", (renov_id,))
        renov = cur.fetchone()
        if not renov:
            raise HTTPException(status_code=404, detail="Renovation project not found")
        renovation = dict(renov)

        cur.execute("SELECT * FROM renovation_expenses WHERE renovation_id = ? ORDER BY date DESC", (renov_id,))
        expenses = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT * FROM renovation_photos WHERE renovation_id = ? ORDER BY created_at DESC", (renov_id,))
        photos = [dict(r) for r in cur.fetchall()]

        total_paid = sum(e["amount"] for e in expenses if e["is_paid"])

        return templates.TemplateResponse(
            request=request,
            name="renovations/detail.html",
            context={
                "renovation": renovation,
                "expenses": expenses,
                "photos": photos,
                "total_paid": total_paid,
            },
        )
    finally:
        conn.close()


@router.post("/{renov_id}/expenses")
async def add_renovation_expense(
    renov_id: int,
    description: str = Form(...),
    expense_type: str = Form("Facture"),
    amount: float = Form(...),
    date: str = Form(...),
    is_paid: bool = Form(True),
):
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO renovation_expenses (renovation_id, description, expense_type, amount, date, is_paid)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (renov_id, description, expense_type, amount, date, 1 if is_paid else 0),
            )
            # Update actual_cost in renovations
            conn.execute(
                """
                UPDATE renovations 
                SET actual_cost = (SELECT COALESCE(SUM(amount), 0) FROM renovation_expenses WHERE renovation_id = ? AND is_paid = 1),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (renov_id, renov_id),
            )
        return RedirectResponse(url=f"/renovations/{renov_id}", status_code=status.HTTP_303_SEE_OTHER)
    finally:
        conn.close()


@router.post("/{renov_id}/delete")
async def delete_renovation(renov_id: int):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT property_id FROM renovations WHERE id = ?", (renov_id,))
        row = cur.fetchone()
        prop_id = row["property_id"] if row else None

        with conn:
            conn.execute("DELETE FROM renovations WHERE id = ?", (renov_id,))

        redirect_url = f"/renovations?property_id={prop_id}" if prop_id else "/renovations"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    finally:
        conn.close()
