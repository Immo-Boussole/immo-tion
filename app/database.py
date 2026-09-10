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

            -- Taxes & Fiscal Notices (Taxe foncière, TEOM, taxes locales)
            CREATE TABLE IF NOT EXISTS taxes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
                tax_year INTEGER NOT NULL,
                tax_type TEXT NOT NULL DEFAULT 'Taxe Foncière',
                amount REAL NOT NULL,
                teom_amount REAL DEFAULT 0.0,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Payé',
                document_path TEXT,
                reference_number TEXT,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- Users (Comptes utilisateurs et authentification)
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash BLOB NOT NULL,
                salt BLOB NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                email TEXT,
                apprise_url TEXT,
                auto_read_after_days INTEGER DEFAULT 30,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- Notifications (In-App notifications center)
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                property_id INTEGER REFERENCES properties(id) ON DELETE SET NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'system',
                link_url TEXT,
                event_key TEXT,
                is_read BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                read_at DATETIME
            );
            CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read);
            CREATE INDEX IF NOT EXISTS idx_notifications_event_key ON notifications(event_key);
            CREATE INDEX IF NOT EXISTS idx_notifications_category ON notifications(category);

            -- App Settings (Paramètres globaux & jetons)
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Safe column migration for users table
            user_cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
            if "apprise_url" not in user_cols:
                conn.execute("ALTER TABLE users ADD COLUMN apprise_url TEXT")
            if "auto_read_after_days" not in user_cols:
                conn.execute("ALTER TABLE users ADD COLUMN auto_read_after_days INTEGER DEFAULT 30")
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


def get_setting(key: str, default: Optional[str] = None, db_path: Optional[Path] = None) -> Optional[str]:
    """Retrieve an application setting value from app_settings table."""
    conn = get_db_connection(db_path)
    try:
        row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default
    finally:
        conn.close()


def set_setting(key: str, value: str, db_path: Optional[Path] = None) -> None:
    """Store or update an application setting in app_settings table."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO app_settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                """,
                (key, value),
            )
    finally:
        conn.close()


def get_user_count(db_path: Optional[Path] = None) -> int:
    """Return the total number of registered users."""
    conn = get_db_connection(db_path)
    try:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()


def get_user_by_username(username: str, db_path: Optional[Path] = None) -> Optional[sqlite3.Row]:
    """Return user row by username or None if not found."""
    conn = get_db_connection(db_path)
    try:
        return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    finally:
        conn.close()


def get_bridge_api_token(db_path: Optional[Path] = None) -> str:
    """Return active Bridge API token, generating one if not yet initialized."""
    token = get_setting("bridge_api_token", db_path=db_path)
    if not token:
        import secrets
        token = secrets.token_hex(24)
        set_setting("bridge_api_token", token, db_path=db_path)
    return token


def regenerate_bridge_api_token(db_path: Optional[Path] = None) -> str:
    """Generate and store a brand-new Bridge API token, invalidating the previous one."""
    import secrets
    token = secrets.token_hex(24)
    set_setting("bridge_api_token", token, db_path=db_path)
    return token


# ── Notification Helpers ───────────────────────────────────────────────────────

def create_notification(
    title: str,
    message: str,
    category: str = "system",
    property_id: Optional[int] = None,
    user_id: Optional[int] = None,
    link_url: Optional[str] = None,
    event_key: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> int:
    """Insert a new in-app notification and return its ID."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            cur = conn.execute(
                """
                INSERT INTO notifications (
                    user_id, property_id, title, message, category, link_url, event_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, property_id, title, message, category, link_url, event_key),
            )
            return cur.lastrowid
    finally:
        conn.close()


def is_event_already_notified(event_key: str, db_path: Optional[Path] = None) -> bool:
    """Check if an event_key was already notified to prevent duplicate alerts."""
    if not event_key:
        return False
    conn = get_db_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM notifications WHERE event_key = ? LIMIT 1",
            (event_key,),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def get_notifications(
    user_id: Optional[int] = None,
    role: str = "user",
    category: Optional[str] = None,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    db_path: Optional[Path] = None,
) -> list:
    """Retrieve notifications scoped by user/role with optional category and unread filters."""
    conn = get_db_connection(db_path)
    try:
        query = """
            SELECT n.*, p.name AS property_name
            FROM notifications n
            LEFT JOIN properties p ON n.property_id = p.id
            WHERE 1=1
        """
        params = []

        # Scope: if not admin, show global (user_id IS NULL) or specifically for this user
        if role != "admin" and user_id is not None:
            query += " AND (n.user_id = ? OR n.user_id IS NULL)"
            params.append(user_id)

        if category and category != "all":
            query += " AND n.category = ?"
            params.append(category)

        if unread_only:
            query += " AND n.is_read = 0"

        query += " ORDER BY n.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_unread_notifications_count(
    user_id: Optional[int] = None,
    role: str = "user",
    db_path: Optional[Path] = None,
) -> int:
    """Return count of unread notifications visible to user/role."""
    conn = get_db_connection(db_path)
    try:
        query = "SELECT COUNT(*) AS cnt FROM notifications WHERE is_read = 0"
        params = []
        if role != "admin" and user_id is not None:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
        row = conn.execute(query, params).fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()


