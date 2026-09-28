from __future__ import annotations

import os
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any


_LANGUAGE_CODES = {
    "assamese": "as",
    "bengali": "bn",
    "english": "en",
    "gujarati": "gu",
    "hindi": "hi",
    "kannada": "kn",
    "malayalam": "ml",
    "marathi": "mr",
    "nepali": "ne",
    "odia": "or",
    "oriya": "or",
    "punjabi": "pa",
    "tamil": "ta",
    "telugu": "te",
    "urdu": "ur",
}


def whisper_language_code(language: str | None) -> str | None:
    if not language:
        return None
    normalized = language.strip().lower()
    if normalized in {"odia", "oriya", "or-in"}:
        return None
    if normalized in _LANGUAGE_CODES:
        return _LANGUAGE_CODES[normalized]
    language_code = normalized.split("-", maxsplit=1)[0]
    return language_code if len(language_code) == 2 else None


@lru_cache(maxsize=1)
def _load_model() -> Any:
    try:
        from faster_whisper import WhisperModel
    except ImportError as error:
        raise RuntimeError(
            "Voice transcription is not installed. Install the LLM service requirements."
        ) from error

    model_name = os.getenv("WHISPER_MODEL", "tiny")
    try:
        return WhisperModel(model_name, device="cpu", compute_type="int8")
    except Exception as error:
        raise RuntimeError(
            f"Could not load the {model_name!r} speech model. Check the network connection and available memory, then retry."
        ) from error


def transcribe_audio(audio: bytes, filename: str, language: str | None) -> dict[str, str | None]:
    if not audio:
        raise ValueError("The audio recording is empty.")

    suffix = Path(filename).suffix.lower()
    if suffix not in {".m4a", ".mp3", ".mp4", ".ogg", ".wav", ".webm"}:
        suffix = ".webm"

    audio_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as audio_file:
            audio_file.write(audio)
            audio_path = audio_file.name

        try:
            segments, info = _load_model().transcribe(
                audio_path,
                language=whisper_language_code(language),
                task="transcribe",
                beam_size=3,
                vad_filter=True,
                condition_on_previous_text=False,
            )
            transcript = " ".join(segment.text.strip() for segment in segments).strip()
        except Exception as error:
            raise RuntimeError(
                "Speech recognition failed while processing the recording. Check that the audio is clear and try again."
            ) from error
        return {
            "text": transcript,
            "language": getattr(info, "language", None),
        }
    finally:
        if audio_path is not None:
            Path(audio_path).unlink(missing_ok=True)
