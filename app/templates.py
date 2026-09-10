"""Centralized Jinja2Templates singleton with i18n and global template helpers."""

from pathlib import Path
from fastapi.templating import Jinja2Templates

from app.translations import get_text, get_available_languages

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

def get_unread_count(request) -> int:
    """Return the unread notification count for the current session user."""
    try:
        from app.auth import get_current_user
        from app.database import get_unread_notifications_count
        user = get_current_user(request)
        if not user:
            return 0
        return get_unread_notifications_count(user_id=user["id"], role=user.get("role", "user"))
    except Exception:
        return 0


# Register Jinja2 global functions
templates.env.globals["t"] = get_text
templates.env.globals["app_version"] = "0.1.0"
templates.env.globals["get_available_languages"] = get_available_languages
templates.env.globals["get_unread_count"] = get_unread_count

