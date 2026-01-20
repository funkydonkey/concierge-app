# Google Calendar Setup Guide

This guide explains how to set up Google Calendar integration for the Voice Notes Service.

## Overview

The calendar integration allows the AI agent to automatically create events in your Google Calendar when you mention meetings, calls, or appointments with specific times in your voice notes.

**Example**: "Встреча с клиентом завтра в 15:00 в офисе" → Creates calendar event for tomorrow at 3 PM

## Prerequisites

- Google Cloud Platform account (free tier is sufficient)
- Access to Google Calendar

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Create Project**
3. Enter project name (e.g., "voice-notes-service")
4. Click **Create**

## Step 2: Enable Google Calendar API

1. In your project, go to **APIs & Services** → **Library**
2. Search for "Google Calendar API"
3. Click **Enable**

## Step 3: Create Service Account

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **Service Account**
3. Fill in the details:
   - **Service account name**: voice-notes-calendar
   - **Service account ID**: (auto-generated)
   - **Description**: Service account for voice notes calendar integration
4. Click **CREATE AND CONTINUE**
5. Skip the optional steps (Grant access, User access)
6. Click **DONE**

## Step 4: Create Service Account Key

1. Find your newly created service account in the list
2. Click on the service account email
3. Go to the **KEYS** tab
4. Click **ADD KEY** → **Create new key**
5. Choose **JSON** format
6. Click **CREATE**
7. A JSON file will be downloaded to your computer

**IMPORTANT**: Keep this file secure! It contains credentials for accessing your calendar.

## Step 5: Share Calendar with Service Account

This is crucial - the service account needs access to your calendar:

1. Open [Google Calendar](https://calendar.google.com/)
2. Find the calendar you want to use (usually "Primary")
3. Click the three dots next to it → **Settings and sharing**
4. Scroll to **Share with specific people**
5. Click **+ Add people**
6. Enter the service account email (looks like `voice-notes-calendar@your-project.iam.gserviceaccount.com`)
   - You can find this email in the downloaded JSON file under `client_email`
7. Set permission to **Make changes to events**
8. Click **Send**

## Step 6: Configure Environment Variables

### Option A: Local Development

1. Open the downloaded JSON credentials file
2. Copy the entire JSON content (it should be one line)
3. Edit your `.env` file:

```bash
# Paste the JSON as a single-line string in quotes
GOOGLE_CALENDAR_CREDENTIALS_JSON='{"type":"service_account","project_id":"your-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"voice-notes-calendar@your-project.iam.gserviceaccount.com","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"..."}'

# Optional: Specify calendar ID (default is "primary")
GOOGLE_CALENDAR_ID=primary
```

**Note**: The JSON must be on a single line with escaped quotes. Most text editors can do this automatically.

### Option B: Render.com Deployment

1. Go to your Render.com service dashboard
2. Navigate to **Environment** tab
3. Add environment variable:
   - **Key**: `GOOGLE_CALENDAR_CREDENTIALS_JSON`
   - **Value**: Paste the entire JSON content as a single-line string
4. Add another variable (optional):
   - **Key**: `GOOGLE_CALENDAR_ID`
   - **Value**: `primary` (or your calendar ID)
5. Click **Save Changes**
6. Service will automatically redeploy

## Step 7: Test Integration

1. Restart your service:
```bash
uvicorn app.main:app --reload --port 8000
```

2. Check health endpoint:
```bash
curl http://localhost:8000/api/health
```

You should see:
```json
{
  "status": "healthy",
  "services": {
    "openai": "configured",
    "github": "configured",
    "google_calendar": "enabled"
  },
  ...
}
```

3. Test with a voice note:
   - Record a note saying: "Встреча с командой завтра в 14:00"
   - Upload via iOS Shortcut or test_api.py
   - Check your Google Calendar for the new event!

## Troubleshooting

### Calendar integration shows "disabled"

**Check**:
- `GOOGLE_CALENDAR_CREDENTIALS_JSON` is set in `.env`
- JSON is valid (check for syntax errors)
- Service account email is shared with your calendar

### Events not appearing in calendar

**Check**:
1. Calendar is shared with service account email (Step 5)
2. Permission is set to "Make changes to events"
3. You're checking the correct calendar
4. Check service logs for errors:
```bash
# Logs will show calendar initialization status
```

### "Invalid grant" error

**Possible causes**:
- Service account key is expired or revoked
- System clock is incorrect (service accounts use time-based auth)
- Private key in JSON is corrupted

**Solution**: Create a new service account key (Step 4)

### Wrong timezone

**By default**, events are created in `Europe/Moscow` timezone.

**To change**:
Edit `app/services/google_calendar.py`:
```python
"timeZone": "Europe/Moscow",  # Change to your timezone
```

Common timezones:
- `America/New_York` - US Eastern
- `America/Los_Angeles` - US Pacific
- `Europe/London` - UK
- `Asia/Tokyo` - Japan
- `Australia/Sydney` - Australia

## Security Best Practices

1. **Never commit credentials**: Always use `.env` and `.gitignore`
2. **Rotate keys regularly**: Delete old service account keys
3. **Limit permissions**: Only grant calendar access, not other Google services
4. **Use separate calendars**: Consider creating a dedicated calendar for voice notes
5. **Monitor usage**: Check Google Cloud Console for API usage

## Disabling Calendar Integration

To disable calendar integration:

1. Remove or comment out in `.env`:
```bash
# GOOGLE_CALENDAR_CREDENTIALS_JSON=...
```

2. Restart service

The service will work normally, but calendar events will be saved as TODO tasks instead.

## Advanced Configuration

### Using a Different Calendar

If you don't want to use your primary calendar:

1. Create a new calendar in Google Calendar
2. Share it with the service account (Step 5)
3. Get the calendar ID:
   - Open calendar settings
   - Scroll to "Integrate calendar"
   - Copy the **Calendar ID** (looks like `abc123@group.calendar.google.com`)
4. Set in `.env`:
```bash
GOOGLE_CALENDAR_ID=abc123@group.calendar.google.com
```

### Customizing Event Duration

Events default to 60 minutes. The AI agent can detect duration from context:

- "Встреча на 30 минут" → 30 minute event
- "Звонок на 2 часа" → 2 hour event

Or modify the default in `app/tools/calendar_tools.py`:
```python
duration_minutes: Annotated[int, "Длительность в минутах"] = 60,  # Change default here
```

## Resources

- [Google Calendar API Documentation](https://developers.google.com/calendar/api/guides/overview)
- [Service Account Authentication](https://cloud.google.com/iam/docs/service-accounts)
- [Calendar API Quickstart](https://developers.google.com/calendar/api/quickstart/python)
