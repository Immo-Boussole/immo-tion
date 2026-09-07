"""Documents router for digital file vault and records management."""

from typing import Optional
from fastapi import APIRouter, Request, Form, UploadFile, File, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
import shutil
import uuid
from app.database import get_db_connection
from app.config import settings
from app.templates import templates

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("", response_class=HTMLResponse)
async def documents_list_view(request: Request, property_id: Optional[int] = None, category: Optional[str] = None):
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

        query = "SELECT * FROM documents WHERE 1=1"
        params = []
        if property_id:
            query += " AND property_id = ?"
            params.append(property_id)
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY upload_date DESC"

        cur.execute(query, params)
        documents = [dict(r) for r in cur.fetchall()]

        return templates.TemplateResponse(
            request=request,
            name="documents/list.html",
            context={
                "properties": properties,
                "active_property": active_property,
                "documents": documents,
                "selected_category": category,
            },
        )
    finally:
        conn.close()


@router.post("/upload")
async def upload_document(
    property_id: int = Form(...),
    title: str = Form(...),
    category: str = Form("Autre"),
    notes: Optional[str] = Form(None),
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    # Generate unique filename
    ext = Path(file.filename).suffix
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    target_path = settings.UPLOAD_DIR / safe_filename

    with target_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = target_path.stat().st_size

    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO documents (property_id, title, category, file_path, file_size, mime_type, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (property_id, title, category, safe_filename, file_size, file.content_type, notes),
            )
        return RedirectResponse(url=f"/documents?property_id={property_id}", status_code=status.HTTP_303_SEE_OTHER)
    finally:
        conn.close()


@router.get("/{doc_id}/download")
async def download_document(doc_id: int):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        file_path = settings.UPLOAD_DIR / doc["file_path"]
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Stored file missing on disk")

        return FileResponse(
            path=str(file_path),
            filename=f"{doc['title']}{file_path.suffix}",
            media_type=doc["mime_type"] or "application/octet-stream",
        )
    finally:
        conn.close()


@router.post("/{doc_id}/delete")
async def delete_document(doc_id: int):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT property_id, file_path FROM documents WHERE id = ?", (doc_id,))
        doc = cur.fetchone()
        prop_id = doc["property_id"] if doc else None

        if doc and doc["file_path"]:
            disk_file = settings.UPLOAD_DIR / doc["file_path"]
            if disk_file.exists():
                try:
                    disk_file.unlink()
                except OSError:
                    pass

        with conn:
            conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

        redirect_url = f"/documents?property_id={prop_id}" if prop_id else "/documents"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    finally:
        conn.close()
