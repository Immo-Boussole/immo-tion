"""CIL (Carnet d'Information du Logement) export router."""

import json
import io
import zipfile
import datetime
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, Response
from app.database import get_db_connection
from app.config import settings
from app.templates import templates

router = APIRouter(prefix="/cil", tags=["CIL"])


@router.get("", response_class=HTMLResponse)
async def cil_preview_view(request: Request, property_id: Optional[int] = None):
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

        summary = {}
        if active_property:
            cur.execute("SELECT COUNT(*) FROM renovations WHERE property_id = ?", (property_id,))
            summary["renovations_count"] = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM maintenance_logs WHERE property_id = ?", (property_id,))
            summary["maintenance_logs_count"] = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM inventory WHERE property_id = ?", (property_id,))
            summary["inventory_count"] = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM documents WHERE property_id = ?", (property_id,))
            summary["documents_count"] = cur.fetchone()[0]

        return templates.TemplateResponse(
            request=request,
            name="cil/overview.html",
            context={
                "properties": properties,
                "active_property": active_property,
                "summary": summary,
            },
        )
    finally:
        conn.close()


@router.get("/{property_id}/export")
async def export_cil_archive(property_id: int):
    """Generate a complete certified CIL dossier as a structured ZIP archive."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM properties WHERE id = ?", (property_id,))
        prop = cur.fetchone()
        if not prop:
            raise HTTPException(status_code=404, detail="Property not found")
        property_data = dict(prop)

        # Gather all related data
        cur.execute("SELECT * FROM maintenance_tasks WHERE property_id = ?", (property_id,))
        tasks = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT * FROM maintenance_logs WHERE property_id = ?", (property_id,))
        logs = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT * FROM renovations WHERE property_id = ?", (property_id,))
        renovations = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT * FROM inventory WHERE property_id = ?", (property_id,))
        inventory = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT * FROM documents WHERE property_id = ?", (property_id,))
        documents = [dict(r) for r in cur.fetchall()]

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Add structured summary JSON
            export_dict = {
                "format": "Immo-Tion CIL Export",
                "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "property": property_data,
                "maintenance_tasks": tasks,
                "maintenance_logs": logs,
                "renovations": renovations,
                "inventory": inventory,
                "documents": documents,
            }
            zf.writestr("carnet_logement.json", json.dumps(export_dict, indent=2, ensure_ascii=False))

            # 2. Add human-readable Markdown dossier
            md_content = f"""# 🏠 Carnet d'Information du Logement (CIL)
**Généré par Immo-Tion le {datetime.date.today().isoformat()}**

## 1. Identité du Bien
- **Dénomination** : {property_data['name']}
- **Adresse** : {property_data['address']}, {property_data.get('postal_code', '')} {property_data.get('city', '')}
- **Surface Habitable** : {property_data.get('surface_m2', 'N/A')} m² (Terrain: {property_data.get('land_surface_m2', 'N/A')} m²)
- **Parcelle Cadastrale** : {property_data.get('cadastral_reference', 'N/A')}
- **DPE / GES** : {property_data.get('dpe_rating', 'N/A')} / {property_data.get('ges_rating', 'N/A')}

## 2. Historique des Rénovations et Travaux ({len(renovations)})
"""
            for r in renovations:
                md_content += f"- **{r['title']}** ({r['status']}) - Coût réel: {r['actual_cost']} € - Artisan: {r.get('contractor_name', 'N/A')} (Décennale: {r.get('warranty_decennale_expiry', 'N/A')})\n"

            md_content += f"\n## 3. Historique d'Entretien & Maintenance ({len(logs)})\n"
            for l in logs:
                md_content += f"- [{l['performed_date']}] Intervention par {l.get('performed_by', 'Propriétaire')} ({l.get('cost', 0)} €) : {l.get('notes', 'Sans note')}\n"

            md_content += f"\n## 4. Équipements & Garanties ({len(inventory)})\n"
            for it in inventory:
                md_content += f"- **{it['name']}** ({it.get('brand', '')} {it.get('model_number', '')}) - Garantie jusqu'au: {it.get('warranty_expiry_date', 'N/A')}\n"

            zf.writestr("DOSSIER_CIL.md", md_content)

            # 3. Embed existing stored documents
            for doc in documents:
                if doc.get("file_path"):
                    disk_file = settings.UPLOAD_DIR / doc["file_path"]
                    if disk_file.exists():
                        safe_arcname = f"documents/{doc['category']}/{doc['title']}_{doc['file_path']}"
                        zf.write(disk_file, arcname=safe_arcname)

        zip_buffer.seek(0)
        filename = f"CIL_Immo_Tion_{property_id}_{datetime.date.today().strftime('%Y%m%d')}.zip"
        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    finally:
        conn.close()
