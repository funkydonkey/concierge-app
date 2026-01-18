# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Voice Notes Service** - AI-powered voice notes processing with automatic transcription and Obsidian integration. Records voice notes from iPhone (via iOS Shortcuts), transcribes with OpenAI Whisper, analyzes content with AI agents, and saves to Obsidian vault via GitHub API.

**Tech Stack**: FastAPI, OpenAI Whisper API, OpenAI Agents SDK, GitHub API, Python 3.11+, `uv` package manager

**Key Concept**: The service acts as a bridge between iPhone → Cloud Backend (Render.com) → GitHub Repository ← Obsidian (local). GitHub serves as the intermediary because Obsidian runs locally while the service runs in the cloud.

## Setup and Development Commands

```bash
# Install uv package manager (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Configure environment
cp .env.example .env
# Edit .env with: OPENAI_API_KEY, GITHUB_TOKEN, GITHUB_REPO_OWNER, GITHUB_REPO_NAME

# Run development server
uvicorn app.main:app --reload --port 8000
# Access at: http://localhost:8000

# Run with direct Python execution
python -m app.main

# Testing
pytest                      # Run all tests
pytest --cov=app tests/     # With coverage
pytest tests/test_*.py -v   # Specific test file

# Code quality
black app/ tests/           # Format code
ruff check app/ tests/      # Lint
```

## Architecture

### Request Flow
1. **Audio Upload** → POST `/api/voice` with multipart/form-data
2. **Transcription** → `WhisperTranscriber` converts audio to text (Russian language)
3. **AI Processing** → `VoiceNotesAgent` analyzes transcription and determines actions
4. **GitHub Integration** → `GitHubVaultService` creates/updates files in vault
5. **Obsidian Sync** → Obsidian Git plugin auto-pulls changes (1-5 min delay)

### Core Services Architecture

**`app/services/transcriber.py`** - `WhisperTranscriber`
- Uses OpenAI Whisper API (`whisper-1` model)
- Supports: m4a, mp3, wav, webm formats
- Language: Russian (`language="ru"`)
- Returns plain text transcription

**`app/services/agent.py`** - `VoiceNotesAgent`
- System prompt defines behavior: analyze transcription, classify content, execute actions
- Content types: TODO tasks, Ideas, Work notes, Personal notes, Mixed content
- Uses OpenAI Agents SDK with function calling (tools)
- Model: `gpt-4o-mini`
- Returns: `{actions: list[dict], summary: str}`

**`app/services/github_vault.py`** - `GitHubVaultService`
- REST API client for GitHub Contents API
- All content must be base64 encoded/decoded
- SHA-based optimistic locking for updates (prevents conflicts)
- Methods:
  - `get_file(path)` → `FileInfo | None` (returns None on 404)
  - `create_file(path, content, commit_message)` → `FileInfo`
  - `update_file(path, content, sha, commit_message)` → `FileInfo`
  - `create_or_update_file(path, content, commit_message)` → `FileInfo` (convenience method)
  - `list_folder(folder_path)` → `list[str]` (bonus feature)

### AI Agent Tools (Function Calling)

**`app/tools/note_tools.py`**
- `create_note(title, content, folder, vault)` - Creates Markdown note with YAML frontmatter
  - Frontmatter: `created`, `source: voice`, `tags: [voice-note]`
  - Filename format: `{YYYY-MM-DD}-{title}.md`
  - Default folder: `Voice Notes`
- `append_to_note(note_path, content, vault)` - Appends to existing note
- `list_notes(folder, search_query, vault)` - Lists notes in folder

**`app/tools/todo_tools.py`**
- `add_todo_task(task, priority, due_date, vault)` - Adds task to `TODO.md`
  - Priority sections: 🔴 High, 🟡 Medium, 🟢 Low, ✅ Completed
  - Creates `TODO.md` if missing using `INITIAL_TODO_TEMPLATE`
  - Task format: `- [ ] {task} (due: {YYYY-MM-DD})`
  - Tasks inserted after section header, before next section

### Important Implementation Details

**GitHub API Constraints**:
- Rate limit: 5000 requests/hour (authenticated)
- Max file size: 1 MB via Contents API
- Returns 409 on SHA mismatch (conflict detection)
- Requires `X-GitHub-Api-Version: 2022-11-28` header

**Obsidian Vault Structure**:
```
vault/
├── TODO.md              # Single TODO list with priority sections
├── Ideas/               # Folder for ideas
├── Work/                # Folder for work notes
├── Personal/            # Folder for personal notes
└── Voice Notes/         # Default folder for voice notes
```

**Content Type Classification** (Agent's responsibility):
- **TODO Task** triggers: "нужно", "купить", "сделать", "не забыть"
- **Ideas** triggers: "идея", "можно", "интересно было бы"
- **Work Notes** triggers: work-related keywords, project names
- **Personal Notes**: fallback when unclear

**Error Handling**:
- Voice processing failures return `VoiceNoteResponse(success=False, error=..., details=...)`
- GitHub 404 → `None` (file not found)
- GitHub 409 → Conflict (SHA mismatch or file exists)
- OpenAI API failures logged with `exc_info=True`

## Project Structure Context

**Duplicate Directories**: Both `app/` (root) and `concierge-app/app/` exist. The root `app/` contains the actual implementation. `concierge-app/` appears to be scaffolding/placeholder (empty test files).

**Configuration**:
- `pyproject.toml` - Python 3.11+, FastAPI, OpenAI SDK, httpx, pytest
- `.env.example` - Template for required environment variables
- `spec.md` - Full technical specification (604 lines)
- `LEARNING.md` - Student assignment guide (explains 5 implementation tasks)

**Key Files**:
- `app/main.py` - FastAPI app with `/api/health`, `/api/voice`, `/` endpoints
- `app/config.py` - Settings via pydantic-settings
- `app/models.py` - Pydantic models: `VoiceNoteResponse`, `HealthCheckResponse`

## Implementation Status

All learning tasks from `LEARNING.md` have been completed:
1. ✅ Whisper transcription implemented (`app/services/transcriber.py`)
2. ✅ GitHub vault service methods implemented (`app/services/github_vault.py`)
3. ✅ Effective agent system prompt written (`app/services/agent.py`)
4. ✅ Function tools created (`app/tools/note_tools.py`, `app/tools/todo_tools.py`)
5. ✅ OpenAI Agents SDK integrated (`app/services/agent.py` - `process_transcription()`)

The service is fully functional and ready for use.

## Deployment

- **Platform**: Render.com
- **Environment**: Set `APP_ENV=development` (local) or `APP_ENV=production`
- **Port**: Configured via `PORT` env var (default: 8000)
- **Health Check**: `/api/health` returns service status and GitHub repo info
- **Logging**: Configured via `LOG_LEVEL` (default: INFO)
