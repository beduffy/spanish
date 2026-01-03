"""
Tokenization utilities for German, Spanish, and other languages.
Uses regex-based approach for word segmentation and spaCy for lemmatization.
"""

import re
from typing import List, Dict, Tuple, Optional

# Cache for spaCy models to avoid reloading
_spacy_models = {}


def normalize_token(text: str) -> str:
    """
    Normalize a token for matching/comparison.
    - Lowercase
    - Strip leading/trailing punctuation
    - Keep umlauts/accents as-is (works for German ä, ö, ü, ß)
    """
    # Strip leading/trailing punctuation but keep internal punctuation
    normalized = text.lower().strip()
    # Remove common punctuation from edges (including German quotation marks)
    normalized = re.sub(r'^[.,;:!?()\[\]„""\'…]+', '', normalized)
    normalized = re.sub(r'[.,;:!?()\[\]„""\'…]+$', '', normalized)
    return normalized


def get_spacy_model(language: str):
    """
    Get or load spaCy model for the given language.
    Caches models to avoid reloading.
    
    Args:
        language: Language code ('de' for German, 'es' for Spanish, etc.)
    
    Returns:
        spaCy language model or None if not available
    """
    # Map language codes to spaCy model names
    model_map = {
        'de': 'de_core_news_sm',
        'es': 'es_core_news_sm',
        'en': 'en_core_web_sm',
    }
    
    model_name = model_map.get(language.lower())
    if not model_name:
        return None
    
    # Return cached model if available
    if model_name in _spacy_models:
        return _spacy_models[model_name]
    
    # Try to load the model
    try:
        import spacy
        nlp = spacy.load(model_name, disable=['parser', 'ner'])
        _spacy_models[model_name] = nlp
        return nlp
    except (ImportError, OSError) as e:
        # spaCy not installed or model not downloaded
        print(f"[tokenization] Warning: Could not load spaCy model '{model_name}': {e}")
        print(f"[tokenization] Install with: python -m spacy download {model_name}")
        return None


def lemmatize_token(text: str, language: str = 'de') -> Optional[str]:
    """
    Lemmatize a token using spaCy.
    
    Args:
        text: The token text to lemmatize
        language: Language code ('de', 'es', etc.)
    
    Returns:
        Lemmatized form or None if lemmatization fails
    """
    nlp = get_spacy_model(language)
    if not nlp:
        return None
    
    try:
        # Process the token
        doc = nlp(text)
        if len(doc) > 0:
            token = doc[0]
            lemma = token.lemma_.lower()
            # Return normalized lemma (same normalization as normalize_token)
            return normalize_token(lemma)
    except Exception as e:
        print(f"[tokenization] Error lemmatizing '{text}': {e}")
        return None
    
    return None


def tokenize_text(text: str, language: str = 'de') -> List[Dict[str, any]]:
    """
    Tokenize text (German, Spanish, etc.) into words and punctuation.
    Returns list of dicts: {text, normalized, lemma, start_offset, end_offset, type}
    Works for German (ä, ö, ü, ß) and Spanish (á, é, í, ó, ú, ñ) characters.
    
    Args:
        text: Text to tokenize
        language: Language code ('de' for German, 'es' for Spanish, etc.)
    
    Returns:
        List of token dictionaries with text, normalized, lemma, offsets, and type
    """
    tokens = []
    # Simple regex-based tokenization
    # Matches words (including accented chars) and punctuation separately
    pattern = r'\w+|[^\w\s]'
    
    offset = 0
    for match in re.finditer(pattern, text):
        token_text = match.group(0)
        start = match.start()
        end = match.end()
        
        # Skip pure whitespace matches
        if token_text.strip():
            is_word = bool(re.match(r'\w+', token_text))
            normalized = normalize_token(token_text)
            
            # Lemmatize words only (not punctuation)
            lemma = None
            if is_word:
                lemma = lemmatize_token(token_text, language)
                # If lemmatization fails, lemma remains None (we don't know the base form)
            
            tokens.append({
                'text': token_text,
                'normalized': normalized,
                'lemma': lemma,
                'start_offset': start,
                'end_offset': end,
                'type': 'word' if is_word else 'punctuation'
            })
    
    return tokens
