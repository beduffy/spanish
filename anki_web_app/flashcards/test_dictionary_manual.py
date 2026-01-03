#!/usr/bin/env python3
"""
Manual test script for dictionary feature.
Run this to test dictionary lookup without needing bearer token.
"""
import os
import sys
import django

# Setup Django
# This script should be run from the anki_web_app directory or via docker-compose exec
import django
from django.conf import settings

if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spanish_anki_project.settings')
    django.setup()

from flashcards.dictionary_service import get_dictionary_entry
import json

def test_german_word():
    """Test dictionary lookup for German word."""
    print("Testing dictionary lookup for 'vorgeschlagen' (German)...")
    result = get_dictionary_entry('vorgeschlagen', 'de', 'en')
    
    if result:
        print("\n✅ Dictionary lookup successful!")
        print(json.dumps(result, indent=2))
        print(f"\nFound {len(result['meanings'])} meaning(s)")
        for i, meaning in enumerate(result['meanings'], 1):
            print(f"\nMeaning {i}:")
            print(f"  Part of speech: {meaning['part_of_speech']}")
            print(f"  Definitions: {meaning['definitions']}")
            if meaning.get('examples'):
                print(f"  Examples: {meaning['examples']}")
    else:
        print("\n❌ Dictionary lookup failed - returned None")
        print("This could mean:")
        print("  - Word not found in Wiktionary")
        print("  - API error (check network/logs)")
        print("  - Parsing error")

if __name__ == '__main__':
    test_german_word()
