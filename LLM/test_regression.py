from app.nlp.analyzer import analyze_question
from app.tools.selector import select_tool


TEST_CASES = [
    # =====================================================
    # ENGLISH
    # =====================================================

    {
        "question": "Will it rain tomorrow in Delhi?",
        "language": "English",
        "intent": "forecast",
        "location": "Delhi",
        "time": "tomorrow",
    },

    {
        "question": "What is the current weather in Mumbai?",
        "language": "English",
        "intent": "current_weather",
        "location": "Mumbai",
        "time": "now",
    },

    {
        "question": "What will the temperature be tomorrow in Kolkata?",
        "language": "English",
        "intent": "forecast",
        "location": "Kolkata",
        "time": "tomorrow",
    },


    # =====================================================
    # HINGLISH
    # =====================================================

    {
        "question": "Kya kal Mumbai mein baarish hogi?",
        "language": "Hinglish",
        "intent": "forecast",
        "location": "Mumbai",
        "time": "tomorrow",
    },

    {
        "question": "Abhi Ranchi ka weather kaisa hai?",
        "language": "Hinglish",
        "intent": "current_weather",
        "location": "Ranchi",
        "time": "now",
    },

    {
        "question": "Aaj Pune mein temperature kitna hai?",
        "language": "Hinglish",
        "intent": "current_weather",
        "location": "Pune",
        "time": "today",
    },


    # =====================================================
    # HINDI
    # =====================================================

    {
        "question": "क्या कल भुवनेश्वर में बारिश होगी?",
        "language": "Hindi",
        "intent": "forecast",
        "location": "Bhubaneswar",
        "time": "tomorrow",
    },

    {
        "question": "अभी दिल्ली का मौसम कैसा है?",
        "language": "Hindi",
        "intent": "current_weather",
        "location": "Delhi",
        "time": "now",
    },

    {
        "question": "अगले सप्ताह मुंबई का मौसम कैसा रहेगा?",
        "language": "Hindi",
        "intent": "forecast",
        "location": "Mumbai",
        "time": "next_week",
    },


    # =====================================================
    # ODIA
    # =====================================================

    {
        "question": "ଆସନ୍ତାକାଲି ଭୁବନେଶ୍ୱରରେ ବର୍ଷା ହେବ କି?",
        "language": "Odia",
        "intent": "forecast",
        "location": "Bhubaneswar",
        "time": "tomorrow",
    },

    {
        "question": "ଏବେ ଭୁବନେଶ୍ୱରର ପାଣିପାଗ କେମିତି ଅଛି?",
        "language": "Odia",
        "intent": "current_weather",
        "location": "Bhubaneswar",
        "time": "now",
    },

    {
        "question": "ଆଜି କଟକରେ ବର୍ଷା ହେବ କି?",
        "language": "Odia",
        "intent": "forecast",
        "location": "Cuttack",
        "time": "today",
    },


    # =====================================================
    # ADDITIONAL TESTS
    # =====================================================

    {
        "question": "Is there heavy rain tomorrow in Chennai?",
        "language": "English",
        "intent": "forecast",
        "location": "Chennai",
        "time": "tomorrow",
    },

    {
        "question": "कल मुंबई का तापमान कितना होगा?",
        "language": "Hindi",
        "intent": "forecast",
        "location": "Mumbai",
        "time": "tomorrow",
    },

    {
        "question": "What is the humidity in Kolkata?",
        "language": "English",
        "intent": "current_weather",
        "location": "Kolkata",
        "time": "now",
    },
]


def run_tests():

    print("\n======================================")
    print("     WeatherGPT Regression Test")
    print("======================================")

    passed = 0
    failed = 0

    for index, test in enumerate(TEST_CASES, start=1):

        print("\n--------------------------------------")
        print(f"TEST {index}/{len(TEST_CASES)}")
        print("--------------------------------------")

        question = test["question"]

        print(f"Question: {question}")

        try:

            result = analyze_question(question)

            detected_language = result.get("language")
            detected_intent = result.get("intent")
            detected_location = result.get("location")
            detected_time = result.get("time")

            selected_tool = select_tool(result)

            print(f"Language : {detected_language}")
            print(f"Intent   : {detected_intent}")
            print(f"Location : {detected_location}")
            print(f"Time     : {detected_time}")
            print(f"Tool     : {selected_tool}")

            errors = []

            if detected_language != test["language"]:
                errors.append(
                    f"Language expected {test['language']} "
                    f"but got {detected_language}"
                )

            if detected_intent != test["intent"]:
                errors.append(
                    f"Intent expected {test['intent']} "
                    f"but got {detected_intent}"
                )

            if detected_location != test["location"]:
                errors.append(
                    f"Location expected {test['location']} "
                    f"but got {detected_location}"
                )

            if detected_time != test["time"]:
                errors.append(
                    f"Time expected {test['time']} "
                    f"but got {detected_time}"
                )

            if errors:

                failed += 1

                print("\n❌ TEST FAILED")

                for error in errors:
                    print("   -", error)

            else:

                passed += 1

                print("\n✅ TEST PASSED")

        except Exception as error:

            failed += 1

            print("\n❌ TEST FAILED")
            print("Error:", error)


    print("\n======================================")
    print("           TEST SUMMARY")
    print("======================================")

    print(f"\nPassed: {passed}/{len(TEST_CASES)}")
    print(f"Failed: {failed}/{len(TEST_CASES)}")

    if failed == 0:

        print("\n🎉 ALL 15 REGRESSION TESTS PASSED!")

    else:

        print("\n⚠️ SOME TESTS FAILED.")

    print("\n======================================")


if __name__ == "__main__":
    run_tests()