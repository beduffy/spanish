"""
Text-to-Speech service using Google Cloud TTS (free tier: 1M chars/month).
Generates audio files and stores them.
"""

import os
from typing import Optional
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from decouple import config


GOOGLE_TTS_CREDENTIALS_PATH = config('GOOGLE_TTS_CREDENTIALS_PATH', default='')


def generate_tts_audio(text: str, language_code: str = 'de-DE', output_filename: str = None) -> Optional[str]:
    """
    Generate TTS audio using Google Cloud TTS.
    Returns the file path/URL.
    """
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
            output_filename = f'tts/{text_hash}.mp3'
        
        file_path = default_storage.save(output_filename, ContentFile(response.audio_content))
        return default_storage.url(file_path)
        
    except ImportError:
        print("google-cloud-texttospeech not installed. Install with: pip install google-cloud-texttospeech")
        return None
    except Exception as e:
        print(f"TTS error: {e}")
        return None
