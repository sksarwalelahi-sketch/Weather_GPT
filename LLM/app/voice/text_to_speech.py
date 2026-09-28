"""
WeatherGPT - Text-to-Speech (TTS) Output
==========================================
Converts WeatherGPT text responses to audio for rural voice accessibility.

Strategy:
  1. gTTS (Google TTS) — works online, supports all Indian languages
  2. pyttsx3 — offline fallback if gTTS fails (English/Hindi only)

The /tts endpoint in api.py returns audio/mpeg bytes directly.
Frontend uses the browser's Audio API to play it.
"""
from __future__ import annotations

import io
import logging
import os
import tempfile

logger = logging.getLogger(__name__)

# Language code map: WeatherGPT language name → gTTS language code
GTTS_LANG_MAP: dict[str, str] = {
    "English":   "en",
    "Hinglish":  "hi",
    "Hindi":     "hi",
    "Bengali":   "bn",
    "Odia":      "or",
    "Gujarati":  "gu",
    "Marathi":   "mr",
    "Punjabi":   "pa",
    "Tamil":     "ta",
    "Telugu":    "te",
    "Kannada":   "kn",
    "Malayalam": "ml",
    "Assamese":  "as",
    "Urdu":      "ur",
    "Nepali":    "ne",
}


def text_to_speech(text: str, language: str = "English") -> bytes:
    """
    Convert text to MP3 audio bytes.

    Parameters
    ----------
    text:     The answer text to speak (max ~500 chars for performance)
    language: WeatherGPT language name (e.g. 'Hindi', 'Tamil', 'English')

    Returns
    -------
    bytes: MP3 audio data ready to stream to frontend
    """
    # Limit to ~500 characters to keep latency low
    if len(text) > 500:
        text = text[:497] + "…"

    lang_code = GTTS_LANG_MAP.get(language, "en")

    # ---- Try gTTS (online, best quality, all Indian languages) ----
    try:
        from gtts import gTTS  # type: ignore[import]
        tts = gTTS(text=text, lang=lang_code, slow=False)
        buffer = io.BytesIO()
        tts.write_to_fp(buffer)
        buffer.seek(0)
        audio_bytes = buffer.read()
        logger.info("gTTS succeeded for language '%s' (%s)", language, lang_code)
        return audio_bytes
    except ImportError:
        logger.warning("gTTS not installed, trying pyttsx3 fallback")
    except Exception as exc:
        logger.warning("gTTS failed (%s), trying pyttsx3 fallback", exc)

    # ---- Fallback: pyttsx3 (offline, English only) ----
    try:
        import pyttsx3  # type: ignore[import]
        engine = pyttsx3.init()
        engine.setProperty("rate", 160)   # words per minute
        engine.setProperty("volume", 0.9)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()
            with open(tmp_path, "rb") as f:
                audio_bytes = f.read()
            logger.info("pyttsx3 TTS fallback succeeded")
            return audio_bytes
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except ImportError:
        logger.error("Neither gTTS nor pyttsx3 is installed. Install: pip install gTTS")
    except Exception as exc:
        logger.error("pyttsx3 TTS fallback failed: %s", exc)

    raise RuntimeError(
        "TTS unavailable: install gTTS with 'pip install gTTS' in the LLM venv"
    )

