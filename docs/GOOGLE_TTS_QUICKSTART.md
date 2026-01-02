# Google TTS Quick Setup

## Quick Steps

1. **Get Google Cloud Credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable "Cloud Text-to-Speech API"
   - Create a Service Account with "Cloud Text-to-Speech API User" role
   - Download JSON key file

2. **Place credentials file**:
   ```bash
   # Create a secure directory
   mkdir -p ~/.google-cloud
   # Move your downloaded JSON file there
   mv ~/Downloads/your-project-*.json ~/.google-cloud/google-tts-credentials.json
   ```

3. **Update docker-compose.yml**:
   Uncomment and update this line in the `backend` service `volumes` section:
   ```yaml
   - ~/.google-cloud/google-tts-credentials.json:/app/google-tts-credentials.json:ro
   ```

4. **Set environment variable**:
   The environment variable is already configured in docker-compose.yml. Just make sure the path matches:
   ```yaml
   - GOOGLE_TTS_CREDENTIALS_PATH=/app/google-tts-credentials.json
   ```

5. **Rebuild backend** (to install google-cloud-texttospeech):
   ```bash
   docker-compose up --build -d backend
   ```

6. **Test**:
   - Import a lesson at `/reader/import`
   - Check "Generate TTS Audio"
   - Audio should be generated and playable

## Alternative: Use ElevenLabs Instead

If you prefer ElevenLabs (easier setup, no file mounting needed):

1. Sign up at [ElevenLabs](https://elevenlabs.io/)
2. Get your API key
3. Set environment variable:
   ```bash
   export ELEVENLABS_API_KEY=your_key_here
   ```
   Or add to docker-compose.yml:
   ```yaml
   - ELEVENLABS_API_KEY=your_key_here
   ```

The system will automatically use ElevenLabs if Google TTS is not configured.
