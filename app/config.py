from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration using Pydantic settings."""

    # OpenAI
    openai_api_key: str

    # GitHub (для Obsidian vault)
    github_token: str
    github_repo_owner: str
    github_repo_name: str
    github_branch: str = "main"

    # App settings
    app_env: str = "development"
    log_level: str = "INFO"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Singleton instance
settings = Settings()
