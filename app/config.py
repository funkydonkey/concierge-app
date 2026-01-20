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

    # App settings
    app_env: str = "development"
    log_level: str = "INFO"
    port: int = 8000

    @property
    def google_calendar_credentials(self) -> Optional[dict]:
        """Parse Google Calendar credentials from JSON string."""
        if self.google_calendar_credentials_json:
            return json.loads(self.google_calendar_credentials_json)
        return None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Singleton instance
settings = Settings()
