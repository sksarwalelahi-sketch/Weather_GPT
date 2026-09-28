from app.nlp.analyzer import analyze_question
from app.tools.selector import select_tool


# ============================================================
# MULTILINGUAL TEST QUESTIONS
# ============================================================

TEST_CASES = [
    # ---------------- ENGLISH ----------------
    {
        "language": "English",
        "question": "Will it rain tomorrow in Delhi?"
    },

    # ---------------- HINGLISH ----------------
    {
        "language": "Hinglish",
        "question": "Kya kal Mumbai mein baarish hogi?"
    },

    # ---------------- HINDI ----------------
    {
        "language": "Hindi",
        "question": "क्या कल भुवनेश्वर में बारिश होगी?"
    },

    # ---------------- ODIA ----------------
    {
        "language": "Odia",
        "question": "ଆସନ୍ତାକାଲି ଭୁବନେଶ୍ୱରରେ ବର୍ଷା ହେବ କି?"
    },

    # ---------------- PUNJABI ----------------
    {
        "language": "Punjabi",
        "question": "ਕੀ ਕੱਲ੍ਹ ਦਿੱਲੀ ਵਿੱਚ ਮੀਂਹ ਪਵੇਗਾ?"
    },

    # ---------------- BENGALI ----------------
    {
        "language": "Bengali",
        "question": "আগামীকাল কলকাতায় বৃষ্টি হবে কি?"
    },
    {
        "language": "Bengali",
        "question": "এখন কলকাতার আবহাওয়া কেমন?"
    },
    {
        "language": "Bengali",
        "question": "আগামীকাল কলকাতায় তাপমাত্রা কত হবে?"
    },

    # ---------------- GUJARATI ----------------
    {
        "language": "Gujarati",
        "question": "કાલે અમદાવાદમાં વરસાદ પડશે કે?"
    },
    {
        "language": "Gujarati",
        "question": "હમણાં અમદાવાદનું હવામાન કેવું છે?"
    },
    {
        "language": "Gujarati",
        "question": "કાલે અમદાવાદમાં તાપમાન કેટલું રહેશે?"
    },

    # ---------------- URDU ----------------
    {
        "language": "Urdu",
        "question": "کیا کل دہلی میں بارش ہوگی؟"
    },
    {
        "language": "Urdu",
        "question": "ابھی دہلی کا موسم کیسا ہے؟"
    },
    {
        "language": "Urdu",
        "question": "کل دہلی میں درجہ حرارت کتنا ہوگا؟"
    },

    # ---------------- MARATHI ----------------
    {
        "language": "Marathi",
        "question": "उद्या मुंबईत पाऊस पडेल का?"
    },
    {
        "language": "Marathi",
        "question": "आत्ता मुंबईचे हवामान कसे आहे?"
    },
    {
        "language": "Marathi",
        "question": "उद्या मुंबईत तापमान किती असेल?"
    },

    # ---------------- ASSAMESE ----------------
    {
        "language": "Assamese",
        "question": "কাইলৈ গুৱাহাটীত বৰষুণ হ'ব নেকি?"
    },
    {
        "language": "Assamese",
        "question": "এতিয়া গুৱাহাটীৰ বতৰ কেনেকুৱা?"
    },
    {
        "language": "Assamese",
        "question": "কাইলৈ গুৱাহাটীৰ উষ্ণতা কিমান হ'ব?"
    },

    # ---------------- NEPALI ----------------
    {
        "language": "Nepali",
        "question": "भोलि काठमाडौंमा पानी पर्ला?"
    },
    {
        "language": "Nepali",
        "question": "अहिले काठमाडौंको मौसम कस्तो छ?"
    },
    {
        "language": "Nepali",
        "question": "भोलि काठमाडौंको तापक्रम कति हुनेछ?"
    },
]


# ============================================================
# RUN TESTS
# ============================================================

def run_tests():

    total = len(TEST_CASES)
    passed = 0

    print("=" * 70)
    print("        WEATHERGPT MULTILINGUAL ANALYZER TEST")
    print("=" * 70)

    for index, test in enumerate(TEST_CASES, start=1):

        question = test["question"]
        expected_language = test["language"]

        print(f"\n{'-' * 70}")
        print(f"TEST {index}/{total}")
        print(f"Expected Language : {expected_language}")
        print(f"Question          : {question}")
        print("-" * 70)

        try:

            result = analyze_question(question)

            detected_language = result.get("language")
            intent = result.get("intent")
            location = result.get("location")
            time = result.get("time")
            parameters = result.get("parameters", [])
            answer = result.get("answer", "")

            tool = select_tool(result)

            language_ok = detected_language == expected_language

            if language_ok:
                passed += 1
                status = "PASS"
            else:
                status = "CHECK"

            print(f"Status            : {status}")
            print(f"Detected Language : {detected_language}")
            print(f"Intent            : {intent}")
            print(f"Location          : {location}")
            print(f"Time              : {time}")
            print(f"Parameters        : {parameters}")
            print(f"Selected Tool     : {tool}")
            print(f"Answer            : {answer}")

        except Exception as e:

            print("Status            : ERROR")
            print(f"Error             : {e}")

    print("\n")
    print("=" * 70)
    print("                 TEST SUMMARY")
    print("=" * 70)

    print(f"Total Tests       : {total}")
    print(f"Language Passed   : {passed}")
    print(f"Language Failed   : {total - passed}")

    percentage = (passed / total) * 100

    print(f"Accuracy          : {percentage:.2f}%")

    if passed == total:
        print("\n🎉 ALL LANGUAGE DETECTION TESTS PASSED!")
    else:
        print("\n⚠️ Some languages need improvement.")

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    run_tests()