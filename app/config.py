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

    # Notification & SMTP settings
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "notifications@immo-tion.local"
    SMTP_USE_TLS: bool = True
    WEBHOOK_URLS: str = ""  # Comma-separated URLs

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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
