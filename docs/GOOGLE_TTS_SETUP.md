# Google Cloud TTS Setup Guide

This guide will help you set up Google Cloud Text-to-Speech for the reader feature.

## Prerequisites

- A Google Cloud account
- A Google Cloud project (or create a new one)

## Step 1: Enable the Text-to-Speech API

**IMPORTANT**: This step is required before TTS will work!

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one)
3. Navigate to **APIs & Services** > **Library**
4. Search for "Cloud Text-to-Speech API"
5. Click on it and press **Enable**
6. **Wait a few minutes** for the API to be fully enabled (Google says it can take a few minutes to propagate)

**Quick Link**: If you see an error with a project ID, you can enable it directly:
- Replace `YOUR_PROJECT_ID` with your actual project ID: `https://console.developers.google.com/apis/api/texttospeech.googleapis.com/overview?project=YOUR_PROJECT_ID`

## Step 2: Create a Service Account

1. In Google Cloud Console, go to **IAM & Admin** > **Service Accounts**
2. Click **Create Service Account**
3. Fill in:
   - **Service account name**: `tts-service` (or any name you prefer)
   - **Service account ID**: auto-generated
   - **Description**: "Service account for Text-to-Speech API"
4. Click **Create and Continue**
5. **Grant this service account access to project**:
   - Role: Select **Cloud Text-to-Speech API User** (or **Cloud Text-to-Speech API Client**)
6. Click **Continue**, then **Done**

## Step 3: Create and Download JSON Key

1. In the Service Accounts list, click on the service account you just created
2. Go to the **Keys** tab
3. Click **Add Key** > **Create new key**
4. Select **JSON** format
5. Click **Create** - this will download a JSON file to your computer
6. **Important**: Keep this file secure! It contains credentials that allow access to your Google Cloud project.

## Step 4: Install the Python Library

The `google-cloud-texttospeech` library needs to be added to your requirements.txt:

```bash
# Already added to requirements.txt, but if you need to install manually:
pip install google-cloud-texttospeech
```

## Step 5: Configure the Credentials Path

You have two options for providing the credentials:

### Option A: Mount the JSON file in Docker (Recommended for Development)

1. Place your downloaded JSON file in a secure location on your host machine
   - Example: `/home/ben/.google-cloud/tts-credentials.json`
   - Or in your project: `/home/ben/all_projects/spanish/credentials/google-tts.json`

2. Update `docker-compose.yml` to mount the file and set the environment variable:

```yaml
services:
  backend:
    volumes:
      - ./anki_web_app:/app
      - ./data:/app/data
      - /home/ben/.google-cloud/tts-credentials.json:/app/google-tts-credentials.json:ro  # Add this line
    environment:
      - GOOGLE_TTS_CREDENTIALS_PATH=/app/google-tts-credentials.json  # Path inside container
```

3. Restart the backend container:
```bash
docker-compose restart backend
```

### Option B: Use Environment Variable with Absolute Path (Production)

1. Place your JSON file on the server in a secure location
2. Set the environment variable to the absolute path:

```bash
export GOOGLE_TTS_CREDENTIALS_PATH=/path/to/your/google-tts-credentials.json
```

Or in `docker-compose.yml`:
```yaml
environment:
  - GOOGLE_TTS_CREDENTIALS_PATH=/app/google-tts-credentials.json
```

## Step 6: Verify the Setup

1. Make sure your backend container has access to the file:
```bash
docker-compose exec backend ls -la /app/google-tts-credentials.json
```

2. Test TTS generation by importing a lesson with TTS enabled in the UI

3. Check backend logs for any errors:
```bash
docker-compose logs backend | grep -i tts
```

## Troubleshooting

### Error: "google-cloud-texttospeech not installed"
- Make sure `google-cloud-texttospeech` is in `requirements.txt`
- Rebuild the Docker container: `docker-compose up --build -d backend`

### Error: "File not found" or "Permission denied"
- Check that the file path is correct
- Ensure the file is readable: `chmod 644 /path/to/credentials.json`
- Verify the volume mount in docker-compose.yml

### Error: "Permission denied" or "Authentication failed"
- Verify the service account has the correct role (Cloud Text-to-Speech API User)
- **Check that the Text-to-Speech API is enabled in your Google Cloud project** (most common issue!)
- Ensure the JSON key file is valid and not corrupted
- Wait a few minutes after enabling the API for it to propagate

### Error: "SERVICE_DISABLED" or "API has not been used in project"
- **The Text-to-Speech API is not enabled** - go to Google Cloud Console and enable it
- Wait 2-5 minutes after enabling for the change to propagate
- Check the error message for the direct activation URL

### Error: "Quota exceeded"
- Google Cloud TTS has free tier limits:
  - **Standard voices**: 4M characters/month free
  - **WaveNet voices**: 1M characters/month free
- Check your usage in Google Cloud Console > APIs & Services > Dashboard

## Free Tier Limits

Google Cloud Text-to-Speech free tier includes:
- **Standard voices**: 4 million characters per month
- **WaveNet voices**: 1 million characters per month
- After free tier: ~$4 per 1 million characters for Standard, ~$16 per 1 million for WaveNet

**Note**: The current implementation uses Standard voices by default. To use WaveNet (higher quality), you would need to modify `tts_service.py` to specify a WaveNet voice.

## Alternative: Using ElevenLabs

If you prefer not to use Google Cloud TTS, you can use ElevenLabs instead:

1. Sign up at [ElevenLabs](https://elevenlabs.io/)
2. Get your API key from the dashboard
3. Set the environment variable:
```bash
export ELEVENLABS_API_KEY=your_api_key_here
```

The system will automatically fall back to ElevenLabs if Google TTS is not configured.

## Security Best Practices

1. **Never commit credentials to git** - Add `*.json` credentials files to `.gitignore`
2. **Use read-only mounts** - Add `:ro` flag when mounting credentials in Docker
3. **Restrict file permissions** - Use `chmod 600` for credentials files
4. **Rotate keys regularly** - Create new service account keys periodically
5. **Use least privilege** - Only grant the minimum required permissions

## Next Steps

Once configured, you can:
1. Import a lesson via `/reader/import`
2. Check "Generate TTS Audio" when importing
3. The audio will be generated and available for playback in the reader view
