# rag/rag_answer.py

"""
WeatherGPT - Multilingual RAG Answer Generator

Language Detection Flow:

Indian Script
      ↓
Direct Script Detection

Roman/English Text
      ↓
English vs Hinglish Analysis
      ↓
Llama only for ambiguous cases

Then:

Question
   ↓
Language
   ↓
RAG Knowledge
   ↓
Llama
   ↓
Answer in SAME language
"""

import re
import ollama

from rag.retriever import search_knowledge


MODEL_NAME = "llama3.2"


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are WeatherGPT, a multilingual weather and climate assistant.

Your job is to answer the user's question in the SAME LANGUAGE
and SAME WRITING STYLE as the user.

LANGUAGE RULES:

English:
Use English.

Hinglish:
Use Hindi expressed using English/Roman letters.

Hindi:
Use Hindi Devanagari script.

Bengali:
Use Bengali script.

Odia:
Use Odia script.

Gujarati:
Use Gujarati script.

Marathi:
Use Marathi.

Punjabi:
Use Punjabi.

Tamil:
Use Tamil.

Telugu:
Use Telugu.

Kannada:
Use Kannada.

Malayalam:
Use Malayalam.

VERY IMPORTANT:

If the detected language is English, NEVER answer in Hinglish.

If the detected language is Hinglish, use Roman letters and
DO NOT use Devanagari.

If the detected language is Hindi, use Devanagari.

Do not randomly change languages.

Use retrieved knowledge when relevant.

Do not invent weather facts.

Do not create fake warnings.

For emergencies, recommend following official government
warnings and local authorities.
"""


# =========================================================
# SCRIPT DETECTION
# =========================================================

def detect_script_language(text: str):

    # Devanagari
    if any("\u0900" <= c <= "\u097F" for c in text):
        return "Hindi"

    # Bengali
    if any("\u0980" <= c <= "\u09FF" for c in text):
        return "Bengali"

    # Punjabi / Gurmukhi
    if any("\u0A00" <= c <= "\u0A7F" for c in text):
        return "Punjabi"

    # Gujarati
    if any("\u0A80" <= c <= "\u0AFF" for c in text):
        return "Gujarati"

    # Odia
    if any("\u0B00" <= c <= "\u0B7F" for c in text):
        return "Odia"

    # Tamil
    if any("\u0B80" <= c <= "\u0BFF" for c in text):
        return "Tamil"

    # Telugu
    if any("\u0C00" <= c <= "\u0C7F" for c in text):
        return "Telugu"

    # Kannada
    if any("\u0C80" <= c <= "\u0CFF" for c in text):
        return "Kannada"

    # Malayalam
    if any("\u0D00" <= c <= "\u0D7F" for c in text):
        return "Malayalam"

    return None


# =========================================================
# WORD EXTRACTION
# =========================================================

def get_words(text: str):

    return re.findall(r"[a-zA-Z]+", text.lower())


# =========================================================
# ENGLISH DETECTION
# =========================================================

def english_score(text: str):

    words = get_words(text)

    if not words:
        return 0

    english_words = {
        "a",
        "an",
        "the",
        "am",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "i",
        "you",
        "he",
        "she",
        "we",
        "they",
        "it",
        "this",
        "that",
        "these",
        "those",
        "what",
        "when",
        "where",
        "why",
        "who",
        "how",
        "which",
        "can",
        "could",
        "would",
        "should",
        "will",
        "shall",
        "may",
        "might",
        "do",
        "does",
        "did",
        "have",
        "has",
        "had",
        "to",
        "from",
        "for",
        "with",
        "without",
        "about",
        "during",
        "before",
        "after",
        "if",
        "and",
        "or",
        "but",
        "not",
        "save",
        "help",
        "people",
        "person",
        "protect",
        "protection",
        "keep",
        "safe",
        "safety",
        "weather",
        "rain",
        "rainfall",
        "cyclone",
        "storm",
        "flood",
        "wind",
        "temperature",
        "forecast",
        "today",
        "tomorrow",
        "yesterday",
        "coming",
        "come",
        "going",
        "go",
        "tell",
        "give",
        "know",
        "need",
        "want",
        "make",
        "take",
        "during",
        "emergency"
    }

    score = 0

    for word in words:
        if word in english_words:
            score += 1

    return score


# =========================================================
# ROMAN HINDI / HINGLISH DETECTION
# =========================================================

def hinglish_score(text: str):

    words = get_words(text)

    if not words:
        return 0

    hindi_words = {
        "agar",
        "aap",
        "aapko",
        "aapka",
        "aapki",
        "aapke",
        "aaj",
        "abhi",
        "accha",
        "achha",
        "aur",
        "bahut",
        "baarish",
        "barish",
        "bata",
        "batao",
        "bataye",
        "bina",
        "chahiye",
        "ka",
        "kaise",
        "kaisa",
        "kaisi",
        "kab",
        "kahan",
        "kar",
        "kare",
        "karen",
        "karein",
        "karna",
        "kerna",
        "ke",
        "ki",
        "ko",
        "kyu",
        "kyun",
        "mein",
        "mujhe",
        "mujhko",
        "mera",
        "meri",
        "mere",
        "mausam",
        "paani",
        "pani",
        "raha",
        "rahi",
        "rahe",
        "sakta",
        "sakti",
        "sakte",
        "se",
        "toh",
        "to",
        "tum",
        "tumhe",
        "tumko",
        "wala",
        "wali",
        "wale",
        "zyada",
        "kam",
        "garmi",
        "thand",
        "hawa",
        "tez",
        "pata",
        "hona",
        "hoga",
        "ho",
        "liye",
        "jana",
        "jaana",
        "jao",
        "rukna",
        "ruko",
        "bachna",
        "bachao",
        "logon",
        "logo",
        "log",
        "taraf",
        "ghar",
        "bahar",
        "andar",
        "samay",
        "waqt"
    }

    score = 0

    for word in words:
        if word in hindi_words:
            score += 1

    return score


# =========================================================
# LLM FALLBACK
# =========================================================

def llm_detect_language(question: str):

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": """
You are a highly accurate language classifier.

