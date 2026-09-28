from pathlib import Path
from types import SimpleNamespace

import pytest

from app.voice import transcription


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        ("Odia", None),
        ("Oriya", None),
        ("or-IN", None),
        ("Hindi", "hi"),
        ("en-IN", "en"),
        (None, None),
    ],
)
def test_whisper_language_code(language, expected):
    assert transcription.whisper_language_code(language) == expected


def test_transcribe_audio_uses_selected_language_and_removes_temporary_file(monkeypatch):
    captured = {}

    class FakeModel:
        def transcribe(self, audio_path, **kwargs):
            captured["path"] = Path(audio_path)
            captured["audio"] = captured["path"].read_bytes()
            captured["kwargs"] = kwargs
            return iter([SimpleNamespace(text=" ଆଜି ବର୍ଷା ହେବ କି? ")]), SimpleNamespace(language="or")

    monkeypatch.setattr(transcription, "_load_model", lambda: FakeModel())

    result = transcription.transcribe_audio(b"test audio", "voice.webm", "or-IN")

    assert result == {"text": "ଆଜି ବର୍ଷା ହେବ କି?", "language": "or"}
    assert captured["audio"] == b"test audio"
    assert captured["kwargs"]["language"] is None
    assert captured["kwargs"]["task"] == "transcribe"
    assert not captured["path"].exists()


def test_transcribe_audio_rejects_empty_recording():
    with pytest.raises(ValueError, match="empty"):
        transcription.transcribe_audio(b"", "voice.webm", "Odia")


def test_transcribe_endpoint_returns_transcript(monkeypatch):
    from fastapi.testclient import TestClient

    from app import api

    def fake_transcribe(audio, filename, language):
        assert audio == b"recorded audio"
        assert filename == "voice.webm"
        assert language == "or-IN"
        return {
            "text": "ଆଜି ବର୍ଷା ହେବ କି?",
            "language": "or",
        }

    monkeypatch.setattr(api, "transcribe_audio", fake_transcribe)
    response = TestClient(api.app).post(
        "/transcribe",
        files={"audio": ("voice.webm", b"recorded audio", "audio/webm")},
        data={"language": "or-IN"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "text": "ଆଜି ବର୍ଷା ହେବ କି?",
        "language": "or",
    }
