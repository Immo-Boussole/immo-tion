"""Application configuration and environment settings."""

from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Immo-Tion"
    APP_ENV: str = "production"
    APP_PORT: int = 8085
    SECRET_KEY: str = "immo-tion-default-secret-key-change-in-production"

    # Filesystem storage paths
    DATA_DIR: Path = Path("/data") if Path("/data").exists() else Path(__file__).resolve().parent.parent / "data"
    UPLOAD_DIR_NAME: str = "uploads"

    # Notification & Multi-channel settings
    APPRISE_URL: str = ""
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "notifications@immo-tion.local"
    SMTP_USE_TLS: bool = True
    WEBHOOK_URLS: str = ""  # Comma-separated URLs

    # Header Enforcement (Cloudflare Tunnel / Reverse Proxy security)
    # Format: comma-separated list of "Header-Name" (presence only) or "Header-Name:Expected-Value" (exact match)
    # Example: "CF-Ray,X-Origin-Verify:my-super-secret-token"
    # Disabled when empty or whitespace.
    REQUIRED_HEADERS: str = ""
    REQUIRED_HEADERS_EXEMPT_LOCALHOST: bool = True

    @property
    def UPLOAD_DIR(self) -> Path:
        p = self.DATA_DIR / self.UPLOAD_DIR_NAME
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def DB_PATH(self) -> Path:
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        return self.DATA_DIR / "immo_tion.db"

    @property
    def parsed_webhook_urls(self) -> List[str]:
        if not self.WEBHOOK_URLS.strip():
            return []
        return [url.strip() for url in self.WEBHOOK_URLS.split(",") if url.strip()]

    @property
    def parsed_required_headers(self) -> dict:
        """Parse REQUIRED_HEADERS into a dictionary {header_name_lowercase: expected_value_or_none}."""
        if not self.REQUIRED_HEADERS or not self.REQUIRED_HEADERS.strip():
            return {}
        result = {}
        for item in self.REQUIRED_HEADERS.split(","):
            item = item.strip()
            if not item:
                continue
            if ":" in item:
                key, val = item.split(":", 1)
                result[key.strip().lower()] = val.strip()
            else:
                result[item.lower()] = None
        return result

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
