"""SQLite Database manager with WAL mode and schema initialization."""

import sqlite3
from pathlib import Path
from typing import Optional
from app.config import settings


def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Return a configured SQLite connection with row factory and WAL mode enabled."""
    target_path = db_path or settings.DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(target_path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    """Initialize the SQLite database schema if not already present."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.executescript("""
            -- Properties (Homes tracked)
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                postal_code TEXT,
                city TEXT,
                surface_m2 REAL,
                land_surface_m2 REAL,
                cadastral_reference TEXT,
                dpe_rating TEXT,
                ges_rating TEXT,
                acquisition_date TEXT,
                acquisition_price REAL,
                notes TEXT,
                cover_image TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- Maintenance Tasks (Opérations / Carnet d'entretien périodique)
            CREATE TABLE IF NOT EXISTS maintenance_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL DEFAULT 'Autre',
                recurrence_months INTEGER NOT NULL DEFAULT 12,
                last_performed_date TEXT,
                next_due_date TEXT NOT NULL,
                estimated_cost REAL,
                preferred_contractor TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- Maintenance Intervention Logs (Historique infalsifiable)
            CREATE TABLE IF NOT EXISTS maintenance_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL REFERENCES maintenance_tasks(id) ON DELETE CASCADE,
                property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
                performed_date TEXT NOT NULL,
                performed_by TEXT,
                cost REAL,
                notes TEXT,
                document_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- Renovations & Works (Travaux & Chantiers)
            CREATE TABLE IF NOT EXISTS renovations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'Général',
                status TEXT NOT NULL DEFAULT 'Planifié',
                estimated_budget REAL,
                actual_cost REAL DEFAULT 0.0,
                start_date TEXT,
                end_date TEXT,
                contractor_name TEXT,
                contractor_siret TEXT,
                contractor_phone TEXT,
                contractor_email TEXT,
                warranty_decennale_expiry TEXT,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- Renovation Expenses (Devis, Acomptes, Factures)
            CREATE TABLE IF NOT EXISTS renovation_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                renovation_id INTEGER NOT NULL REFERENCES renovations(id) ON DELETE CASCADE,
                description TEXT NOT NULL,
                expense_type TEXT NOT NULL DEFAULT 'Facture',
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                is_paid INTEGER NOT NULL DEFAULT 1,
                document_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- Renovation Photo Log (Avant / Pendant / Après)
            CREATE TABLE IF NOT EXISTS renovation_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                renovation_id INTEGER NOT NULL REFERENCES renovations(id) ON DELETE CASCADE,
                photo_type TEXT NOT NULL DEFAULT 'Après',
                file_path TEXT NOT NULL,
                caption TEXT,
                date_taken TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- Equipment Inventory & Warranties (Inventaire / Équipements)
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                brand TEXT,
                model_number TEXT,
                serial_number TEXT,
                category TEXT NOT NULL DEFAULT 'Autre',
                purchase_date TEXT,
                purchase_price REAL,
                warranty_expiry_date TEXT,
                vendor TEXT,
                manual_path TEXT,
                invoice_path TEXT,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- Document Vault (Coffre-fort documentaire)
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'Autre',
                file_path TEXT NOT NULL,
                file_size INTEGER,
                mime_type TEXT,
                upload_date TEXT DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            );

            -- Energy & Utility Readings (Consommations & Énergie)
            CREATE TABLE IF NOT EXISTS energy_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
                energy_type TEXT NOT NULL,
                reading_date TEXT NOT NULL,
                reading_value REAL NOT NULL,
                unit TEXT NOT NULL,
                cost REAL,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)
    finally:
        conn.close()


STANDARD_MAINTENANCE_TEMPLATES = [
    {
        "title": "Entretien annuel de la chaudière / pompe à chaleur",
        "category": "Chauffage",
        "recurrence_months": 12,
        "description": "Obligation légale annuelle d'entretien et réglage par un professionnel certifié.",
        "estimated_cost": 150.0,
    },
    {
        "title": "Ramonage des conduits de fumée (cheminée / poêle)",
        "category": "Chauffage",
        "recurrence_months": 12,
        "description": "Ramonage mécanique obligatoire annuel ou semestriel avec certificat d'assurance.",
        "estimated_cost": 80.0,
    },
    {
        "title": "Contrôle et nettoyage des filtres VMC",
        "category": "Ventilation",
        "recurrence_months": 6,
        "description": "Dépoussiérage des bouches d'extraction et remplacement des filtres du groupe.",
        "estimated_cost": 25.0,
    },
    {
        "title": "Nettoyage des chéneaux et gouttières",
        "category": "Toiture",
        "recurrence_months": 12,
        "description": "Évacuation des feuilles mortes avant l'hiver pour éviter les débordements et infiltrations.",
        "estimated_cost": 50.0,
    },
    {
        "title": "Test des détecteurs autonomes avertisseurs de fumée (DAAF)",
        "category": "Sécurité",
        "recurrence_months": 1,
        "description": "Test de la sonnerie et dépoussiérage de la cellule optique.",
        "estimated_cost": 0.0,
    },
    {
        "title": "Purge des radiateurs à eau chaude",
        "category": "Plomberie",
        "recurrence_months": 12,
        "description": "Évacuation de l'air accumulé avant le démarrage de la saison de chauffe.",
        "estimated_cost": 0.0,
    },
]


def seed_standard_maintenance_tasks(property_id: int, db_path: Optional[Path] = None) -> None:
    """Seed standard recommended maintenance tasks for a newly created or imported property."""
    import datetime
    today = datetime.date.today()
    conn = get_db_connection(db_path)
    try:
        with conn:
            for tmpl in STANDARD_MAINTENANCE_TEMPLATES:
                due_date = today + datetime.timedelta(days=tmpl["recurrence_months"] * 30)
                conn.execute(
                    """
                    INSERT INTO maintenance_tasks (
                        property_id, title, description, category, recurrence_months, next_due_date, estimated_cost
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        property_id,
                        tmpl["title"],
                        tmpl["description"],
                        tmpl["category"],
                        tmpl["recurrence_months"],
                        due_date.isoformat(),
                        tmpl["estimated_cost"],
                    ),
                )
    finally:
        conn.close()
