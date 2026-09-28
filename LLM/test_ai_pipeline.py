# =========================================================
# WeatherGPT - AI Pipeline Test
# =========================================================

from app.pipeline import process_question


# =========================================================
# TEST QUESTIONS
# =========================================================

TEST_QUESTIONS = [

    # English
    "Will it rain tomorrow in Delhi?",

    # Hinglish
    "Kya kal Mumbai mein heavy rainfall hone ki sambhavna hai?",

    # Hindi
    "क्या कल भुवनेश्वर में बारिश होगी?",

    # Odia
    "ଆସନ୍ତାକାଲି ଭୁବନେଶ୍ୱରରେ ବର୍ଷା ହେବ କି?",

    # Current weather
    "What is the current temperature in Delhi?",

    # Forecast
    "What will the weather be tomorrow in Mumbai?"

]


# =========================================================
# RUN TESTS
# =========================================================

def run_tests():

    print("\n======================================")
    print("       WeatherGPT AI Test Suite")
    print("======================================")

    total = len(TEST_QUESTIONS)
    passed = 0

    for number, question in enumerate(
        TEST_QUESTIONS,
        start=1
    ):

        print("\n")
        print("======================================")
        print(f"TEST {number}/{total}")
        print("======================================")

        print("\nQuestion:")
        print(question)

        try:

            result = process_question(
                question
            )

            print("\nDetected Language:")
            print(
                result["analysis"].get(
                    "language",
                    "unknown"
                )
            )

            print("\nIntent:")
            print(
                result["analysis"].get(
                    "intent",
                    "unknown"
                )
            )

            print("\nLocation:")
            print(
                result["analysis"].get(
                    "location",
                    "unknown"
                )
            )

            print("\nSelected Tool:")
            print(
                result["selected_tool"]
            )

            print("\nFinal Answer:")
            print(
                result["final_answer"]
            )

            # Basic success check
            if result["final_answer"]:

                print("\n✅ TEST PASSED")

                passed += 1

            else:

                print("\n❌ TEST FAILED")

        except Exception as error:

            print("\n❌ TEST ERROR:")
            print(error)

    # =====================================================
    # SUMMARY
    # =====================================================

    print("\n======================================")
    print("             TEST SUMMARY")
    print("======================================")

    print(
        f"\nPassed: {passed}/{total}"
    )

    print(
        f"Failed: {total - passed}/{total}"
    )

    if passed == total:

        print(
            "\n🎉 ALL TESTS PASSED!"
        )

    else:

        print(
            "\n⚠️ Some tests need attention."
        )

    print(
        "\n======================================"
    )


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    run_tests()