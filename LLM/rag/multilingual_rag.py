import sys
import os

# Allow Python to find the app folder
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.append(PROJECT_ROOT)

from app.nlp.analyzer import analyze_question
from rag_answer import generate_answer


def process_question(question: str):

    # ======================================
    # STEP 1: Analyze the question
    # ======================================

    analysis = analyze_question(question)

    print("\n========== ANALYSIS ==========")
    print(analysis)

    # ======================================
    # STEP 2: Automatically detect language
    # ======================================

    language = analysis.get("language", "English")

    # ======================================
    # STEP 3: Generate RAG + Llama answer
    # ======================================

    answer = generate_answer(
        question,
        language
    )

    return {
        "question": question,
        "analysis": analysis,
        "language": language,
        "answer": answer
    }


# ==========================================
# MAIN PROGRAM
# ==========================================

if __name__ == "__main__":

    print("\n======================================")
    print("      WeatherGPT AI Assistant")
    print("======================================")

    print("\nType 'exit' to stop.")

    while True:

        question = input("\nYou: ")

        if question.lower().strip() == "exit":

            print("\nWeatherGPT stopped.")

            break

        if not question.strip():

            print("Please enter a question.")

            continue

        try:

            result = process_question(question)

            print("\nDetected Language:")
            print(result["language"])

            print("\nWeatherGPT:")
            print(result["answer"])

        except Exception as e:

            print("\nERROR:")
            print(e)