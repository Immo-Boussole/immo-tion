"""Dynamic Internationalization (i18n) engine for Immo-Tion."""

import glob
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import Request

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"

_translations: Dict[str, Dict[str, Any]] = {}
_translations_mtime: Dict[str, float] = {}

LANGUAGE_NAMES = {
    "fr": "Français",
    "en": "English",
}


def load_translations() -> None:
    """Load or reload all locale JSON files found in locales/."""
    global _translations, _translations_mtime
    if not LOCALES_DIR.exists():
        return

    for file_path in LOCALES_DIR.glob("*.json"):
        lang = file_path.stem
        try:
            mtime = file_path.stat().st_mtime
            if lang not in _translations or _translations_mtime.get(lang, 0) < mtime:
                with open(file_path, "r", encoding="utf-8") as f:
                    _translations[lang] = json.load(f)
                _translations_mtime[lang] = mtime
        except Exception as e:
            print(f"[i18n] Error loading {file_path}: {e}")
            if lang not in _translations:
                _translations[lang] = {}


def get_available_languages() -> List[Dict[str, str]]:
    """Return available languages detected in the locales directory."""
    load_translations()
    langs = []
    for code in _translations.keys():
        langs.append({
            "code": code,
            "name": LANGUAGE_NAMES.get(code, code.upper()),
        })
    return langs or [{"code": "fr", "name": "Français"}, {"code": "en", "name": "English"}]


def get_text(request: Optional[Request], key: str, default: Optional[str] = None, **kwargs: Any) -> str:
    """Resolve a dot-notated translation key for the current request's language."""
    load_translations()

    # Resolve language preference: session > Accept-Language > default 'fr'
    lang = "fr"
    if request is not None:
        try:
            if hasattr(request, "session") and request.session.get("lang"):
                lang = request.session["lang"]
            else:
                accept = request.headers.get("Accept-Language", "").lower()
                if "en" in accept and "fr" not in accept:
                    lang = "en"
                elif "fr" in accept:
                    lang = "fr"
        except Exception:
            lang = "fr"

    if lang not in _translations and "fr" in _translations:
        lang = "fr"

    # Traverse nested dictionary
    parts = key.split(".")
    curr: Any = _translations.get(lang, {})
    for part in parts:
        if isinstance(curr, dict) and part in curr:
            curr = curr[part]
        else:
            # Fallback to French if requested in another language
            if lang != "fr":
                curr_fr: Any = _translations.get("fr", {})
                for p_fr in parts:
                    if isinstance(curr_fr, dict) and p_fr in curr_fr:
                        curr_fr = curr_fr[p_fr]
                    else:
                        curr_fr = None
                        break
                if curr_fr is not None:
                    curr = curr_fr
                    break
            curr = None
            break

    val = curr if isinstance(curr, str) else (default or key)
    if kwargs and isinstance(val, str):
        try:
            return val.format(**kwargs)
        except Exception:
            return val
    return val
