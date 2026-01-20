# Deployment Guide

## Prerequisites

1. **GitHub Repository** - Create a private repository for your Obsidian vault
2. **GitHub Personal Access Token** - With `repo` permissions
3. **OpenAI API Key** - From OpenAI platform
4. **Render.com Account** - Free tier works

## Step 1: Prepare Obsidian Vault Repository

1. Create a private GitHub repository (e.g., `obsidian-vault`)
2. Initialize with the following structure:

```
obsidian-vault/
├── TODO.md              # Will be auto-created
├── Ideas/               # Create empty folder
├── Work/                # Create empty folder
├── Personal/            # Create empty folder
└── Voice Notes/         # Create empty folder
```

3. Install Obsidian Git plugin in your local Obsidian:
   - Settings → Community plugins → Browse → "Obsidian Git"
   - Configure auto-pull every 1-5 minutes

## Step 2: Get API Keys

### GitHub Token
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope (full control of private repositories)
3. Save the token securely

### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Save the key securely

## Step 3: Deploy to Render.com

### Option A: Using render.yaml (Recommended)

1. Push this repository to GitHub
2. Go to Render.com → New → Blueprint
3. Connect your GitHub repository
4. Render will detect `render.yaml` and auto-configure
5. Set environment variables:
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `GITHUB_TOKEN` - Your GitHub personal access token
   - `GITHUB_REPO_OWNER` - Your GitHub username
   - `GITHUB_REPO_NAME` - Your vault repository name (e.g., `obsidian-vault`)
6. Click "Apply" to deploy

### Option B: Manual Setup

1. Go to Render.com → New → Web Service
2. Connect your GitHub repository
3. Configure:
   - **Name**: `voice-notes-service`
   - **Region**: Oregon (or closest to you)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -e .`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables (see above)
5. Set health check path: `/api/health`
6. Deploy

## Step 4: Configure iOS Shortcuts

> **📱 Подробная инструкция:** См. [IOS_SHORTCUTS_GUIDE.md](IOS_SHORTCUTS_GUIDE.md) для детального руководства с примерами и устранением проблем.

### Creating the Shortcut

1. **Open Shortcuts app** on iPhone

2. **Tap "+" (New Shortcut)** in top right corner

3. **Add Action 1 - Record Audio**:
   - Search for and add "Record Audio"
   - Configure: Tap "Until You Tap Stop" or set a time limit
   - This records the voice note

4. **Add Action 2 - Get Contents of URL**:
   - Search for and add "Get Contents of URL"
   - Tap "URL" field and enter: `https://your-app.onrender.com/api/voice`
   - Tap "Show More" to expand options
   - Set **Method**: `POST`
   - Set **Request Body**: `Form`
   - Tap "Add new field":
     - Key: `audio`
     - Value: Tap and select "Recorded Audio" (from previous action)
     - Type will automatically be set to file

5. **Add Action 3 - Get Dictionary Value** (Optional but recommended):
   - Search for and add "Get Dictionary Value"
   - Set key: `transcription`
   - This extracts the transcription text from the response

6. **Add Action 4 - Show Notification**:
   - Search for and add "Show Notification"
   - Set text to "Dictionary Value" from previous step
   - This shows you the transcribed text

7. **Name your shortcut**: Tap "Done" and name it (e.g., "Voice to Obsidian")

8. **Add to Home Screen** (Optional):
   - Tap the shortcut → Tap "..." menu
   - Tap "Add to Home Screen"
   - Choose icon and name
   - Tap "Add"

### Alternative: Simpler Version (No Notification)

If you just want to send the audio without seeing the result:
1. Record Audio
2. Get Contents of URL (configured as above)
3. Done!

The notes will appear in your Obsidian vault automatically.

### Testing

1. Run the shortcut
2. Record a test message (e.g., "Нужно купить молоко")
3. Wait for processing (5-10 seconds)
4. Check notification (if configured)
5. Wait 1-5 minutes for Obsidian Git to sync
6. Check your vault for the new TODO/note

### Troubleshooting Shortcuts

**"Network Error"**:
- Check URL is correct (https://your-app.onrender.com/api/voice)
- Verify your Render app is running
- Check health endpoint in browser first

**"No Response"**:
- Recording might be too long (Render free tier has timeout)
- Check Render logs for errors

**"Invalid Response"**:
- Check response in Shortcuts debugger (tap play icon)
- Look at "Contents of URL" output
- Verify error message in response

## Step 5: Verify Setup

### Test Health Endpoint
```bash
curl https://your-app.onrender.com/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "openai": "configured",
    "github": "configured"
  },
  "vault": {
    "repo": "username/obsidian-vault",
    "branch": "main"
  }
}
```

### Test Voice Endpoint
```bash
curl -X POST \
  -F "audio=@test.m4a" \
  https://your-app.onrender.com/api/voice
```

Expected response:
```json
{
  "success": true,
  "transcription": "Нужно купить молоко",
  "actions": [
    {
      "function": "add_todo_task",
      "arguments": {...},
      "result": "Задача 'Купить молоко' добавлена в TODO"
    }
  ],
  "agent_summary": "Добавил задачу в TODO список"
}
```

## Troubleshooting

### Service won't start
- Check logs in Render dashboard
- Verify all environment variables are set
- Ensure GitHub token has `repo` permissions

### Transcription fails
- Check OPENAI_API_KEY is valid
- Verify audio file format (m4a, mp3, wav, webm)
- Check Render logs for error details

### GitHub operations fail
- Verify GITHUB_TOKEN has `repo` scope
- Check repository exists and is accessible
- Verify folder structure in vault repository

### Notes not appearing in Obsidian
- Check Obsidian Git plugin is installed
- Verify auto-pull is enabled (1-5 min interval)
- Manually pull in Obsidian to test

## Cost Estimates

- **Render.com**: Free tier (750 hours/month) or $7/month for always-on
- **OpenAI Whisper**: ~$0.006/minute of audio
- **OpenAI GPT-4o-mini**: ~$0.15/1M input tokens, ~$0.60/1M output tokens
- **GitHub**: Free for private repositories

**Typical usage**: 10 voice notes/day × 1 min each = ~$2-3/month total

## Security Notes

- Never commit `.env` file to Git
- Use environment variables for all secrets
- GitHub repository should be private
- Rotate tokens periodically
- Monitor Render logs for suspicious activity

## Monitoring

### View Logs
```bash
# In Render dashboard → Logs tab
# Or via CLI
render logs -f
```

### Key Metrics to Watch
- Response time (should be < 10s for 1 min audio)
- Error rate (should be < 1%)
- GitHub API rate limit (5000/hour)
- OpenAI API usage

## Updating

1. Push changes to GitHub repository
2. Render auto-deploys from main branch
3. Monitor deployment logs
4. Test `/api/health` endpoint after deploy

## Backup

Your notes are automatically backed up in:
1. GitHub repository (vault)
2. Local Obsidian folder
3. Render logs (transcriptions for 7 days)
