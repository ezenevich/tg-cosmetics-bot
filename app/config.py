"""Configuration management for the Telegram bot."""
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    bot_token: SecretStr = Field(..., alias="BOT_TOKEN")
    mongo_uri: str = Field(..., alias="MONGO_URI")
    mongo_db: str = Field("tg_cosmetics", alias="MONGO_DB_NAME")
    initial_admin_id: int = Field(23452347532, alias="INITIAL_ADMIN_ID")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings instance."""

    return Settings()
