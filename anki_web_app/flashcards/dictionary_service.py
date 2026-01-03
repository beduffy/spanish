"""
Dictionary service using Wiktionary API (free, no API key required).
Fetches word definitions, meanings, part of speech, and example sentences.
"""

import requests
from django.core.cache import cache
from typing import Optional, Dict, List
import re


def get_wiktionary_language_code(language: str) -> str:
    """
    Convert language code to Wiktionary language code.
    """
    lang_map = {
        'es': 'Spanish',
        'de': 'German',
        'en': 'English',
        'fr': 'French',
        'it': 'Italian',
        'pt': 'Portuguese',
    }
    return lang_map.get(language.lower(), language.capitalize())


def get_dictionary_entry(word: str, source_lang: str = 'de', target_lang: str = 'en') -> Optional[Dict]:
    """
    Get dictionary entry from Wiktionary API.
    Returns dictionary data with meanings, part of speech, and example sentences.
    
    Structure:
    {
        'meanings': [
            {
                'part_of_speech': 'noun',
                'definitions': ['definition1', 'definition2'],
                'examples': ['example1', 'example2']
            }
        ],
        'pronunciation': '...',
        'etymology': '...'
    }
    """
    if not word or len(word.strip()) == 0:
        return None
    
    # Normalize word (lowercase, strip punctuation)
    normalized_word = word.lower().strip()
    # Remove leading/trailing punctuation
    normalized_word = re.sub(r'^[.,;:!?()\[\]„""\'…]+', '', normalized_word)
    normalized_word = re.sub(r'[.,;:!?()\[\]„""\'…]+$', '', normalized_word)
    
    if not normalized_word:
        return None
    
    # Check cache first
    cache_key = f"dictionary:{source_lang}:{normalized_word}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    try:
        # Wiktionary API endpoint
        # Format: https://en.wiktionary.org/api/rest_v1/page/definition/{word}
        # For language-specific: https://{lang}.wiktionary.org/api/rest_v1/page/definition/{word}
        
        # URL encode the word to handle special characters
        from urllib.parse import quote
        encoded_word = quote(normalized_word)
        url = f"https://en.wiktionary.org/api/rest_v1/page/definition/{encoded_word}"
        
        # Wiktionary API requires User-Agent header to avoid 403 errors
        headers = {
            'User-Agent': 'SpanishAnkiApp/1.0 (Language Learning App; https://github.com/yourusername/spanish-anki)'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            # Word not found in Wiktionary
            return None
        
        response.raise_for_status()
        data = response.json()
        
        # Parse Wiktionary response
        dictionary_entry = _parse_wiktionary_response(data, source_lang, target_lang)
        
        if dictionary_entry:
            # Cache for 30 days
            cache.set(cache_key, dictionary_entry, 60 * 60 * 24 * 30)
            return dictionary_entry
            
    except requests.exceptions.RequestException as e:
        print(f"Dictionary API error for '{word}': {e}")
        return None
    except Exception as e:
        print(f"Dictionary parsing error for '{word}': {e}")
        return None
    
    return None


def _parse_wiktionary_response(data: Dict, source_lang: str, target_lang: str) -> Optional[Dict]:
    """
    Parse Wiktionary API response into our dictionary entry format.
    
    Wiktionary API returns: { "en": { "definitions": [...] }, "es": {...}, ... }
    We need to find the entry for the source language.
    """
    if not data or not isinstance(data, dict):
        return None
    
    # Map language codes to Wiktionary language codes
    lang_code_map = {
        'es': 'es',  # Spanish
        'de': 'de',  # German
        'en': 'en',  # English
        'fr': 'fr',  # French
        'it': 'it',  # Italian
        'pt': 'pt',  # Portuguese
    }
    
    # Get language code for Wiktionary API
    wiktionary_lang_code = lang_code_map.get(source_lang.lower(), source_lang.lower())
    
    # Find the language entry in the response
    lang_data = data.get(wiktionary_lang_code)
    if not lang_data or not isinstance(lang_data, dict):
        return None
    
    definitions_list = lang_data.get('definitions', [])
    if not definitions_list:
        return None
    
    meanings = []
    
    # Parse definitions
    for entry in definitions_list:
        if not isinstance(entry, dict):
            continue
            
        part_of_speech = entry.get('partOfSpeech', '').lower()
        definitions = []
        examples = []
        
        # Extract definitions from senses
        senses = entry.get('senses', [])
        for sense in senses:
            # Get glosses (definitions)
            glosses = sense.get('glosses', [])
            for gloss in glosses:
                if isinstance(gloss, str) and gloss.strip():
                    definitions.append(gloss.strip())
            
            # Get examples
            example_objs = sense.get('examples', [])
            for example_obj in example_objs:
                if isinstance(example_obj, dict):
                    example_text = example_obj.get('text', '')
                    if example_text and example_text.strip():
                        examples.append(example_text.strip())
        
        if definitions:
            meanings.append({
                'part_of_speech': part_of_speech,
                'definitions': definitions[:10],  # Limit to 10 definitions per meaning
                'examples': examples[:3]  # Limit to 3 examples
            })
    
    if not meanings:
        return None
    
    # Get pronunciation if available
    pronunciation = None
    pronunciations_data = lang_data.get('pronunciations', [])
    if isinstance(pronunciations_data, list) and len(pronunciations_data) > 0:
        # Get first pronunciation entry
        pron_entry = pronunciations_data[0]
        if isinstance(pron_entry, dict):
            audio_files = pron_entry.get('audio', [])
            if audio_files and len(audio_files) > 0:
                audio = audio_files[0]
                if isinstance(audio, dict):
                    pronunciation = audio.get('url', '')
                elif isinstance(audio, str):
                    pronunciation = audio
    
    return {
        'meanings': meanings,
        'pronunciation': pronunciation,
        'source': 'wiktionary'
    }


def get_dictionary_entry_simple(word: str, source_lang: str = 'de', target_lang: str = 'en') -> Optional[Dict]:
    """
    Simplified version that returns a basic dictionary entry.
    Falls back to translation if dictionary lookup fails.
    """
    dictionary_entry = get_dictionary_entry(word, source_lang, target_lang)
    
    if dictionary_entry:
        return dictionary_entry
    
    # Fallback: return None (caller can use translation service as fallback)
    return None
