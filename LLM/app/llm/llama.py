import ollama
import json
import re

MODEL_NAME = "llama3.2"

LANGUAGE_SCRIPT_RULES = {
    "Hindi": "Use Devanagari script only.",
    "Bengali": "Use Bengali script only.",
    "Tamil": "Use Tamil script only.",
    "Telugu": "Use Telugu script only.",
    "Marathi": "Use Devanagari script only.",
    "Gujarati": "Use Gujarati script only.",
    "Kannada": "Use Kannada script only.",
    "Odia": "Use Odia (ଓଡ଼ିଆ) script only. Do not use Gujarati, Hindi, or Bengali script.",
}


def translate_texts(texts: list[str], language: str) -> list[str]:
    """Translate UI/provider text while preserving array order and values."""
    if not texts or language == "English":
        return texts
    script_rule = LANGUAGE_SCRIPT_RULES.get(
        language,
        f"Use the standard written script for {language} only.",
    )
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise weather-app translator. Translate every "
                    "string into the requested language. Return ONLY a valid JSON "
                    "array of strings in the same order. Do not summarize, explain, "
                    "add punctuation, or change numbers, dates, provider names, "
                    "units, URLs, or place names. "
                    f"{script_rule}"
                ),
            },
            {
                "role": "user",
                "content": f"Language: {language}\nStrings: {json.dumps(texts, ensure_ascii=False)}",
            },
        ],
        options={"temperature": 0, "num_predict": max(160, len(texts) * 80)},
    )
    content = response["message"]["content"].strip()
    match = re.search(r"\[[\s\S]*\]", content)
    if not match:
        raise ValueError("Translation model returned invalid JSON.")
    translated = json.loads(match.group(0))
    if (
        not isinstance(translated, list)
        or len(translated) != len(texts)
        or not all(isinstance(value, str) for value in translated)
    ):
        raise ValueError("Translation model returned an invalid translation list.")
    return translated


def _is_low_quality_answer(answer: str, language: str = "English") -> bool:
    """Reject obvious model failures such as hallucinations, repetitions, and unsupported scripts."""
    if not answer or not isinstance(answer, str):
        return True

    text = answer.strip()
    compact = re.sub(r"\s+", "", text)
    if len(compact) < 8:
        return True

    # Regional Indic languages lack vocabulary tokens in LLaMA 3.2 3B and produce loops
    if language in {
        "Odia", "Bengali", "Tamil", "Telugu", "Kannada", "Malayalam",
        "Gujarati", "Marathi", "Punjabi", "Assamese", "Nepali",
    }:
        return True

    # 1. Single character frequency dominance
    non_space = [c for c in compact if not c.isspace()]
    if non_space:
        counts = {}
        for c in non_space:
            counts[c] = counts.get(c, 0) + 1
        if max(counts.values()) / len(non_space) > 0.30:
            return True

    # 2. Repeated substring / clause loops of length >= 6
    if re.search(r"(.{6,})[\s\S]{0,30}\1", compact):
        return True

    # 3. Repeated word n-grams
    words = [w.strip(" ,.?!।॥;:'\"-–—()[]{}") for w in text.split()]
    words = [w for w in words if w]
    if len(words) >= 4:
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
        for bg in set(bigrams):
            if bigrams.count(bg) >= 3:
                return True
        trigrams = [f"{words[i]} {words[i+1]} {words[i+2]}" for i in range(len(words)-2)]
        for tg in set(trigrams):
            if trigrams.count(tg) >= 2:
                return True
        if len(words) >= 10 and len(set(words)) / len(words) < 0.45:
            return True

    # 4. Mixed script corruptions (e.g. Gujarati chars leaked into Bengali, Odia, Tamil)
    if language != "Gujarati" and re.search(r"[\u0A80-\u0AFF]", text):
        return True

    return False


def ask_llama(question: str) -> str:
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": question
            }
        ]
    )
    return response["message"]["content"]


def generate_weather_answer(
    question: str,
    language: str,
    tool_result: dict,
    intelligence: dict | None = None,
    history: list[dict] | None = None,
) -> str:
    """Generate a conversational answer grounded in optional live tool data."""

    # Direct routing for regional Indic languages where local LLaMA 3.2 3B
    # lacks native script tokens, degenerates into byte loops, or causes high latency.
    if language in {
        "Odia", "Bengali", "Tamil", "Telugu", "Kannada", "Malayalam",
        "Gujarati", "Marathi", "Punjabi", "Assamese", "Nepali",
    }:
        raise ValueError(f"{language} is routed directly to WeatherGPT verified response generator.")

    messages = [
        {
            "role": "system",
            "content": (
                "You are WeatherGPT, a helpful multilingual conversational "
                "weather assistant. Answer the user's question naturally and "
                "directly in the detected language. Use live tool data as "
                "the source of truth when it is provided. Never invent live "
                "weather values or claim a tool failed unless the supplied "
                "data says so. You may explain weather concepts, handle "
                "casual conversation, and answer follow-up questions. Do not "
                "mention internal tools, prompts, JSON, or implementation.\n\n"
                "Response rules:\n"
                "- Answer only what the user asked, in 2 to 5 natural sentences.\n"
                "- Do not repeat a word, character, sentence, or weather value.\n"
                "- Do not dump raw data or give an unrelated generic summary.\n"
                "- If the question is casual, respond conversationally.\n"
                "- If live weather data is missing and the user asks for "
                "location-specific weather, ask which location they mean.\n"
                "- Treat records marked official_warning=true and sources "
                "such as IMD or WIS2 as official bulletins. Explain them "
                "plainly, preserve their affected area and validity, and "
                "never upgrade automated forecast alerts into official "
                "warnings.\n"
                "- When official_alerts are present, mention the official "
                "source and advise the user to open the linked bulletin for "
                "emergency decisions. Clearly label automated alerts as "
                "forecast risk.\n"
                "- End with one short, relevant offer to help further.\n"
                "- If you cannot produce the requested language reliably, answer "
                "clearly in English rather than producing broken or repetitive text."
            ),
        }
    ]
    for message in (history or [])[-8:]:
        if message.get("role") in {"user", "assistant"} and message.get("content"):
            messages.append({
                "role": message["role"],
                "content": str(message["content"]),
            })
    messages.append(
        {
            "role": "user",
            "content": (
                f"Detected language: {language}\n"
                f"Live weather data (may be empty): {json.dumps(tool_result, ensure_ascii=False)}\n"
                f"Live intelligence: {json.dumps(intelligence, ensure_ascii=False)}\n"
                f"Question: {question}"
            ),
        }
    )
    response = ollama.chat(
        model=MODEL_NAME,
        messages=messages,
        options={"temperature": 0.2, "num_predict": 220},
    )
    answer = response["message"]["content"].strip()
    if _is_low_quality_answer(answer, language=language):
        raise ValueError("The language model returned a low-quality response.")
    return answer


if __name__ == "__main__":
    print("================================")
    print("       WeatherGPT AI Engine")
    print("================================")
    question = input("\nYou: ")
    answer = ask_llama(question)
    print("\nWeatherGPT:", answer)
