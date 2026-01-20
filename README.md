# Voice Notes Service

AI-powered voice notes processing with automatic transcription and Obsidian integration.

**Status**: ✅ Fully implemented and ready for deployment

## Features

- 🎤 **Voice Transcription** - OpenAI Whisper API (Russian language)
- 🤖 **AI Agent** - Smart content classification and action execution
- 📝 **Automatic Note Creation** - Markdown notes with YAML frontmatter
- ✅ **TODO Management** - Priority-based task organization
- 📅 **Google Calendar Integration** - Automatic event creation from voice notes
- 🔄 **GitHub Integration** - Obsidian vault sync via GitHub API
- 📱 **iOS Shortcuts** - Record and process on-the-go

## Quick Start

### 1. Setup

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Configuration

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your keys:
# - OPENAI_API_KEY                      (from OpenAI platform)
# - GITHUB_TOKEN                        (personal access token with 'repo' scope)
# - GITHUB_REPO_OWNER                   (your GitHub username)
# - GITHUB_REPO_NAME                    (your Obsidian vault repository)
# - GOOGLE_CALENDAR_CREDENTIALS_JSON    (optional - for calendar integration)
```

### 3. Run

```bash
# Development server
uvicorn app.main:app --reload --port 8000

# Access at: http://localhost:8000
```

### 4. Test

```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Test with audio file
python test_api.py test.m4a
```

## Architecture

- **FastAPI** backend for REST API
- **OpenAI Whisper** for audio transcription
- **OpenAI Agents SDK** for AI-powered content analysis
- **Google Calendar API** for event creation (optional)
- **GitHub API** for Obsidian vault integration

## Endpoints

- `GET /` - Service info
- `GET /api/health` - Health check
- `POST /api/voice` - Process voice note (multipart/form-data with audio file)

## Development

```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/

# Format code
black app/ tests/

# Lint
ruff check app/ tests/
```

## Project Structure

```
voice-notes-service/
├── app/
│   ├── main.py           # FastAPI app
│   ├── config.py         # Configuration
│   ├── models.py         # Pydantic models
│   ├── services/         # Business logic
│   │   ├── transcriber.py
│   │   ├── agent.py
│   │   └── github_vault.py
│   └── tools/            # AI agent tools
│       ├── note_tools.py
│       └── todo_tools.py
├── tests/
├── pyproject.toml
└── .env.example
```

## How It Works

1. **Record** voice note on iPhone (via iOS Shortcuts)
2. **Upload** to service endpoint `/api/voice`
3. **Transcribe** audio with OpenAI Whisper
4. **Analyze** content with AI agent (GPT-4o-mini)
5. **Execute** actions:
   - Create notes in Ideas/Work/Personal/Voice Notes folders
   - Add tasks to TODO.md with priorities
   - Append to existing notes
6. **Sync** to Obsidian via GitHub repository
7. **Access** notes in Obsidian (auto-pulls every 1-5 min)

## AI Agent Capabilities

The agent automatically classifies content and takes action:

- **Calendar Events** → `create_calendar_event()` when specific time mentioned
- **TODO Tasks** → `add_todo_task()` with priority detection
- **Ideas** → `create_note(folder="Ideas")` with Markdown formatting
- **Work Notes** → `create_note(folder="Work")` with action items
- **Personal Notes** → `create_note(folder="Personal")`
- **Mixed Content** → Multiple actions in sequence

Examples:
- "Встреча с клиентом завтра в 15:00" → Creates calendar event
- "Нужно купить молоко" → Adds TODO task
- "Идея для приложения..." → Creates note in Ideas folder

Triggered by keywords: "встреча", "звонок", "нужно", "идея", "купить", "не забыть", etc.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

**Quick Deploy to Render.com:**
1. Push to GitHub
2. Connect to Render
3. Use `render.yaml` blueprint
4. Set environment variables
5. Deploy!

## Documentation

- `spec.md` - Full technical specification
- `LEARNING.md` - Implementation tasks (all completed ✅)
- `DEPLOYMENT.md` - Deployment guide for Render.com
- `GOOGLE_CALENDAR_SETUP.md` - 📅 Google Calendar integration setup guide
- `IOS_SHORTCUTS_GUIDE.md` - 📱 Пошаговая инструкция по созданию iOS шортката
- `CLAUDE.md` - Claude Code reference
