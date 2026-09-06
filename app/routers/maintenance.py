"""Maintenance router for recurring upkeep, logs, and iCal calendar feed."""

import datetime
from typing import Optional
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Request, Form, Response, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.database import get_db_connection
from app.scheduler import evaluate_task_status
from app.notifier import generate_ical_feed

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent.parent / "templates"))


@router.get("", response_class=HTMLResponse)
async def maintenance_list_view(request: Request, property_id: Optional[int] = None):
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

        cur.execute(f"SELECT * FROM maintenance_tasks {prop_filter} ORDER BY next_due_date ASC", params)
        raw_tasks = [dict(r) for r in cur.fetchall()]

        tasks = []
        for t in raw_tasks:
            t["status_info"] = evaluate_task_status(t["next_due_date"])
            tasks.append(t)

        return templates.TemplateResponse(
            request=request,
            name="maintenance/list.html",
            context={
                "properties": properties,
                "active_property": active_property,
                "tasks": tasks,
            },
        )
    finally:
        conn.close()


@router.post("/tasks")
async def create_maintenance_task(
    property_id: int = Form(...),
    title: str = Form(...),
    category: str = Form("Autre"),
    recurrence_months: int = Form(12),
    next_due_date: str = Form(...),
    description: Optional[str] = Form(None),
    estimated_cost: Optional[float] = Form(None),
    preferred_contractor: Optional[str] = Form(None),
):
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO maintenance_tasks (
                    property_id, title, category, recurrence_months, next_due_date,
                    description, estimated_cost, preferred_contractor
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    property_id, title, category, recurrence_months, next_due_date,
                    description, estimated_cost, preferred_contractor
                ),
            )
        return RedirectResponse(url=f"/maintenance?property_id={property_id}", status_code=status.HTTP_303_SEE_OTHER)
    finally:
        conn.close()


@router.post("/tasks/{task_id}/log")
async def log_maintenance_intervention(
    task_id: int,
    performed_date: str = Form(...),
    performed_by: Optional[str] = Form(None),
    cost: Optional[float] = Form(None),
    notes: Optional[str] = Form(None),
    update_next_due: bool = Form(True),
):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM maintenance_tasks WHERE id = ?", (task_id,))
        task = cur.fetchone()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        prop_id = task["property_id"]
        recurrence = task["recurrence_months"] or 12

        with conn:
            # 1. Add log entry
            conn.execute(
                """
                INSERT INTO maintenance_logs (
                    task_id, property_id, performed_date, performed_by, cost, notes
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (task_id, prop_id, performed_date, performed_by, cost, notes),
            )

            # 2. Update task last_performed and next_due_date
            if update_next_due:
                perf_date_obj = datetime.date.fromisoformat(performed_date)
                new_due = perf_date_obj + relativedelta(months=recurrence)
                conn.execute(
                    """
                    UPDATE maintenance_tasks 
                    SET last_performed_date = ?, next_due_date = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (performed_date, new_due.isoformat(), task_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE maintenance_tasks 
                    SET last_performed_date = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (performed_date, task_id),
                )

        return RedirectResponse(url=f"/maintenance?property_id={prop_id}", status_code=status.HTTP_303_SEE_OTHER)
    finally:
        conn.close()


@router.post("/tasks/{task_id}/delete")
async def delete_maintenance_task(task_id: int):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT property_id FROM maintenance_tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        prop_id = row["property_id"] if row else None

        with conn:
            conn.execute("DELETE FROM maintenance_tasks WHERE id = ?", (task_id,))

        redirect_url = f"/maintenance?property_id={prop_id}" if prop_id else "/maintenance"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    finally:
        conn.close()


@router.get("/ical/{property_id}")
async def export_property_ical(property_id: int):
    """Serve a standard .ics calendar feed for Google Calendar / Apple Calendar subscription."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM properties WHERE id = ?", (property_id,))
        prop_row = cur.fetchone()
        if not prop_row:
            raise HTTPException(status_code=404, detail="Property not found")

        cur.execute("SELECT * FROM maintenance_tasks WHERE property_id = ?", (property_id,))
        tasks = [dict(r) for r in cur.fetchall()]

        ical_content = generate_ical_feed(prop_row["name"], tasks)
        return Response(
            content=ical_content,
            media_type="text/calendar",
            headers={"Content-Disposition": f"attachment; filename=immo_tion_property_{property_id}.ics"},
        )
    finally:
        conn.close()
