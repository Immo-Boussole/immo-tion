"""Centralized Jinja2Templates singleton with i18n and global template helpers."""

from pathlib import Path
from fastapi.templating import Jinja2Templates

from app.translations import get_text, get_available_languages

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Register Jinja2 global functions
templates.env.globals["t"] = get_text
templates.env.globals["app_version"] = "0.1.0"
templates.env.globals["get_available_languages"] = get_available_languages
