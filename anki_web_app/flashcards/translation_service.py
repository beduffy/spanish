"""
Translation service using DeepL API (free tier: 500k chars/month).
Caches translations to avoid redundant API calls.
"""

import os
import requests
from django.core.cache import cache
from typing import Optional, Dict
from decouple import config


DEEPL_API_KEY = config('DEEPL_API_KEY', default='')
DEEPL_API_URL = 'https://api-free.deepl.com/v2/translate' if not DEEPL_API_KEY.startswith('paid') else 'https://api.deepl.com/v2/translate'


def translate_text(text: str, source_lang: str = 'de', target_lang: str = 'en') -> Optional[str]:
    """
    Translate text using DeepL API.
    Caches results in Django cache.
    """
    if not DEEPL_API_KEY:
        return None
    
    # Check cache first
    cache_key = f"translation:{source_lang}:{target_lang}:{text}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    try:
        response = requests.post(
            DEEPL_API_URL,
            data={
                'auth_key': DEEPL_API_KEY,
                'text': text,
                'source_lang': source_lang.upper(),
                'target_lang': target_lang.upper(),
            },
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get('translations'):
            translation = result['translations'][0]['text']
            # Cache for 30 days
            cache.set(cache_key, translation, 60 * 60 * 24 * 30)
            return translation
    except Exception as e:
        print(f"Translation error: {e}")
        return None
    
    return None


def get_word_translation(word: str, source_lang: str = 'de', target_lang: str = 'en') -> Optional[Dict]:
    """
    Get dictionary-style translation for a single word.
    For MVP, just translate the word. Later can integrate with dictionary API.
    """
    translation = translate_text(word, source_lang, target_lang)
    if translation:
        return {
            'word': word,
            'translation': translation,
            'meanings': [translation],  # Simplified for MVP
        }
    return None
