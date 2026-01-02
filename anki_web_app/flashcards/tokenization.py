"""
Tokenization utilities for German, Spanish, and other languages.
Uses regex-based approach for word segmentation.
"""

import re
from typing import List, Dict, Tuple


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


def tokenize_text(text: str) -> List[Dict[str, any]]:
    """
    Tokenize text (German, Spanish, etc.) into words and punctuation.
    Returns list of dicts: {text, normalized, start_offset, end_offset, type}
    Works for German (ä, ö, ü, ß) and Spanish (á, é, í, ó, ú, ñ) characters.
    """
    tokens = []
    # Simple regex-based tokenization (can be improved with spaCy later)
    # Matches words (including accented chars) and punctuation separately
    pattern = r'\w+|[^\w\s]'
    
    offset = 0
    for match in re.finditer(pattern, text):
        token_text = match.group(0)
        start = match.start()
        end = match.end()
        
        # Skip pure whitespace matches
        if token_text.strip():
            tokens.append({
                'text': token_text,
                'normalized': normalize_token(token_text),
                'start_offset': start,
                'end_offset': end,
                'type': 'word' if re.match(r'\w+', token_text) else 'punctuation'
            })
    
    return tokens
