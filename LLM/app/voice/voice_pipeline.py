# =========================================================
# WeatherGPT - Voice Pipeline
# =========================================================

from app.voice.speech_to_text import speech_to_text
from app.nlp.analyzer import analyze_question
from app.tools.selector import select_tool
from app.tools.tool_runner import run_selected_tool
from app.response.response_generator import generate_final_answer


# =========================================================
# VOICE QUESTION PROCESSOR
# =========================================================

def process_voice_question():

    print("\n======================================")
    print("       WeatherGPT Voice Assistant")
    print("======================================")

    # -----------------------------------------------------
    # STEP 1: Voice -> Text
    # -----------------------------------------------------

    print("\n🎤 Speak your weather question...")

    voice_result = speech_to_text()

    # Check for microphone / Whisper error
    if voice_result.get("error"):

        print("\n❌ Voice Error:")
        print(voice_result["error"])

        return

    question = voice_result.get(
        "text",
        ""
    ).strip()

    if not question:

        print(
            "\n❌ Could not understand your speech."
        )

        return

    print("\n📝 You said:")
    print(question)

    print("\n🌐 Whisper detected language:")
    print(
        voice_result.get(
            "language_name",
            voice_result.get(
                "language",
                "unknown"
            )
        )
    )

    # -----------------------------------------------------
    # STEP 2: Analyze Question
    # -----------------------------------------------------

    print("\n🔍 Analyzing question...")

    analysis = analyze_question(
        question
    )

    print("\n--- Detected Analysis ---")
    print(analysis)

    # -----------------------------------------------------
    # STEP 3: Select Tool
    # -----------------------------------------------------

    print("\n🛠 Selecting weather tool...")

    selected_tool = select_tool(
        analysis
    )

    print("\n--- Selected Tool ---")
    print(selected_tool)

    # -----------------------------------------------------
    # STEP 4: Run Weather Tool
    # -----------------------------------------------------

    print("\n🌦 Getting weather information...")

    tool_result = run_selected_tool(
        analysis,
        selected_tool
    )

    print("\n--- Weather Data ---")
    print(tool_result)

    # -----------------------------------------------------
    # STEP 5: Generate Final Llama Answer
    # -----------------------------------------------------

    print("\n🤖 Generating final answer...")

    final_answer = generate_final_answer(
        question,
        analysis,
        tool_result
    )

    # -----------------------------------------------------
    # FINAL OUTPUT
    # -----------------------------------------------------

    print("\n======================================")
    print("           FINAL ANSWER")
    print("======================================")

    print(
        "\n" + final_answer
    )

    print("\n======================================")


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    try:

        process_voice_question()

    except KeyboardInterrupt:

        print(
            "\n\nVoice assistant stopped."
        )

    except Exception as error:

        print("\n❌ ERROR:")
        print(error)