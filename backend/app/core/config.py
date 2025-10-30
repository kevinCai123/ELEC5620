from __future__ import annotations

from pathlib import Path
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
    )

    app_name: str = "Study Companion Backend"
    environment: str = Field(default="development")
    database_url: str = Field(..., alias="DATABASE_URL")
    sentry_dsn: str | None = Field(default=None, alias="SENTRY_DSN")
    vite_sentry_dsn: str | None = Field(default=None, alias="VITE_SENTRY_DSN")

    openweather_api_key: str | None = Field(default=None, alias="OPENWEATHER_API_KEY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_embed_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBED_MODEL")
    local_embeddings_model: str | None = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", alias="LOCAL_EMBEDDINGS_MODEL"
    )
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    google_client_id: str | None = Field(default=None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: str | None = Field(default=None, alias="GOOGLE_CLIENT_SECRET")
    google_refresh_token: str | None = Field(default=None, alias="GOOGLE_REFRESH_TOKEN")
    google_api_user_email: str | None = Field(default=None, alias="GOOGLE_API_USER_EMAIL")
    google_redirect_uri: str | None = Field(default=None, alias="GOOGLE_REDIRECT_URI")
    frontend_origin: str | None = Field(default=None, alias="FRONTEND_ORIGIN")
    dev_allow_oauth_write_dotenv: bool = Field(default=False, alias="DEV_ALLOW_OAUTH_WRITE_DOTENV")
    default_weather_location: str = Field(default="Sydney,AU", alias="DEFAULT_WEATHER_LOCATION")

    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int | None = Field(default=None, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_pass: str | None = Field(default=None, alias="SMTP_PASS")

    default_timezone: str = "Australia/Sydney"
    generic_travel_buffer_minutes: int = Field(default=15, alias="GENERIC_TRAVEL_BUFFER_MINUTES")

    vite_api_base_url: str | None = Field(default=None, alias="VITE_API_BASE_URL")

    google_maps_base_url: str = Field(
        default="https://www.google.com/maps/dir/?api=1&travelmode=walking",
        alias="GOOGLE_MAPS_BASE_URL",
    )

    _OPTIONAL_STR_FIELDS = {
        "sentry_dsn",
        "vite_sentry_dsn",
        "openweather_api_key",
        "openai_api_key",
        "local_embeddings_model",
        "redis_url",
        "smtp_host",
        "smtp_user",
        "smtp_pass",
        "vite_api_base_url",
        "google_client_id",
        "google_client_secret",
        "google_refresh_token",
        "google_api_user_email",
        "google_redirect_uri",
        "frontend_origin",
        "dev_allow_oauth_write_dotenv",
    }

    _DEFAULTABLE_STR_FIELDS = {
        "openai_model": "gpt-4o-mini",
        "openai_embed_model": "text-embedding-3-small",
        "local_embeddings_model": "sentence-transformers/all-MiniLM-L6-v2",
    }

    @field_validator(*_OPTIONAL_STR_FIELDS, mode="before")
    @classmethod
    def _blank_optional_str_to_none(cls, value: Any) -> Any:
        if isinstance(value, str) and value.strip() == "":
            return None
        return value

    @field_validator(*_DEFAULTABLE_STR_FIELDS.keys(), mode="before")
    @classmethod
    def _blank_string_to_default(cls, value: Any, info) -> Any:
        if isinstance(value, str) and value.strip() == "":
            return cls._DEFAULTABLE_STR_FIELDS[info.field_name]
        return value

    @field_validator("smtp_port", mode="before")
    @classmethod
    def _blank_to_none_int(cls, value: Any) -> Any:
        if isinstance(value, str) and value.strip() == "":
            return None
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


__all__ = ["Settings", "get_settings"]
