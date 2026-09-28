# =========================================================
# WeatherGPT - Speech To Text
# =========================================================

import whisper
import sounddevice as sd
import numpy as np
import tempfile
import wave
import os


# =========================================================
# CONFIGURATION
# =========================================================

MODEL_NAME = "small"

SAMPLE_RATE = 16000
RECORD_SECONDS = 8


# =========================================================
# LOAD WHISPER
# =========================================================

print("\n======================================")
print("     Loading WeatherGPT Voice AI")
print("======================================")

print("\nLoading Whisper model...")

model = whisper.load_model(MODEL_NAME)

print("Whisper model loaded!")


# =========================================================
# RECORD MICROPHONE AUDIO
# =========================================================

def record_audio(
    duration=RECORD_SECONDS,
    sample_rate=SAMPLE_RATE
):
    """
    Record audio from microphone.
    """

    print("\n======================================")
    print("        WeatherGPT Voice Input")
    print("======================================")

    print(
        f"\n🎤 Speak now... "
        f"({duration} seconds)"
    )

    try:

        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.float32
        )

        sd.wait()

    except Exception as error:

        raise RuntimeError(
            f"Microphone error: {error}"
        )

    print("Recording complete.")

    # Convert to 1D mono audio
    audio = np.squeeze(audio)

    return audio, sample_rate


# =========================================================
# AUDIO CLEANING
# =========================================================

def clean_audio(audio):
    """
    Basic audio normalization.
    """

    audio = np.asarray(
        audio,
        dtype=np.float32
    )

    # Remove DC offset
    audio = audio - np.mean(audio)

    # Normalize volume
    peak = np.max(
        np.abs(audio)
    )

    if peak > 0:

        audio = audio / peak

    # Prevent clipping
    audio = np.clip(
        audio,
        -1.0,
        1.0
    )

    return audio


# =========================================================
# SAVE WAV FILE
# =========================================================

def save_wav(
    audio,
    sample_rate
):
    """
    Save audio as temporary WAV file.
    """

    temp_file = tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False
    )

    audio_path = temp_file.name

    temp_file.close()

    # float32 -> int16
    audio_int16 = np.int16(
        np.clip(audio, -1, 1)
        * 32767
    )

    with wave.open(
        audio_path,
        "wb"
    ) as wav_file:

        wav_file.setnchannels(1)

        wav_file.setsampwidth(2)

        wav_file.setframerate(
            sample_rate
        )

        wav_file.writeframes(
            audio_int16.tobytes()
        )

    return audio_path


# =========================================================
# SPEECH TO TEXT
# =========================================================

def speech_to_text():

    # -----------------------------------------------------
    # Record
    # -----------------------------------------------------

    audio, sample_rate = record_audio()

    # -----------------------------------------------------
    # Clean
    # -----------------------------------------------------

    audio = clean_audio(audio)

    # -----------------------------------------------------
    # Check microphone level
    # -----------------------------------------------------

    volume = np.max(
        np.abs(audio)
    )

    print(
        f"\nAudio level: {volume:.4f}"
    )

    if volume < 0.01:

        return {
            "text": "",
            "language": "unknown",
            "error": (
                "Microphone volume is too low."
            )
        }

    # -----------------------------------------------------
    # Save temporary WAV
    # -----------------------------------------------------

    audio_path = save_wav(
        audio,
        sample_rate
    )

    try:

        print(
            "\n🔊 Processing your voice..."
        )

        # =================================================
        # WHISPER
        # =================================================

        result = model.transcribe(

            audio_path,

            # Automatically detect language
            language=None,

            # Speech -> text
            task="transcribe",

            # CPU compatibility
            fp16=False,

            # Reduce hallucination
            temperature=0,

            # Don't repeatedly copy previous text
            condition_on_previous_text=False,

            # Don't hallucinate during silence
            no_speech_threshold=0.6,

            # Better decoding
            beam_size=5,

            best_of=5,

            # Weather-related vocabulary
            initial_prompt=(
                "WeatherGPT weather assistant. "
                "Weather, forecast, rain, rainfall, "
                "heavy rainfall, temperature, humidity, "
                "wind, storm, cyclone, thunderstorm, "
                "Delhi, Mumbai, Bhubaneswar, Sonpur, "
                "Odisha, India. "
                "Kya kal Delhi mein heavy rainfall "
                "hone ki sambhavna hai? "
                "क्या कल दिल्ली में भारी बारिश होने की "
                "संभावना है?"
            ),

            verbose=False
        )

        # -------------------------------------------------
        # Get transcription
        # -------------------------------------------------

        text = result.get(
            "text",
            ""
        ).strip()

        language = result.get(
            "language",
            "unknown"
        )

        # -------------------------------------------------
        # Clean whitespace
        # -------------------------------------------------

        text = " ".join(
            text.split()
        )

        # -------------------------------------------------
        # Display detected language
        # -------------------------------------------------

        language_names = {

            "en": "English",
            "hi": "Hindi",
            "bn": "Bengali",
            "or": "Odia",
            "gu": "Gujarati",
            "mr": "Marathi",
            "pa": "Punjabi",
            "ta": "Tamil",
            "te": "Telugu",
            "kn": "Kannada",
            "ml": "Malayalam",
            "ur": "Urdu",
            "ne": "Nepali"
        }

        readable_language = language_names.get(
            language,
            language
        )

        return {
            "text": text,
            "language": language,
            "language_name": readable_language,
            "error": None
        }

    finally:

        # -------------------------------------------------
        # Delete temporary WAV
        # -------------------------------------------------

        try:

            if os.path.exists(
                audio_path
            ):

                os.remove(
                    audio_path
                )

        except Exception:

            pass


# =========================================================
# MAIN TEST
# =========================================================

if __name__ == "__main__":

    try:

        result = speech_to_text()

        print("\n======================================")
        print("          TRANSCRIPTION")
        print("======================================")

        print(
            "\nDetected Language:"
        )

        print(
            result.get(
                "language_name",
                result.get(
                    "language",
                    "unknown"
                )
            )
        )

        print(
            "\nWhisper Code:"
        )

        print(
            result.get(
                "language",
                "unknown"
            )
        )

        print(
            "\nYou said:"
        )

        print(
            result.get(
                "text",
                ""
            )
        )

        if result.get("error"):

            print(
                "\nERROR:"
            )

            print(
                result["error"]
            )

        print(
            "\n======================================"
        )

    except KeyboardInterrupt:

        print(
            "\n\nRecording stopped."
        )

    except Exception as error:

        print(
            "\nERROR:"
        )

        print(error)