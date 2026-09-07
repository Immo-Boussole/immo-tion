"""Taxes and fiscal management router for Immo-Tion."""

import datetime
import os
import shutil
from pathlib import Path
from typing import Optional
from urllib.parse import quote
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from starlette import status as http_status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.auth import login_required
from app.config import settings
from app.database import get_db_connection
from app.templates import templates

router = APIRouter(prefix="/taxes", tags=["Taxes"], dependencies=[Depends(login_required)])


@router.get("", response_class=HTMLResponse)
async def taxes_dashboard(request: Request, property_id: Optional[int] = None):
    """Render property taxes, annual analytics, and tax notices archive."""
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

        taxes_list = []
        chart_data = []
        latest_year_total = 0.0
        latest_year_teom = 0.0
        latest_year = datetime.date.today().year
        yoy_diff = 0.0
        yoy_pct = None
        next_due_tax = None
        today = datetime.date.today()

        if active_property:
            cur.execute(
                """
                SELECT * FROM taxes
                WHERE property_id = ?
                ORDER BY tax_year DESC, due_date DESC
                """,
                (property_id,),
            )
            taxes_list = [dict(r) for r in cur.fetchall()]

            # Aggregate by year for pluriannual evolution chart
            by_year = {}
            for t in taxes_list:
                yr = t["tax_year"]
                if yr not in by_year:
                    by_year[yr] = {"year": yr, "total": 0.0, "teom": 0.0, "count": 0}
                by_year[yr]["total"] += t["amount"]
                by_year[yr]["teom"] += t["teom_amount"] or 0.0
                by_year[yr]["count"] += 1

                # Find next upcoming unpaid tax
                if not next_due_tax and t["status"] in ("À payer", "Mensualisé"):
                    try:
                        d_due = datetime.date.fromisoformat(t["due_date"][:10])
                        if d_due >= today or t["status"] == "À payer":
                            next_due_tax = t
                    except (ValueError, TypeError):
                        pass

            # Sort ascending for chart
            sorted_years = sorted(by_year.keys())
            chart_data = [by_year[y] for y in sorted_years]

            # Calculate Max for relative chart heights
            max_amount = max([c["total"] for c in chart_data], default=100.0)
            for c in chart_data:
                c["pct_height"] = max(12, min(100, round((c["total"] / max_amount) * 100)))

            # YoY calculation (compare latest year with previous recorded year)
            if len(sorted_years) >= 1:
                latest_year = sorted_years[-1]
                latest_year_total = by_year[latest_year]["total"]
                latest_year_teom = by_year[latest_year]["teom"]

                if len(sorted_years) >= 2:
                    prev_year = sorted_years[-2]
                    prev_total = by_year[prev_year]["total"]
                    yoy_diff = latest_year_total - prev_total
                    if prev_total > 0:
                        yoy_pct = round((yoy_diff / prev_total) * 100, 1)

        success = request.query_params.get("success")
        error = request.query_params.get("error")

        return templates.TemplateResponse(
            request=request,
            name="taxes/list.html",
            context={
                "properties": properties,
                "active_property": active_property,
                "taxes": taxes_list,
                "chart_data": chart_data,
                "latest_year": latest_year,
                "latest_year_total": latest_year_total,
                "latest_year_teom": latest_year_teom,
                "yoy_diff": yoy_diff,
                "yoy_pct": yoy_pct,
                "next_due_tax": next_due_tax,
                "current_year": today.year,
                "success": success,
                "error": error,
            },
        )
    finally:
        conn.close()


@router.post("")
async def create_tax_record(
    request: Request,
    property_id: int = Form(...),
    tax_year: int = Form(...),
    tax_type: str = Form("Taxe Foncière"),
    amount: float = Form(...),
    teom_amount: Optional[float] = Form(0.0),
    due_date: str = Form(...),
    status: str = Form("Payé"),
    reference_number: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    document: Optional[UploadFile] = File(None),
):
    """Save a new tax notice record with optional PDF notice upload."""
    if amount < 0:
        return RedirectResponse(
            url=f"/taxes?property_id={property_id}&error=" + quote("Le montant de la taxe doit être positif."),
            status_code=http_status.HTTP_303_SEE_OTHER,
        )

    doc_rel_path = None
    if document and document.filename and document.filename.strip():
        taxes_upload_dir = settings.UPLOAD_DIR / "taxes"
        taxes_upload_dir.mkdir(parents=True, exist_ok=True)

        clean_filename = f"tax_{property_id}_{tax_year}_{os.path.basename(document.filename)}"
        target_path = taxes_upload_dir / clean_filename

        with open(target_path, "wb") as f:
            shutil.copyfileobj(document.file, f)

        doc_rel_path = f"/media/taxes/{clean_filename}"

    conn = get_db_connection()
    try:
        with conn:
            # 1. Insert tax notice
            cur = conn.execute(
                """
                INSERT INTO taxes (
                    property_id, tax_year, tax_type, amount, teom_amount,
                    due_date, status, document_path, reference_number, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    property_id,
                    tax_year,
                    tax_type.strip(),
                    amount,
                    teom_amount or 0.0,
                    due_date.strip(),
                    status.strip(),
                    doc_rel_path,
                    reference_number.strip() if reference_number else None,
                    notes.strip() if notes else None,
                ),
            )

            # 2. Automatically register in documents vault if a file was uploaded
            if doc_rel_path:
                conn.execute(
                    """
                    INSERT INTO documents (property_id, title, category, file_path, notes)
                    VALUES (?, ?, 'Fiscalité', ?, ?)
                    """,
                    (
                        property_id,
                        f"Avis {tax_type.strip()} {tax_year}",
                        doc_rel_path,
                        f"Avis d'imposition {tax_year} (Montant: {amount:,.0f} €)",
                    ),
                )
    finally:
        conn.close()

    return RedirectResponse(
        url=f"/taxes?property_id={property_id}&success=" + quote(f"Avis de {tax_type} {tax_year} enregistré avec succès."),
        status_code=http_status.HTTP_303_SEE_OTHER,
    )


@router.post("/{tax_id}/delete")
async def delete_tax_record(request: Request, tax_id: int, property_id: int = Form(...)):
    """Delete a tax record and its associated document."""
    conn = get_db_connection()
    try:
        tax = conn.execute("SELECT * FROM taxes WHERE id = ?", (tax_id,)).fetchone()
        if not tax:
            return RedirectResponse(
                url=f"/taxes?property_id={property_id}&error=" + quote("Avis de taxe introuvable."),
                status_code=http_status.HTTP_303_SEE_OTHER,
            )

        with conn:
            conn.execute("DELETE FROM taxes WHERE id = ?", (tax_id,))
    finally:
        conn.close()

    return RedirectResponse(
        url=f"/taxes?property_id={property_id}&success=" + quote("Avis de taxe supprimé avec succès."),
        status_code=http_status.HTTP_303_SEE_OTHER,
    )