def mark_notification_read(
    notification_id: int,
    user_id: Optional[int] = None,
    role: str = "user",
    db_path: Optional[Path] = None,
) -> bool:
    """Mark a single notification as read."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            query = "UPDATE notifications SET is_read = 1, read_at = CURRENT_TIMESTAMP WHERE id = ?"
            params = [notification_id]
            if role != "admin" and user_id is not None:
                query += " AND (user_id = ? OR user_id IS NULL)"
                params.append(user_id)
            cur = conn.execute(query, params)
            return cur.rowcount > 0
    finally:
        conn.close()


def mark_notification_unread(
    notification_id: int,
    user_id: Optional[int] = None,
    role: str = "user",
    db_path: Optional[Path] = None,
) -> bool:
    """Mark a single notification as unread."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            query = "UPDATE notifications SET is_read = 0, read_at = NULL WHERE id = ?"
            params = [notification_id]
            if role != "admin" and user_id is not None:
                query += " AND (user_id = ? OR user_id IS NULL)"
                params.append(user_id)
            cur = conn.execute(query, params)
            return cur.rowcount > 0
    finally:
        conn.close()


def mark_all_notifications_read(
    user_id: Optional[int] = None,
    role: str = "user",
    category: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> int:
    """Mark all notifications matching filters as read."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            query = "UPDATE notifications SET is_read = 1, read_at = CURRENT_TIMESTAMP WHERE is_read = 0"
            params = []
            if role != "admin" and user_id is not None:
                query += " AND (user_id = ? OR user_id IS NULL)"
                params.append(user_id)
            if category and category != "all":
                query += " AND category = ?"
                params.append(category)
            cur = conn.execute(query, params)
            return cur.rowcount
    finally:
        conn.close()


def delete_notification(
    notification_id: int,
    user_id: Optional[int] = None,
    role: str = "user",
    db_path: Optional[Path] = None,
) -> bool:
    """Delete a notification."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            query = "DELETE FROM notifications WHERE id = ?"
            params = [notification_id]
            if role != "admin" and user_id is not None:
                query += " AND (user_id = ? OR user_id IS NULL)"
                params.append(user_id)
            cur = conn.execute(query, params)
            return cur.rowcount > 0
    finally:
        conn.close()


def cleanup_expired_notifications(db_path: Optional[Path] = None) -> int:
    """Automatically mark as read or clean up old notifications based on users' auto_read_after_days."""
    conn = get_db_connection(db_path)
    total_cleaned = 0
    try:
        with conn:
            # For each user, mark notifications older than auto_read_after_days as read
            users = conn.execute("SELECT id, auto_read_after_days FROM users").fetchall()
            for u in users:
                days = u["auto_read_after_days"] or 30
                cur = conn.execute(
                    """
                    UPDATE notifications
                    SET is_read = 1, read_at = CURRENT_TIMESTAMP
                    WHERE is_read = 0
                      AND user_id = ?
                      AND created_at <= datetime('now', '-' || ? || ' days')
                    """,
                    (u["id"], days),
                )
                total_cleaned += cur.rowcount

            # Global notifications cleanup (fallback 30 days)
            cur_global = conn.execute(
                """
                UPDATE notifications
                SET is_read = 1, read_at = CURRENT_TIMESTAMP
                WHERE is_read = 0
                  AND user_id IS NULL
                  AND created_at <= datetime('now', '-30 days')
                """
            )
            total_cleaned += cur_global.rowcount
        return total_cleaned
    finally:
        conn.close()


def get_user_apprise_urls(db_path: Optional[Path] = None) -> list:
    """Return all configured Apprise URLs across users."""
    conn = get_db_connection(db_path)
    try:
        rows = conn.execute("SELECT apprise_url FROM users WHERE apprise_url IS NOT NULL AND TRIM(apprise_url) != ''").fetchall()
        return [r["apprise_url"].strip() for r in rows if r["apprise_url"]]
    finally:
        conn.close()