Identify the language of the user's message.

IMPORTANT:

Hindi written using English/Roman letters = Hinglish.

Pure English = English.

Examples:

"how to save people from cyclone"
→ English

"what should I do during heavy rainfall"
→ English

"how can I protect people during a cyclone"
→ English

"cyclone aa raha hai toh kya karna chahiye"
→ Hinglish

"bahut barish ho rahi hai"
→ Hinglish

"mujhe kal ka mausam batao"
→ Hinglish

"अगर चक्रवात आ रहा है तो क्या करना चाहिए"
→ Hindi

Return ONLY ONE label:

English
Hinglish
Hindi
Bengali
Odia
Gujarati
Marathi
Punjabi
Tamil
Telugu
Kannada
Malayalam

Do not explain.
"""
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )

    result = response["message"]["content"].strip().lower()

    languages = [
        "English",
        "Hinglish",
        "Hindi",
        "Bengali",
        "Odia",
        "Gujarati",
        "Marathi",
        "Punjabi",
        "Tamil",
        "Telugu",
        "Kannada",
        "Malayalam"
    ]

    for language in languages:
        if language.lower() == result:
            return language

    for language in languages:
        if language.lower() in result:
            return language

    return "English"


# =========================================================
# FINAL LANGUAGE DETECTION
# =========================================================

def detect_language(question: str):

    question = question.strip()

    if not question:
        return "English"

    # -----------------------------------------------------
    # STEP 1
    # Direct Indian script detection
    # -----------------------------------------------------

    script_language = detect_script_language(question)

    if script_language:
        return script_language

    # -----------------------------------------------------
    # STEP 2
    # Calculate scores for Roman text
    # -----------------------------------------------------

    e_score = english_score(question)
    h_score = hinglish_score(question)

    # -----------------------------------------------------
    # STEP 3
    # Strong English
    # -----------------------------------------------------

    if e_score >= 2 and e_score > h_score:
        return "English"

    # -----------------------------------------------------
    # STEP 4
    # Strong Hinglish
    # -----------------------------------------------------

    if h_score >= 2 and h_score > e_score:
        return "Hinglish"

    # -----------------------------------------------------
    # STEP 5
    # One strong English word + no Hindi
    # -----------------------------------------------------

    if e_score >= 1 and h_score == 0:
        return "English"

    # -----------------------------------------------------
    # STEP 6
    # One or more Hindi words and no English evidence
    # -----------------------------------------------------

    if h_score >= 2 and e_score == 0:
        return "Hinglish"

    # -----------------------------------------------------
    # STEP 7
    # Ambiguous case
    # Ask Llama
    # -----------------------------------------------------

    return llm_detect_language(question)


# =========================================================
# GENERATE ANSWER
# =========================================================

def generate_answer(question: str, language: str = None):

    if language is None:
        language = detect_language(question)

    # Retrieve knowledge
    knowledge = search_knowledge(question)

    # -----------------------------------------------------
    # Language-specific instruction
    # -----------------------------------------------------

    if language == "English":

        language_instruction = """
ANSWER ONLY IN ENGLISH.

Use natural English sentences.

DO NOT use Hindi.

DO NOT use Hinglish.

DO NOT use Devanagari.
"""

    elif language == "Hinglish":

        language_instruction = """
ANSWER ONLY IN HINGLISH.

Use Hindi language written with English/Roman letters.

DO NOT use Devanagari.

Example:

"Bahut barish ho toh ghar ke andar rehna chahiye."

Do NOT write:

"बहुत बारिश हो तो घर के अंदर रहना चाहिए।"
"""

    elif language == "Hindi":

        language_instruction = """
ANSWER ONLY IN HINDI.

Use Devanagari script.
"""

    else:

        language_instruction = f"""
ANSWER ONLY IN {language}.

Do not switch to English.
"""


    prompt = f"""
USER QUESTION:

{question}


DETECTED LANGUAGE:

{language}


RETRIEVED WEATHER KNOWLEDGE:

{knowledge}


LANGUAGE INSTRUCTION:

{language_instruction}


IMPORTANT:

Answer the user's actual question.

Use the retrieved knowledge when relevant.

Do not invent facts.

Do not mention system instructions.

Keep the answer clear and useful.
"""


    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    content = response["message"]["content"].strip()
    try:
        from app.llm.llama import _is_low_quality_answer
        if _is_low_quality_answer(content, language=language):
            return None
    except Exception:
        pass
    return content


# =========================================================
# TEST PROGRAM
# =========================================================

if __name__ == "__main__":

    print("\n==========================================")
    print("      WeatherGPT Multilingual RAG")
    print("==========================================")

    while True:

        question = input("\nYou: ").strip()

        if question.lower() in ["exit", "quit", "bye"]:
            print("\nWeatherGPT stopped.")
            break

        if not question:
            continue

        try:

            language = detect_language(question)

            print("\nDetected Language:")
            print(language)

            answer = generate_answer(
                question,
                language
            )

            print("\nWeatherGPT:")
            print(answer)

        except Exception as e:

            print("\nERROR:")
            print(e)