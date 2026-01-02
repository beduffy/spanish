"""
Text-to-Speech service using Google Cloud TTS or ElevenLabs.
Generates audio files and stores them.
"""

import os
import requests
from typing import Optional
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from decouple import config


GOOGLE_TTS_CREDENTIALS_PATH = config('GOOGLE_TTS_CREDENTIALS_PATH', default='')
ELEVENLABS_API_KEY = config('ELEVENLABS_API_KEY', default='')
ELEVENLABS_VOICE_ID = config('ELEVENLABS_VOICE_ID', default='21m00Tcm4TlvDq8ikWAM')  # Default voice: Rachel


def _get_elevenlabs_voice_id(language_code: str) -> str:
    """Map language code to ElevenLabs voice ID."""
    # Default voice mappings (can be customized)
    voice_map = {
        'de-DE': 'pNInz6obpgDQGcFmaJgB',  # Adam (German)
        'es-ES': 'EXAVITQu4vr4xnSDxMaL',  # Bella (Spanish)
        'fr-FR': 'ThT5KcBeYPX3keUQyH3D',  # Arnold (French)
        'it-IT': 'EXAVITQu4vr4xnSDxMaL',  # Bella (Italian)
        'en-US': '21m00Tcm4TlvDq8ikWAM',  # Rachel (English)
    }
    return voice_map.get(language_code, ELEVENLABS_VOICE_ID)


def generate_tts_audio(text: str, language_code: str = 'de-DE', output_filename: str = None) -> Optional[str]:
    """
    Generate TTS audio using Google Cloud TTS (preferred) or ElevenLabs (fallback).
    Returns the file path/URL.
    """
    # Try Google Cloud TTS first
    audio_url = _generate_google_tts(text, language_code, output_filename)
    if audio_url:
        return audio_url
    
    # Fallback to ElevenLabs if Google TTS fails
    audio_url = _generate_elevenlabs_tts(text, language_code, output_filename)
    if audio_url:
        return audio_url
    
    return None


def _generate_google_tts(text: str, language_code: str, output_filename: str = None) -> Optional[str]:
    """Generate TTS using Google Cloud TTS."""
    if not GOOGLE_TTS_CREDENTIALS_PATH or not os.path.exists(GOOGLE_TTS_CREDENTIALS_PATH):
        return None
    
    try:
        from google.cloud import texttospeech
        
        client = texttospeech.TextToSpeechClient.from_service_account_file(
            GOOGLE_TTS_CREDENTIALS_PATH
        )
        
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Save to Django storage
        if not output_filename:
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            output_filename = f'tts/google_{text_hash}.mp3'
        
        file_path = default_storage.save(output_filename, ContentFile(response.audio_content))
        audio_url = default_storage.url(file_path)
        # Ensure URL is absolute for frontend access
        if audio_url.startswith('/'):
            from django.conf import settings
            # In production, you might want to use a full domain
            # For now, return relative URL (frontend will handle it)
            pass
        return audio_url
        
    except ImportError:
        print("google-cloud-texttospeech not installed. Install with: pip install google-cloud-texttospeech")
        return None
    except Exception as e:
        print(f"Google TTS error: {e}")
        return None


def _generate_elevenlabs_tts(text: str, language_code: str, output_filename: str = None) -> Optional[str]:
    """Generate TTS using ElevenLabs API."""
    if not ELEVENLABS_API_KEY:
        return None
    
    try:
        voice_id = _get_elevenlabs_voice_id(language_code)
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",  # Supports multiple languages
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Save to Django storage
        if not output_filename:
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            output_filename = f'tts/elevenlabs_{text_hash}.mp3'
        
        file_path = default_storage.save(output_filename, ContentFile(response.content))
        return default_storage.url(file_path)
        
    except Exception as e:
        print(f"ElevenLabs TTS error: {e}")
        return None
