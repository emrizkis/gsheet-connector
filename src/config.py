import os
from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from src.exceptions import ConfigurationError


class Settings(BaseSettings):
    """Application settings class that loads and validates variables from .env."""
    
    google_service_account_file: str = Field(
        default="credentials.json",
        validation_alias="GOOGLE_SERVICE_ACCOUNT_FILE"
    )
    spreadsheet_id: str = Field(
        validation_alias="SPREADSHEET_ID"
    )
    sheet_range: str = Field(
        default="Sheet1!A1:E100",
        validation_alias="SHEET_RANGE"
    )
    filter_sprint_id: Optional[str] = Field(
        default=None,
        validation_alias="FILTER_SPRINT_ID"
    )
    cache_ttl_seconds: int = Field(
        default=300,
        validation_alias="CACHE_TTL_SECONDS"
    )
    gantt_title: str = Field(
        default="Project Gantt Chart",
        validation_alias="GANTT_TITLE"
    )
    kanban_title: str = Field(
        default="Project Kanban Board",
        validation_alias="KANBAN_TITLE"
    )

    # Menggunakan SettingsConfigDict untuk memuat konfigurasi dari file .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("spreadsheet_id")
    @classmethod
    def validate_spreadsheet_id(cls, v: str) -> str:
        if not v or v == "YOUR_SPREADSHEET_ID_HERE" or v.strip() == "":
            raise ValueError("SPREADSHEET_ID harus diisi dengan ID Google Sheet yang valid.")
        return v.strip()

    @field_validator("google_service_account_file")
    @classmethod
    def validate_creds_path(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_FILE tidak boleh kosong.")
        return v.strip()

    @field_validator("filter_sprint_id")
    @classmethod
    def validate_filter_sprint_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_stripped = v.strip()
            if not v_stripped or v_stripped == "YOUR_FILTER_SPRINT_ID_HERE":
                return None
            return v_stripped
        return None

    @field_validator("cache_ttl_seconds")
    @classmethod
    def validate_cache_ttl(cls, v: int) -> int:
        # Enforce non-negative TTL
        return max(0, v)


def load_config() -> Settings:
    """Loads and validates the configuration, throwing ConfigurationError if invalid."""
    try:
        return Settings()
    except Exception as e:
        raise ConfigurationError(f"Gagal memuat konfigurasi: {e}") from e
