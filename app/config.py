from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import json


class Settings(BaseSettings):
    """Application configuration using Pydantic settings."""

    # OpenAI
    openai_api_key: str

    # GitHub (для Obsidian vault)
    github_token: str
    github_repo_owner: str
    github_repo_name: str
    github_branch: str = "main"

    # Google Calendar (опционально)
    google_calendar_credentials_json: Optional[str] = None
    google_calendar_id: str = "primary"
    google_calendar_timezone: str = "Europe/Berlin"  # CET timezone

    # App settings
    app_env: str = "development"
    log_level: str = "INFO"
    port: int = 8000

    @property
    def google_calendar_credentials(self) -> Optional[dict]:
        """Parse Google Calendar credentials from JSON string."""
        if self.google_calendar_credentials_json:
            try:
                return json.loads(self.google_calendar_credentials_json)
            except json.JSONDecodeError as e:
                import logging
                logging.error(f"Failed to parse GOOGLE_CALENDAR_CREDENTIALS_JSON: {e}")
                return None
        return None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Singleton instance
settings = Settings()
