"""CASHNET Backend Configuration via Pydantic Settings."""

from pathlib import Path
from typing import Any, List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application and environment settings."""

    # Project Information
    PROJECT_NAME: str = "CASHNET Cybercrime Cash-Out Intervention Engine"
    PROJECT_VERSION: str = "2.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    SIMULATION_MODE: bool = True  # Explicit disclaimer that all records and predictions are synthetic prototypes

    # Database Settings (Default to SQLite for local development, PostgreSQL compatible)
    DATABASE_URL: str = "sqlite:///./cashnet_dev.db"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # CORS Settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Synthetic Dataset Import Defaults
    DEFAULT_DATA_DIR: str = "data_v2"

    # ML Artifacts Directory
    MODELS_DIR: str = "models"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Any) -> str:
        """Normalize database URL for PostgreSQL compatibility."""
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        """Support comma-separated strings, JSON arrays, and lists of CORS origins."""
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return [str(i).strip() for i in v]
        return ["*"]


settings = Settings()
