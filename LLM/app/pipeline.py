from app.nlp.analyzer import analyze_question
from app.tools.selector import select_tool
from app.tools.tool_runner import run_selected_tool
from app.response.response_generator import generate_final_answer
from app.response.knowledge_answer import generate_knowledge_answer
from app.intelligence.weather_intelligence import analyze_weather_intelligence
from app.intelligence.member3_client import get_intelligence
from app.llm.llama import generate_weather_answer as generate_llama_answer


def process_question(
    question: str,
    climate_request: dict | None = None,
    location_context: str | None = None,
    language_context: str | None = None,
    history: list[dict] | None = None,
):
    """
    Complete WeatherGPT AI pipeline.

    Flow:
    Question
        ↓
    Language + Intent + Location Analysis
        ↓
    Tool Selection
        ↓
    Weather Data
        ↓
    Weather Intelligence
        ↓
    Final Natural Language Answer
    """

    # 1. Analyze user question
    analysis = analyze_question(question)
    # Resolve short follow-ups such as "what about tomorrow?" from the most
    # recent user turn before falling back to browser location context.
    if not analysis.get("location") and history:
        for previous_message in reversed(history):
            if previous_message.get("role") != "user":
                continue
            previous_question = str(previous_message.get("content", "")).strip()
            if not previous_question:
                continue
            previous_analysis = analyze_question(previous_question)
            if previous_analysis.get("location"):
                analysis["location"] = previous_analysis["location"]
                break
    if location_context and not analysis.get("location"):
        analysis["location"] = location_context
    detected_lang = analysis.get("language", "English")
    if language_context and language_context in {
        "English", "Hinglish", "Hindi", "Bengali", "Odia", "Gujarati",
        "Marathi", "Punjabi", "Tamil", "Telugu", "Kannada", "Malayalam",
        "Assamese", "Urdu", "Nepali",
    }:
        if detected_lang not in {"English", "Hinglish"} and language_context == "English":
            # Keep detected Indic script if user typed in regional language
            pass
        else:
            analysis["language"] = language_context

    # 2. Select weather tool
    selected_tool = select_tool(analysis)

    # 3. Run a grounding tool only when this is a location-specific request.
    # General conversation must reach the LLM even when no location is known.
    location = analysis.get("location")
    if selected_tool == "general_weather":
        tool_result = {
            "status": "not_required",
            "data": {},
        }
    elif not location:
        tool_result = {
            "status": "location_required",
            "message": "A location is required for live weather data.",
            "data": {},
        }
    else:
        try:
            tool_result = run_selected_tool(
                analysis,
                selected_tool,
                climate_request=climate_request,
            )
        except Exception as error:
            tool_result = {
                "status": "unavailable",
                "message": str(error),
                "data": {},
            }

    # 4. Analyze weather intelligence
    intelligence_result = None

    if (
        selected_tool != "get_climate_analysis"
        and tool_result.get("status") == "live_data"
        and isinstance(tool_result, dict)
    ):
        weather_data = tool_result.get("data")

        if isinstance(weather_data, dict):
            intelligence_result = analyze_weather_intelligence(
                weather_data
            )

    # Member 3 is the canonical intelligence and decision engine.
    # Keep the existing local intelligence result only as an offline fallback.
    if (
        selected_tool == "get_climate_analysis"
        and tool_result.get("status") == "intelligence_data"
    ):
        intelligence_result = tool_result.get("data")

    elif location and tool_result.get("status") == "live_data":
        member3_intelligence = get_intelligence(
            location,
            selected_tool,
        )

        if member3_intelligence is not None:
            intelligence_result = member3_intelligence

    # 5. Llama is the primary conversational layer. Deterministic/RAG
    # responders are fallbacks for offline or low-quality model responses.
    final_answer = None
    llm_language = analysis.get("language", "English")
    try:
        final_answer = generate_llama_answer(
            question=question,
            language=llm_language,
            tool_result=tool_result,
            intelligence=intelligence_result,
            history=history,
        )
    except Exception:
        final_answer = None

    if (
        final_answer is None
        and selected_tool == "general_weather"
    ):
        final_answer = generate_knowledge_answer(
            question,
            llm_language,
        )

    if final_answer is None:
        final_answer = generate_final_answer(
            question,
            analysis,
            tool_result,
            intelligence_result
        )

    # 6. Return complete result
    return {
        "analysis": analysis,
        "selected_tool": selected_tool,
        "tool_result": tool_result,
        "intelligence": intelligence_result,
        "final_answer": final_answer
    }


def main():
    """Run WeatherGPT from the terminal."""

    print("\n======================================")
    print("       WeatherGPT AI Pipeline")
    print("======================================")
    print("\nAsk your weather question.")
    print("Type 'exit' to stop.")

    while True:
        question = input("\nYou: ").strip()

        if question.lower() in ["exit", "quit", "bye"]:
            print("\nWeatherGPT stopped.")
            break

        if not question:
            print("Please enter a question.")
            continue

        try:
            result = process_question(question)

            print("\n--- Analysis ---")
            print(result["analysis"])

            print("\n--- Selected Tool ---")
            print(result["selected_tool"])

            print("\n--- Weather Data ---")
            print(result["tool_result"])

            print("\n--- Weather Intelligence ---")

            intelligence = result["intelligence"]

            if intelligence:
                print("Risk:", intelligence["risk"]["level"])
                print("Risk Score:", intelligence["risk"]["score"])
                print("Alerts:", len(intelligence["alerts"]))

                print("\nAdvisory:")
                print(intelligence["advisory_text"])
            else:
                print("Weather intelligence unavailable.")

            print("\n======================================")
            print("           FINAL ANSWER")
            print("======================================")
            print(result["final_answer"])
            print("======================================")

        except Exception as error:
            print("\nERROR:")
            print(error)


if __name__ == "__main__":
    main()
