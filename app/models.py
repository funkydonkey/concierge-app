from pydantic import BaseModel


class VoiceNoteResponse(BaseModel):
    """Response model for voice note processing."""

    success: bool
    transcription: str | None = None
    actions: list[dict] = []
    agent_summary: str | None = None
    error: str | None = None
    details: str | None = None


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str
    version: str = "1.0.0"
    services: dict[str, str] = {}
    vault: dict[str, str] | None = None
