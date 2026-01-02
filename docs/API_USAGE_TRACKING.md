# API Usage Tracking Guide

## Overview

This guide explains how to monitor your usage of DeepL Translation API and Google Cloud Text-to-Speech API to stay within free tier limits.

---

## DeepL Translation API

### Free Tier Limits
- **500,000 characters per month**
- Resets on the 1st of each month
- No credit card required for free tier

### How to Check Usage

#### Method 1: DeepL API Dashboard (Recommended)
1. Go to: https://www.deepl.com/pro-api
2. Log in to your DeepL account
3. Navigate to **"Usage"** or **"API Usage"** section
4. You'll see:
   - Characters used this month
   - Characters remaining
   - Usage breakdown by day/week

#### Method 2: API Usage Endpoint
DeepL doesn't provide a direct API endpoint to check usage, but you can:
1. Check your account dashboard (link above)
2. Monitor your application logs for translation calls
3. Track usage manually in your database

#### Method 3: Application-Level Tracking
Add usage tracking to your Django app:

```python
# In translation_service.py
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

def translate_text(text, source_lang='de', target_lang='en'):
    # ... existing code ...
    
    # Track usage (approximate)
    char_count = len(text)
    cache_key = 'deepl_usage_this_month'
    current_usage = cache.get(cache_key, 0)
    cache.set(cache_key, current_usage + char_count, timeout=60*60*24*31)  # 31 days
    
    logger.info(f"DeepL translation: {char_count} chars (total this month: ~{current_usage + char_count})")
    
    return translation
```

### Monitoring Tips
- **Average lesson**: ~500-2000 characters of text
- **Token translations**: ~5-20 characters each
- **Sentence translations**: ~50-200 characters each
- **Estimated**: ~250-500 lessons per month before hitting limit

### What Happens When Limit Reached?
- API returns error: `"Quota exceeded"`
- Translation service returns `None`
- User sees error message: "Translation failed"
- **Solution**: Wait until next month or upgrade to paid plan ($6.99/month for 1M chars)

---

## Google Cloud Text-to-Speech API

### Free Tier Limits
- **4 million characters per month** (Standard voices)
- **1 million characters per month** (WaveNet/Neural voices)
- Resets monthly
- Requires Google Cloud account (free tier includes $300 credit)

### How to Check Usage

#### Method 1: Google Cloud Console (Recommended)
1. Go to: https://console.cloud.google.com/
2. Select your project (the one matching your credentials file)
3. Navigate to **"APIs & Services"** > **"Dashboard"**
4. Find **"Cloud Text-to-Speech API"**
5. Click on it to see:
   - Requests per day/week/month
   - Characters processed
   - Errors and quotas

#### Method 2: Billing Dashboard
1. Go to: https://console.cloud.google.com/billing
2. Select your billing account
3. View **"Cost breakdown"** and **"Usage"**
4. Filter by **"Cloud Text-to-Speech API"**

#### Method 3: API Quotas Page
1. Go to: https://console.cloud.google.com/apis/api/texttospeech.googleapis.com/quotas
2. View:
   - Characters per day/month
   - Requests per minute/day
   - Current usage vs. limits

#### Method 4: Application-Level Tracking
Add usage tracking to your Django app:

```python
# In tts_service.py
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

def generate_tts_audio(text, language_code='de-DE'):
    # ... existing code ...
    
    # Track usage (approximate)
    char_count = len(text)
    cache_key = 'google_tts_usage_this_month'
    current_usage = cache.get(cache_key, 0)
    cache.set(cache_key, current_usage + char_count, timeout=60*60*24*31)  # 31 days
    
    logger.info(f"Google TTS: {char_count} chars (total this month: ~{current_usage + char_count})")
    
    return audio_url
```

### Monitoring Tips
- **Average lesson**: ~500-2000 characters
- **Audio generation**: ~1-4 minutes of audio per lesson
- **Estimated**: ~2000-8000 lessons per month before hitting Standard limit
- **Estimated**: ~500-2000 lessons per month before hitting WaveNet limit

### What Happens When Limit Reached?
- API returns error: `"Quota exceeded"` or `"RESOURCE_EXHAUSTED"`
- TTS service falls back to ElevenLabs (if configured)
- If no fallback: Returns `None`, user sees error message
- **Solution**: 
  - Wait until next month
  - Upgrade to paid plan (pay-as-you-go pricing)
  - Use ElevenLabs as fallback

---

## ElevenLabs (Fallback TTS)

### Free Tier Limits
- **10,000 characters per month** (very limited)
- **$11/month**: ~200 minutes (~200,000 characters)
- **$99/month**: ~1000 minutes (~1,000,000 characters)

### How to Check Usage
1. Go to: https://elevenlabs.io/app/usage
2. Log in to your account
3. View:
   - Characters used this month
   - Remaining quota
   - Usage history

### Monitoring Tips
- ElevenLabs is used as fallback when Google TTS fails
- Check usage if you see many fallback calls in logs
- Consider upgrading if hitting limits frequently

---

## Quick Usage Check Script

Create a script to check approximate usage:

```python
# check_api_usage.py
from django.core.cache import cache
import os

# DeepL usage (approximate)
deepl_usage = cache.get('deepl_usage_this_month', 0)
deepl_limit = 500_000
deepl_percent = (deepl_usage / deepl_limit) * 100

print(f"DeepL Usage: ~{deepl_usage:,} / {deepl_limit:,} chars ({deepl_percent:.1f}%)")

# Google TTS usage (approximate)
google_tts_usage = cache.get('google_tts_usage_this_month', 0)
google_tts_limit = 4_000_000  # Standard voices
google_tts_percent = (google_tts_usage / google_tts_limit) * 100

print(f"Google TTS Usage: ~{google_tts_usage:,} / {google_tts_limit:,} chars ({google_tts_percent:.1f}%)")
```

Run it:
```bash
docker-compose exec backend python manage.py shell < check_api_usage.py
```

---

## Best Practices

1. **Cache Aggressively**: Both services cache translations/TTS by text hash
2. **Monitor Regularly**: Check usage weekly to avoid surprises
3. **Set Up Alerts**: Configure billing alerts in Google Cloud Console
4. **Use Fallbacks**: ElevenLabs fallback prevents complete failure
5. **Optimize Text**: Don't generate TTS for very short lessons
6. **Batch Translations**: Cache sentence translations to reduce API calls

---

## Troubleshooting

### "Quota Exceeded" Errors
1. Check usage in respective dashboards
2. Verify you're on free tier (not accidentally using paid features)
3. Wait until next month for reset
4. Consider upgrading or using alternative service

### Unexpected High Usage
1. Check for duplicate API calls in logs
2. Verify caching is working correctly
3. Review lesson sizes (very long lessons use more characters)
4. Check for retry loops causing multiple calls

---

## References

- **DeepL API**: https://www.deepl.com/pro-api
- **Google Cloud TTS**: https://cloud.google.com/text-to-speech/pricing
- **ElevenLabs**: https://elevenlabs.io/pricing
