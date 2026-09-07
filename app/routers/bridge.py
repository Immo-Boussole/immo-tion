"""Bridge router providing seamless integration and 1-click import from Immo-Boussole."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.auth import verify_bearer_token
from app.models import ImmoBoussoleImportPayload
from app.database import get_db_connection, seed_standard_maintenance_tasks

router = APIRouter(prefix="/api/v1/bridge", tags=["Immo-Boussole Bridge"])


@router.post("/import-listing", status_code=status.HTTP_201_CREATED)
async def import_listing_from_immo_boussole(
    payload: ImmoBoussoleImportPayload,
    token: str = Depends(verify_bearer_token),
):
    """Import an acquired real estate property directly from Immo-Boussole."""
    conn = get_db_connection()
    try:
        # Build comprehensive initial notes from contacts
        notes_lines = ["Importé automatiquement depuis Immo-Boussole."]
        if payload.contacts:
            notes_lines.append("\nContacts d'origine :")
            for c in payload.contacts:
                notes_lines.append(f"- {c.get('role', 'Contact')} : {c.get('name', '')} ({c.get('phone', '')} / {c.get('email', '')})")

        cover_img = payload.photos[0] if payload.photos else None

        with conn:
            cur = conn.execute(
                """
                INSERT INTO properties (
                    name, address, postal_code, city, surface_m2, land_surface_m2,
                    cadastral_reference, dpe_rating, ges_rating, acquisition_price,
                    notes, cover_image
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.title,
                    payload.address,
                    payload.postal_code,
                    payload.city,
                    payload.surface_m2,
                    payload.land_surface_m2,
                    payload.cadastral_reference,
                    payload.dpe_rating,
                    payload.ges_rating,
                    payload.price,
                    "\n".join(notes_lines),
                    cover_img,
                ),
            )
            property_id = cur.lastrowid

            # Import furniture & equipment from Immo-Boussole visit inventory
            if payload.furniture_inventory:
                for item in payload.furniture_inventory:
                    conn.execute(
                        """
                        INSERT INTO inventory (property_id, name, category, notes)
                        VALUES (?, ?, 'Mobilier', ?)
                        """,
                        (property_id, item.get("name", "Équipement"), f"État: {item.get('condition', 'Bon')} | Pièce: {item.get('room', 'N/A')}"),
                    )

        # Seed standard lifecycle maintenance tasks if requested
        if payload.seed_tasks and property_id:
            seed_standard_maintenance_tasks(property_id)

        return {
            "status": "success",
            "message": "Property successfully imported into Immo-Tion",
            "property_id": property_id,
            "property_name": payload.title,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import property: {str(e)}")
    finally:
        conn.close()
