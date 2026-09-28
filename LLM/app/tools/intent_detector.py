# tools/intent_detector.py

"""
WeatherGPT - Intent Detector

Purpose:
Understand what the user wants.

Examples:

"What is the weather today?"
        -> weather

"Will it rain tomorrow?"
        -> forecast

"Is there a cyclone warning?"
        -> alert

"What should I do during a cyclone?"
        -> safety

"Why does a cyclone happen?"
        -> climate

"How does rainfall happen?"
        -> knowledge
"""

import json
import ollama


MODEL_NAME = "llama3.2"


# =========================================================
# INTENT DETECTION
# =========================================================

def detect_intent(question: str) -> dict:
    """
    Detect the user's intent and extract useful entities.
    """

    prompt = f"""
You are the intent detection module of WeatherGPT.

Analyze the user's question and return ONLY valid JSON.

Possible intents:

weather
forecast
alert
safety
climate
agriculture
marine
aviation
knowledge
location

Definitions:

weather:
Current weather conditions.

forecast:
Future weather such as tomorrow, next week, rain prediction,
temperature prediction, etc.

alert:
Weather warnings, cyclone warnings, flood warnings,
heatwave warnings, storm alerts, etc.

safety:
What people should do during dangerous weather.

climate:
Climate, climate change, long-term weather patterns,
historical climate analysis.

agriculture:
Weather advice related to farming, crops, irrigation,
harvesting, etc.

marine:
Weather information related to sea, ocean, fishermen,
waves, wind at sea, etc.

aviation:
Weather information related to flights and aviation.

knowledge:
General educational weather questions.

location:
Questions mainly asking about identifying or finding a place.

Return JSON in exactly this format:

{{
    "intent": "forecast",
    "location": "Bhubaneswar",
    "time": "tomorrow",
    "parameters": []
}}

Rules:

- intent must be one of the allowed intents.
- location should contain the location mentioned by the user.
- If no location is mentioned, use null.
- time should contain words such as today, tomorrow,
  next week, etc., if present.
- If no time is mentioned, use null.
- parameters should contain important requested weather
  information.
- Do not add explanations.
- Return ONLY JSON.

User question:

{question}
"""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": """
You are a strict JSON intent classifier.

Never return normal sentences.
Always return valid JSON only.
"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    result = response["message"]["content"].strip()

    # -----------------------------------------------------
    # Remove markdown code fences if Llama adds them
    # -----------------------------------------------------

    if result.startswith("```"):
        result = result.replace("```json", "")
        result = result.replace("```", "")
        result = result.strip()

    # -----------------------------------------------------
    # Convert JSON text into Python dictionary
    # -----------------------------------------------------

    try:

        data = json.loads(result)

    except json.JSONDecodeError:

        # Safe fallback
        data = {
            "intent": "knowledge",
            "location": None,
            "time": None,
            "parameters": []
        }

    return data


# =========================================================
# TEST PROGRAM
# =========================================================

if __name__ == "__main__":

    print("\n===================================")
    print("     WeatherGPT Intent Detector")
    print("===================================")

    while True:

        question = input("\nYou: ").strip()

        if question.lower() in ["exit", "quit", "bye"]:
            print("\nIntent Detector stopped.")
            break

        if not question:
            continue

        try:

            result = detect_intent(question)

            print("\nDetected Intent:")
            print(json.dumps(
                result,
                indent=4,
                ensure_ascii=False
            ))

        except Exception as e:

            print("\nERROR:")
            print(e)