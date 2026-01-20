from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import logging
import tempfile
import os
from pathlib import Path

from app.config import settings
from app.models import VoiceNoteResponse, HealthCheckResponse
from app.services.transcriber import WhisperTranscriber
from app.services.agent import VoiceNotesAgent
from app.services.github_vault import GitHubVaultService
from app.services.google_calendar import GoogleCalendarService

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Voice Notes Service",
    description="AI-powered voice notes processing with Obsidian integration",
    version="1.0.0"
)

# Initialize services
vault_service = GitHubVaultService(
    token=settings.github_token,
    repo_owner=settings.github_repo_owner,
    repo_name=settings.github_repo_name,
    branch=settings.github_branch
)

# Initialize Google Calendar (опционально)
calendar_service = None
if settings.google_calendar_credentials:
    try:
        calendar_service = GoogleCalendarService(
            credentials_json=settings.google_calendar_credentials,
            calendar_id=settings.google_calendar_id
        )
        logger.info("Google Calendar service initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Google Calendar: {e}")
        logger.warning("Calendar integration will be disabled")

transcriber = WhisperTranscriber(api_key=settings.openai_api_key)
agent = VoiceNotesAgent(
    api_key=settings.openai_api_key,
    vault_service=vault_service,
    calendar_service=calendar_service
)


@app.get("/api/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Basic health check - services are initialized on startup
        # Could add actual API pings here if needed
        services_status = {
            "openai": "configured",
            "github": "configured",
            "google_calendar": "enabled" if calendar_service else "disabled"
        }

        return HealthCheckResponse(
            status="healthy",
            services=services_status,
            vault={
                "repo": f"{settings.github_repo_owner}/{settings.github_repo_name}",
                "branch": settings.github_branch
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.post("/api/voice", response_model=VoiceNoteResponse)
async def process_voice_note(audio: UploadFile = File(...)):
    """
    Process voice note: transcribe audio and execute AI agent actions.

    Args:
        audio: Audio file (m4a, mp3, wav, webm)

    Returns:
        VoiceNoteResponse with transcription and executed actions
    """
    temp_file_path = None

    try:
        # Validate file
        if not audio:
            raise HTTPException(status_code=400, detail="No audio file provided")

        # Validate file extension
        allowed_extensions = {'.m4a', '.mp3', '.wav', '.webm'}
        file_ext = Path(audio.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}"
            )

        logger.info(f"Processing voice note: {audio.filename}")

        # 1. Save temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file_path = temp_file.name
            content = await audio.read()
            temp_file.write(content)

        logger.info(f"Saved temporary file: {temp_file_path}")

        # 2. Transcribe with Whisper
        logger.info("Starting transcription...")
        transcription = await transcriber.transcribe(temp_file_path)
        logger.info(f"Transcription completed: {len(transcription)} characters")

        # 3. Process with AI agent
        logger.info("Processing with AI agent...")
        agent_result = await agent.process_transcription(transcription)
        logger.info(f"Agent processing completed: {len(agent_result['actions'])} actions")

        # 4. Return results
        return VoiceNoteResponse(
            success=True,
            transcription=transcription,
            actions=agent_result["actions"],
            agent_summary=agent_result["summary"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice processing failed: {e}", exc_info=True)
        return VoiceNoteResponse(
            success=False,
            error="Internal server error",
            details=str(e)
        )
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "Voice Notes Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "voice": "/api/voice (POST)"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
