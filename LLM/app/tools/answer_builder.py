import ollama
import json

MODEL_NAME = "llama3.2"


def build_final_answer(question, analysis, tool_result):

    language = analysis.get("language", "English")

    prompt = f"""
You are WeatherGPT, a multilingual weather assistant.

USER QUESTION:
{question}

DETECTED LANGUAGE:
{language}

ANALYSIS:
{json.dumps(analysis, ensure_ascii=False)}

LIVE WEATHER TOOL RESULT:
{json.dumps(tool_result, ensure_ascii=False)}

IMPORTANT INSTRUCTIONS:

1. Answer the user's original question directly.

2. Use the LIVE WEATHER TOOL RESULT as the primary
   source for actual weather information.

3. Do not invent weather information.

4. Do not mention internal tools, analyzer, selector,
   RAG, JSON, Llama, API, or programming.

5. Answer ONLY in the detected language.

6. If the language is English, answer completely in English.

7. If the language is Hindi, answer completely in Hindi.

8. If the language is Hinglish, answer naturally in
   Hinglish using Roman/English letters.

9. If rain probability is available, mention it.

10. If temperature is available and relevant, mention it.

11. If weather condition is available, mention it.

12. Keep the answer short, clear and useful.

13. For dangerous weather conditions, advise the user
    to follow official government warnings and local
    authorities.

Return ONLY the final natural-language answer.
"""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are WeatherGPT's final answer generator."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"].strip()


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print("\n======================================")
    print("       WeatherGPT Answer Builder")
    print("======================================")

    question = "Will it rain tomorrow in Bhubaneswar?"

    analysis = {
        "intent": "forecast",
        "location": "Bhubaneswar",
        "time": "tomorrow",
        "language": "English",
        "parameters": [
            "rainfall",
            "precipitation_probability"
        ]
    }

    tool_result = {
        "tool": "get_forecast",
        "location": "Bhubaneswar",
        "time": "tomorrow",
        "status": "live_data",
        "data": {
            "temperature_max_c": 32.2,
            "temperature_min_c": 25.8,
            "condition": "Thunderstorm",
            "rain_probability": 81,
            "precipitation_mm": 7.5,
            "rainfall_mm": 3.4
        }
    }

    try:

        answer = build_final_answer(
            question,
            analysis,
            tool_result
        )

        print("\nQuestion:")
        print(question)

        print("\nFinal Answer:")
        print(answer)

        print("\n======================================")
        print("             TEST COMPLETE")
        print("======================================")

    except Exception as error:

        print("\nERROR:")
        print(error)