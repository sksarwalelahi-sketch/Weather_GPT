from datetime import date
import logging

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.gateway import router as gateway_router
from app.pipeline import process_question
from app.llm.llama import translate_texts
from app.voice.transcription import transcribe_audio


# =========================================================
# WEATHERGPT API
# =========================================================

app = FastAPI(
    title="WeatherGPT API",
    description="WeatherGPT API Gateway and multilingual AI Weather Assistant",
    version="1.0.0"
)

app.include_router(gateway_router)
logger = logging.getLogger(__name__)


# =========================================================
# REQUEST MODELS
# =========================================================

class WeatherRequest(BaseModel):
    question: str
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    language: str | None = None
    history: list[dict[str, str]] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None
    baselines: dict[str, float] | None = None


class TranslationRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=100)
    language: str = Field(min_length=2, max_length=32)


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    language: str = Field(default="English")


MAX_VOICE_AUDIO_BYTES = 15 * 1024 * 1024


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "WeatherGPT API is running"
    }


# =========================================================
# WEATHER QUESTION
# =========================================================

@app.post("/ask")
def ask_weather(request: WeatherRequest):

    try:

        result = process_question(
            request.question,
            location_context=request.location,
            language_context=request.language,
            history=request.history,
            climate_request={
                "start_date": (
                    request.start_date.isoformat()
                    if request.start_date else None
                ),
                "end_date": (
                    request.end_date.isoformat()
                    if request.end_date else None
                ),
                "baselines": request.baselines,
            },
        )

        return {
            "success": True,
            "question": request.question,
            "analysis": result["analysis"],
            "selected_tool": result["selected_tool"],
            "tool_result": result["tool_result"],
            "intelligence": result["intelligence"],
            "answer": result["final_answer"]
        }

    except Exception as error:

        return {
            "success": False,
            "error": str(error)
        }


@app.post("/translate")
def translate(request: TranslationRequest):
    """Translate live provider/UI strings without changing their structure."""
    try:
        return {
            "success": True,
            "translations": translate_texts(request.texts, request.language),
        }
    except Exception as error:
        return {"success": False, "error": str(error)}


@app.post("/transcribe")
async def transcribe_voice(
    audio: UploadFile = File(...),
    language: str = Form(default="English"),
):
    if audio.content_type and not audio.content_type.startswith("audio/"):
        raise HTTPException(status_code=415, detail="Upload a supported audio recording.")

    try:
        audio_bytes = await audio.read(MAX_VOICE_AUDIO_BYTES + 1)
    finally:
        await audio.close()

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="The audio recording is empty.")
    if len(audio_bytes) > MAX_VOICE_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio recordings must be 15 MB or smaller.")

    try:
        result = await run_in_threadpool(
            transcribe_audio,
            audio_bytes,
            audio.filename or "voice.webm",
            language,
        )
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        logger.exception("Unexpected voice transcription failure")
        raise HTTPException(
            status_code=500,
            detail="Voice recognition failed unexpectedly. Restart M2 and try again.",
        ) from error

    return {"success": True, **result}


# =========================================================
# TEXT-TO-SPEECH  (Gap #3 — Voice Output)
# =========================================================

@app.post("/tts", response_class=Response)
def text_to_speech_endpoint(request: TTSRequest):
    """
    Convert text to MP3 audio and return it as audio/mpeg bytes.
    Supports all 14 Indian languages via gTTS.

    Frontend usage:
        const res = await fetch('/api/m2/tts', { method: 'POST', body: JSON.stringify({text, language}) })
        const audioBlob = await res.blob()
        new Audio(URL.createObjectURL(audioBlob)).play()
    """
    try:
        from app.voice.text_to_speech import text_to_speech
        audio_bytes = text_to_speech(request.text, request.language)
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=weathergpt_response.mp3"},
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"TTS error: {exc}")


# =========================================================
# FULL VOICE LOOP: Speech → AI → Speech  (Gap #3)
# =========================================================

@app.post("/voice-ask")
def voice_ask(request: WeatherRequest):
    """
    Complete voice pipeline:
    1. Process question text through AI pipeline
    2. Return both text answer AND audio URL hint

    The frontend sends the transcribed question from Whisper (via /api/m2/ask),
    then calls /api/m2/tts with the returned answer to get audio back.
    This endpoint combines both steps and returns answer + audio_available flag.
    """
    try:
        result = process_question(
            request.question,
            location_context=request.location,
            language_context=request.language,
            history=request.history,
        )
        answer_text = result["final_answer"]
        language = result["analysis"].get("language", request.language or "English")
        return {
            "success": True,
            "question": request.question,
            "answer": answer_text,
            "language": language,
            "audio_available": True,
            "tts_endpoint": "/api/m2/tts",
            "tts_payload": {"text": answer_text, "language": language},
        }
    except Exception as error:
        return {"success": False, "error": str(error)}
