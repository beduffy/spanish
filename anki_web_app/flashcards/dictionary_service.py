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
    
    Wiktionary API returns: { "de": [...], "en": [...], ... }
    Each language entry is an array of definition objects.
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
    
    # Find the language entry in the response (it's an array, not a dict!)
    lang_data = data.get(wiktionary_lang_code)
    if not lang_data:
        return None
    
    # Wiktionary API returns language data as an array of definition objects
    if not isinstance(lang_data, list) or len(lang_data) == 0:
        return None
    
    meanings = []
    
    # Parse each definition entry
    for entry in lang_data:
        if not isinstance(entry, dict):
            continue
        
        part_of_speech = entry.get('partOfSpeech', '').lower()
        definitions = []
        examples = []
        
        # Extract definitions - Wiktionary API has two possible structures:
        # 1. Direct 'definitions' array with 'definition' field (HTML)
        # 2. 'senses' array with 'glosses' array
        
        # Try structure 1: direct definitions array
        defs_list = entry.get('definitions', [])
        if defs_list:
            for def_item in defs_list:
                if isinstance(def_item, dict):
                    # Extract text from HTML definition
                    def_text = def_item.get('definition', '')
                    if def_text:
                        # Strip HTML tags using regex (simple approach)
                        clean_text = re.sub(r'<[^>]+>', '', def_text)
                        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                        if clean_text:
                            definitions.append(clean_text)
        
        # Try structure 2: senses with glosses
        if not definitions:
            senses = entry.get('senses', [])
            for sense in senses:
                if isinstance(sense, dict):
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
                        elif isinstance(example_obj, str):
                            if example_obj.strip():
                                examples.append(example_obj.strip())
        
        # Extract examples from entry level if not found in senses
        if not examples:
            entry_examples = entry.get('examples', [])
            for ex in entry_examples:
                if isinstance(ex, dict):
                    ex_text = ex.get('text', '')
                    if ex_text and ex_text.strip():
                        examples.append(ex_text.strip())
                elif isinstance(ex, str):
                    if ex.strip():
                        examples.append(ex.strip())
        
        if definitions:
            meanings.append({
                'part_of_speech': part_of_speech,
                'definitions': definitions[:10],  # Limit to 10 definitions per meaning
                'examples': examples[:3]  # Limit to 3 examples
            })
    
    if not meanings:
        return None
    
    # Get pronunciation if available (check first entry)
    pronunciation = None
    if len(lang_data) > 0:
        first_entry = lang_data[0]
        if isinstance(first_entry, dict):
            pronunciations_data = first_entry.get('pronunciations', [])
            if isinstance(pronunciations_data, list) and len(pronunciations_data) > 0:
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
