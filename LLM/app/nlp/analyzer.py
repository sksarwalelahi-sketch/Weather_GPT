import re


# =========================================================
# WEATHERGPT QUERY ANALYZER
# Deterministic Multilingual Analyzer
# =========================================================


SUPPORTED_LANGUAGES = [
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
    "Malayalam",
    "Assamese",
    "Urdu",
    "Nepali",
]

LLM_INTENTS = {
    "current_weather",
    "forecast",
    "alerts",
    "flood",
    "climate",
    "agriculture",
    "aviation",
    "marine",
    "knowledge",
    "location",
}


def get_llm_fallback(question: str) -> dict | None:
    """Use the existing Llama intent detector only for ambiguous queries."""

    try:
        from app.tools.intent_detector import detect_intent as llm_detect_intent

        result = llm_detect_intent(question)

    except Exception:
        return None

    if not isinstance(result, dict):
        return None

    intent = result.get("intent")

    if intent == "weather":
        intent = "current_weather"

    elif intent == "alert":
        intent = "alerts"

    elif intent in {"flooding", "flood_risk"}:
        intent = "flood"

    if intent not in LLM_INTENTS:
        return None

    location = result.get("location")

    if not isinstance(location, str):
        location = None

    parameters = result.get("parameters", [])

    if not isinstance(parameters, list):
        parameters = []

    return {
        "intent": intent,
        "location": normalize_location(location),
        "time": result.get("time"),
        "parameters": parameters,
    }


def needs_llm_fallback(
    question: str,
    intent: str,
) -> bool:
    """Identify questions that the rule classifier cannot safely classify."""

    if intent == "general_weather":
        return True

    text = question.lower()

    knowledge_markers = [
        "why ",
        "how does",
        "how do",
        "what causes",
        "explain ",
        "meaning of",
        "difference between",
    ]

    return any(marker in text for marker in knowledge_markers)


# =========================================================
# CITY / LOCATION DATABASE
# =========================================================

LOCATION_ALIASES = {

    # -----------------------------------------------------
    # English / Roman
    # -----------------------------------------------------

    "new delhi": "Delhi",
    "delhi": "Delhi",

    "mumbai": "Mumbai",
    "bombay": "Mumbai",

    "kolkata": "Kolkata",
    "calcutta": "Kolkata",

    "ranchi": "Ranchi",

    "bhubaneswar": "Bhubaneswar",
    "bhubaneshwar": "Bhubaneswar",
    "bhubanesar": "Bhubaneswar",

    "cuttack": "Cuttack",

    "chennai": "Chennai",
    "madras": "Chennai",

    "hyderabad": "Hyderabad",

    "bengaluru": "Bengaluru",
    "bangalore": "Bengaluru",

    "pune": "Pune",
    "jaipur": "Jaipur",
    "lucknow": "Lucknow",
    "patna": "Patna",
    "ahmedabad": "Ahmedabad",
    "surat": "Surat",
    "nagpur": "Nagpur",
    "indore": "Indore",
    "bhopal": "Bhopal",
    "guwahati": "Guwahati",
    "kathmandu": "Kathmandu",
    "srinagar": "Srinagar",
    "noida": "Noida",
    "gurgaon": "Gurugram",
    "gurugram": "Gurugram",
    "visakhapatnam": "Visakhapatnam",
    "vizag": "Visakhapatnam",
    "chandaka": "Chandaka",
    "puri": "Puri",
    "sambalpur": "Sambalpur",
    "balasore": "Balasore",
    "rourkela": "Rourkela",
    "berhampur": "Berhampur",

    # -----------------------------------------------------
    # Hindi / Devanagari
    # -----------------------------------------------------

    "दिल्ली": "Delhi",
    "मुंबई": "Mumbai",
    "बंबई": "Mumbai",
    "कोलकाता": "Kolkata",
    "रांची": "Ranchi",
    "भुवनेश्वर": "Bhubaneswar",
    "कटक": "Cuttack",
    "चेन्नई": "Chennai",
    "हैदराबाद": "Hyderabad",
    "बेंगलुरु": "Bengaluru",
    "बेंगलूरु": "Bengaluru",
    "पुणे": "Pune",
    "जयपुर": "Jaipur",
    "लखनऊ": "Lucknow",
    "पटना": "Patna",
    "अहमदाबाद": "Ahmedabad",
    "गुवाहाटी": "Guwahati",

    # -----------------------------------------------------
    # Odia
    # -----------------------------------------------------

    "ଭୁବନେଶ୍ୱର": "Bhubaneswar",
    "ଚନ୍ଦକା": "Chandaka",
    "ପୁରୀ": "Puri",
    "ସମ୍ବଲପୁର": "Sambalpur",
    "ବାଲେଶ୍ୱର": "Balasore",
    "ରାଉରକେଲା": "Rourkela",
    "ବ୍ରହ୍ମପୁର": "Berhampur",
    "ଦିଲ୍ଲୀ": "Delhi",
    "ମୁମ୍ବାଇ": "Mumbai",
    "କୋଲକାତା": "Kolkata",
    "ରାଞ୍ଚି": "Ranchi",
    "କଟକ": "Cuttack",
    "ଚେନ୍ନାଇ": "Chennai",
    "ହାଇଦ୍ରାବାଦ": "Hyderabad",
    "ବେଙ୍ଗାଲୁରୁ": "Bengaluru",
    "ପୁଣେ": "Pune",

    # -----------------------------------------------------
    # Bengali
    # -----------------------------------------------------

    "দিল্লি": "Delhi",
    "মুম্বাই": "Mumbai",
    "কলকাতা": "Kolkata",
    "রাঁচি": "Ranchi",
    "ভুবনেশ্বর": "Bhubaneswar",
    "কটক": "Cuttack",
    "চেন্নাই": "Chennai",
    "হায়দ্রাবাদ": "Hyderabad",
    "পুনে": "Pune",
    "গুয়াহাটি": "Guwahati",

    # -----------------------------------------------------
    # Gujarati
    # -----------------------------------------------------

    "દિલ્હી": "Delhi",
    "મુંબઈ": "Mumbai",
    "કોલકાતા": "Kolkata",
    "રાંચી": "Ranchi",
    "ભુવનેશ્વર": "Bhubaneswar",
    "કટક": "Cuttack",
    "ચેન્નાઈ": "Chennai",
    "હૈદરાબાદ": "Hyderabad",
    "પુણે": "Pune",
    "અમદાવાદ": "Ahmedabad",

    # -----------------------------------------------------
    # Marathi
    # -----------------------------------------------------

    "दिल्ली": "Delhi",
    "मुंबई": "Mumbai",
    "कोलकाता": "Kolkata",
    "रांची": "Ranchi",
    "भुवनेश्वर": "Bhubaneswar",
    "पुणे": "Pune",
    "अहमदाबाद": "Ahmedabad",

    # -----------------------------------------------------
    # Punjabi
    # -----------------------------------------------------

    "ਦਿੱਲੀ": "Delhi",
    "ਮੁੰਬਈ": "Mumbai",
    "ਕੋਲਕਾਤਾ": "Kolkata",
    "ਰਾਂਚੀ": "Ranchi",
    "ਭੁਵਨੇਸ਼ਵਰ": "Bhubaneswar",
    "ਚੰਡੀਗੜ੍ਹ": "Chandigarh",
    "ਅੰਮ੍ਰਿਤਸਰ": "Amritsar",

    # -----------------------------------------------------
    # Tamil
    # -----------------------------------------------------

    "டெல்லி": "Delhi",
    "மும்பை": "Mumbai",
    "கொல்கத்தா": "Kolkata",
    "சென்னை": "Chennai",
    "ஹைதராபாத்": "Hyderabad",
    "பெங்களூரு": "Bengaluru",
    "புனே": "Pune",

    # -----------------------------------------------------
    # Telugu
    # -----------------------------------------------------

    "ఢిల్లీ": "Delhi",
    "ముంబై": "Mumbai",
    "కోల్‌కతా": "Kolkata",
    "చెన్నై": "Chennai",
    "హైదరాబాద్": "Hyderabad",
    "బెంగళూరు": "Bengaluru",
    "పుణె": "Pune",

    # -----------------------------------------------------
    # Kannada
    # -----------------------------------------------------

    "ದೆಹಲಿ": "Delhi",
    "ಮುಂಬೈ": "Mumbai",
    "ಕೋಲ್ಕತ್ತಾ": "Kolkata",
    "ಚೆನ್ನೈ": "Chennai",
    "ಹೈದರಾಬಾದ್": "Hyderabad",
    "ಬೆಂಗಳೂರು": "Bengaluru",
    "ಪುಣೆ": "Pune",

    # -----------------------------------------------------
    # Malayalam
    # -----------------------------------------------------

    "ഡൽഹി": "Delhi",
    "മുംബൈ": "Mumbai",
    "കൊൽക്കത്ത": "Kolkata",
    "ചെന്നൈ": "Chennai",
    "ഹൈദരാബാദ്": "Hyderabad",
    "ബെംഗളൂരു": "Bengaluru",
    "പൂനെ": "Pune",

    # -----------------------------------------------------
    # Assamese
    # -----------------------------------------------------

    "দিল্লী": "Delhi",
    "মুম্বাই": "Mumbai",
    "কলকাতা": "Kolkata",
    "গুৱাহাটী": "Guwahati",

    # -----------------------------------------------------
    # Urdu
    # -----------------------------------------------------

    "دہلی": "Delhi",
    "ممبئی": "Mumbai",
    "کولکاتا": "Kolkata",
    "رانچی": "Ranchi",
    "بھوبنیشور": "Bhubaneswar",
    "چنئی": "Chennai",
    "حیدرآباد": "Hyderabad",
    "پونے": "Pune",

    # -----------------------------------------------------
    # Nepali
    # -----------------------------------------------------

    "काठमाडौं": "Kathmandu",
    "काठमाडौँ": "Kathmandu",
}


# =========================================================
# SCRIPT DETECTION
# =========================================================

def detect_script_language(text: str):

    # Bengali / Assamese
    if any("\u0980" <= c <= "\u09FF" for c in text):
        return "Bengali"

    # Punjabi
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

    # Devanagari
    if any("\u0900" <= c <= "\u097F" for c in text):
        return "Devanagari"

    # Urdu / Arabic
    if any("\u0600" <= c <= "\u06FF" for c in text):
        return "Urdu"

    return None


# =========================================================
# LANGUAGE DETECTION
# =========================================================

def detect_language(question: str):

    text = question.strip()

    if not text:
        return "English"

    script = detect_script_language(text)

    # -----------------------------------------------------
    # Bengali / Assamese
    # -----------------------------------------------------

    if script == "Bengali":

        assamese_markers = [
            "কাইলৈ",
            "এতিয়া",
            "বতৰ",
            "বৰষুণ",
            "গুৱাহাট",
            "উষ্ণতা",
            "হ'ব",
            "কিমান",
        ]

        if any(word in text for word in assamese_markers):
            return "Assamese"

        return "Bengali"

    # -----------------------------------------------------
    # Urdu
    # -----------------------------------------------------

    if script == "Urdu":
        return "Urdu"

    # -----------------------------------------------------
    # Unique scripts
    # -----------------------------------------------------

    if script in [
        "Punjabi",
        "Gujarati",
        "Odia",
        "Tamil",
        "Telugu",
        "Kannada",
        "Malayalam",
    ]:
        return script

    # -----------------------------------------------------
    # Devanagari
    # Hindi / Marathi / Nepali
    # -----------------------------------------------------

    if script == "Devanagari":

        # IMPORTANT:
        # Do not use generic substring "मा" for Nepali.
        # It incorrectly matches Hindi words such as तापमान.

        strong_nepali_markers = [
            "भोलि",
            "अहिले",
            "काठमाडौं",
            "काठमाडौँ",
            "कस्तो",
            "पर्ला",
            "तापक्रम",
            "हुनेछ",
        ]

        strong_marathi_markers = [
            "उद्या",
            "आत्ता",
            "मुंबईत",
            "पाऊस",
            "हवामान",
            "असेल",
            "पडेल",
            "किती",
            "मध्ये",
            "चे",
            "चा",
            "ची",
            "चे",
        ]

        if any(
            word in text
            for word in strong_nepali_markers
        ):
            return "Nepali"

        if any(
            word in text
            for word in strong_marathi_markers
        ):
            return "Marathi"

        return "Hindi"

    # -----------------------------------------------------
    # Roman English / Hinglish
    # -----------------------------------------------------

    words = set(
        re.findall(
            r"[a-zA-Z]+",
            text.lower()
        )
    )

    hindi_words = {
        "kya",
        "kal",
        "aaj",
        "abhi",
        "baarish",
        "barish",
        "paani",
        "pani",
        "mausam",
        "mein",
        "ka",
        "ki",
        "ke",
        "ko",
        "hai",
        "hoga",
        "hogi",
        "honge",
        "kaisa",
        "kaisi",
        "kaise",
        "kitna",
        "kitni",
        "batao",
        "mujhe",
        "mera",
        "meri",
        "mere",
        "wala",
        "wali",
        "wale",
        "raha",
        "rahi",
        "rahe",
        "hona",
        "chahiye",
        "tez",
        "garmi",
        "thand",
        "hawa",
        "par",
        "se",
        "liye",
    }

    english_words = {
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
        "is",
        "are",
        "was",
        "were",
        "have",
        "has",
        "had",
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "if",
        "to",
        "from",
        "for",
        "with",
        "about",
        "weather",
        "rain",
        "rainfall",
        "storm",
        "wind",
        "temperature",
        "forecast",
        "today",
        "tomorrow",
        "yesterday",
        "humidity",
        "current",
        "heavy",
        "receive",
        "received",
        "trend",
        "changed",
        "change",
        "average",
        "last",
        "month",
        "year",
        "week",
        "in",
        "there",
        "be",
        "expected",
    }

    hindi_score = sum(
        1
        for word in words
        if word in hindi_words
    )

    english_score = sum(
        1
        for word in words
        if word in english_words
    )

    if (
        hindi_score > 0
        and english_score > 0
    ):
        return "Hinglish"

    if hindi_score > english_score:
        return "Hinglish"

    return "English"


# =========================================================
# LOCATION DETECTION
# =========================================================

def detect_location(question: str):

    text = question.strip()
    text_lower = text.lower()

    aliases = sorted(
        LOCATION_ALIASES.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for alias, city in aliases:

        # Roman / English
        if re.fullmatch(
            r"[a-zA-Z0-9 ]+",
            alias
        ):

            pattern = (
                r"(?<![a-zA-Z])"
                + re.escape(alias.lower())
                + r"(?![a-zA-Z])"
            )

            if re.search(
                pattern,
                text_lower
            ):
                return city

        # Indian scripts
        else:

            if alias in text:
                return city

    return None


# =========================================================
# TIME DETECTION
# =========================================================

def detect_time_from_question(question: str):

    text = question.strip().lower()

    # -----------------------------------------------------
    # NEXT WEEK
    # -----------------------------------------------------

    next_week_words = [
        "next week",
        "next_week",
        "अगले सप्ताह",
        "अगले हफ्ते",
        "पुढच्या आठवड्यात",
        "पुढील आठवड्यात",
        "परच्या आठवड्यात",
        "পরের সপ্তাহ",
        "આવતા અઠવાડિયે",
        "ਅਗਲੇ ਹਫ਼ਤੇ",
    ]

    if any(
        word in text
        for word in next_week_words
    ):
        return "next_week"

    # -----------------------------------------------------
    # LAST MONTH
    # -----------------------------------------------------

    last_month_words = [
        "last month",
        "पिछले महीने",
        "मागील महिन्यात",
        "गेल्या महिन्यात",
    ]

    if any(
        word in text
        for word in last_month_words
    ):
        return "last_month"

    # -----------------------------------------------------
    # LAST YEAR
    # -----------------------------------------------------

    last_year_words = [
        "last year",
        "पिछले साल",
        "पिछले वर्ष",
        "मागील वर्षी",
        "गेल्या वर्षी",
    ]

    if any(
        word in text
        for word in last_year_words
    ):
        return "last_year"

    # -----------------------------------------------------
    # TOMORROW
    # -----------------------------------------------------

    if re.search(
        r"\bkal\b",
        text
    ):
        return "tomorrow"

    tomorrow_words = [
        "tomorrow",
        "कल",
        "उद्या",
        "भोलि",
        "আগামীকাল",
        "কাল",
        "কালকে",
        "કાલે",
        "કાલ",
        "ଆସନ୍ତାକାଲି",
        "କାଲି",
        "କାଲିକି",
        "நாளை",
        "நாளைக்கு",
        "రేపు",
        "రేపటికి",
        "ನಾಳೆ",
        "ನಾಳೆಗೆ",
        "നാളെത്തേക്ക്",
        "کل",
        "کلّ",
        "কাইলৈ",
        "ਕੱਲ੍ਹ",
        "ਭਲਕੇ",
    ]

    if any(
        word in text
        for word in tomorrow_words
    ):
        return "tomorrow"

    tonight_words = [
        "tonight",
        "this evening",
        "at night",
        "आज रात",
        "आज रात्री",
        "आज रात",
        "आज रात्रि",
        "আজ রাতে",
        "આજે રાત્રે",
        "ଆଜି ରାତି",
        "ଆଜି ରାତିରେ",
        "ଆଜି ସନ୍ଧ୍ୟାରେ",
        "ਅੱਜ ਰਾਤ",
        "آج رات",
    ]

    if any(word in text for word in tonight_words):
        return "tonight"

    # -----------------------------------------------------
    # TODAY
    # -----------------------------------------------------

    if re.search(
        r"\baaj\b",
        text
    ):
        return "today"

    today_words = [
        "today",
        "आज",
        "आजच",
        "আজ",
        "આજે",
        "ଆଜି",
        "ਅੱਜ",
        "آج",
        "இன்று",
        "இன்னைக்கு",
        "ఈ రోజు",
        "ఈరోజు",
        "ಇಂದು",
        "ഇന്ന്",
    ]

    if any(
        word in text
        for word in today_words
    ):
        return "today"

    # -----------------------------------------------------
    # NOW
    # -----------------------------------------------------

    now_words = [
        "now",
        "right now",
        "currently",
        "current",
        "अभी",
        "वर्तमान",
        "आत्ता",
        "अहिले",
        "এখন",
        "હમણાં",
        "ଏବେ",
        "ବର୍ତ୍ତମାନ",
        "ਹੁਣ",
        "ابھی",
        "இப்போது",
        "இப்போ",
        "ఇప్పుడు",
        "ಈಗ",
        "ഇപ്പോൾ",
    ]

    if any(
        word in text
        for word in now_words
    ):
        return "now"

    return "now"


# =========================================================
# PARAMETER DETECTION
# =========================================================

def detect_parameters(question: str):

    text = question.lower()

    parameters = []

    # -----------------------------------------------------
    # Temperature
    # -----------------------------------------------------

    temperature_words = [
        "temperature",
        "temp",

        # Hindi
        "तापमान",
        "तापक्रम",

        # Bengali
        "তাপমাত্রা",
        "উষ্ণতা",

        # Gujarati
        "તાપમાન",

        # Odia
        "ତାପମାତ୍ରା",

        # Urdu
        "درجہ حرارت",

        # Tamil
        "வெப்பநிலை",

        # Telugu
        "ఉష్ణోగ్రత",

        # Kannada
        "ತಾಪಮಾನ",
    ]

    if any(
        word in text
        for word in temperature_words
    ):
        parameters.append("temperature")

    # -----------------------------------------------------
    # Humidity
    # -----------------------------------------------------

    humidity_words = [
        "humidity",
        "आर्द्रता",
        "আর্দ্রতা",
        "ભેજ",
        "ଆର୍ଦ୍ରତା",
        "ਨਮੀ",
        "رطوبت",
    ]

    if any(
        word in text
        for word in humidity_words
    ):
        parameters.append("humidity")

    # -----------------------------------------------------
    # Rain
    # -----------------------------------------------------

    rain_words = [
        "rain",
        "rainfall",
        "precipitation",

        "बारिश",
        "वर्षा",
        "पानी",

        "पाऊस",

        "বৃষ্টি",

        "વરસાદ",

        "ବର୍ଷା",

        "ਮੀਂਹ",

        "বৰষুণ",

        "بارش",

        "पर्ला",

        "மழை",
        "వర్షం",
        "ಮಳೆ",
        "മഴ",
    ]

    if any(
        word in text
        for word in rain_words
    ):
        parameters.append("rainfall")
        parameters.append("weather_condition")

    # -----------------------------------------------------
    # Wind
    # -----------------------------------------------------

    wind_words = [
        "wind",
        "wind speed",
        "हवा",
        "वारा",
        "वाऱ्याचा",
        "বাতাস",
        "પવન",
        "ପବନ",
        "ਹਵਾ",
        "ہوا",
    ]

    if any(
        word in text
        for word in wind_words
    ):
        parameters.append("wind_speed")

    # -----------------------------------------------------
    # Visibility
    # -----------------------------------------------------

    visibility_words = [
        "visibility",
        "दृश्यता",
        "दृश्यमानता",
        "দৃশ্যমানতা",
    ]

    if any(
        word in text
        for word in visibility_words
    ):
        parameters.append("visibility")

    # -----------------------------------------------------
    # Pressure
    # -----------------------------------------------------

    pressure_words = [
        "pressure",
        "दबाव",
        "दाब",
        "ચાપ",
        "ଦାବ",
    ]

    if any(
        word in text
        for word in pressure_words
    ):
        parameters.append("pressure")

    # -----------------------------------------------------
    # Weather condition
    # -----------------------------------------------------

    weather_words = [
        "weather",
        "condition",

        "मौसम",
        "हवामान",

        "पानीपाग",
        "पाणिपाग",

        "আবহাওয়া",

        "હવામાન",

        "ପାଣିପାଗ",

        "ਬੱਦਲ",

        "موسم",
    ]

    if any(
        word in text
        for word in weather_words
    ):
        parameters.append("weather_condition")

    # Remove duplicates
    parameters = list(
        dict.fromkeys(parameters)
    )

    if not parameters:
        parameters = [
            "weather_condition"
        ]

    return parameters


# =========================================================
# CLIMATE DETECTION
# =========================================================

def is_climate_question(question: str):

    text = question.lower()

    climate_words = [

        # General climate
        "climate",
        "historical",
        "history",
        "historically",

        # Trends
        "trend",
        "trends",
        "rainfall trend",
        "temperature trend",
        "humidity trend",

        # Average
        "average temperature",
        "average rainfall",
        "average humidity",
        "average weather",

        # Historical periods
        "last month",
        "last year",
        "over time",

        # Historical observation
        "received",
        "receive",
        "recorded",
        "record",

        # Change
        "changed",
        "change",
        "changing",
        "temperature changed",
        "rainfall changed",
        "temperature change",
        "rainfall change",

        # Hindi
        "ऐतिहासिक",
        "इतिहास",
        "रुझान",
        "बदलाव",
        "पिछले महीने",
        "पिछले साल",

        # Marathi
        "मागील महिन्यात",
        "मागील वर्षी",
    ]

    # IMPORTANT:
    # Do NOT include "कल", "आज", "उद्या", etc.
    # They are time indicators, not climate indicators.

    return any(
        word in text
        for word in climate_words
    )


# =========================================================
# FUTURE DETECTION
# =========================================================

def is_future_question(
    question: str,
    time_value: str
):

    text = question.lower()

    if time_value in [
        "tomorrow",
        "tonight",
        "next_week",
    ]:
        return True

    future_words = [
        "tomorrow",
        "next week",
        "will",
        "going to",
        "later",
        "tonight",
        "this evening",

        # Hindi
        "कल",
        "अगले सप्ताह",
        "अगले हफ्ते",

        # Marathi
        "उद्या",
        "पुढच्या आठवड्यात",
        "पुढील आठवड्यात",

        # Nepali
        "भोलि",

        # Bengali
        "আগামীকাল",
        "কাল",
        "কালকে",

        # Gujarati
        "કાલે",
        "કાલ",

        # Odia
        "ଆସନ୍ତାକାଲି",
        "କାଲି",
        "କାଲିକି",
        "ଭବିଷ୍ୟତ",

        # Tamil
        "நாளை",
        "நாளைக்கு",

        # Telugu
        "రేపు",
        "రేపటికి",

        # Kannada
        "ನಾಳೆ",
        "ನಾಳೆಗೆ",

        # Malayalam
        "നാളെ",
        "നാളെത്തേക്ക്",

        # Assamese
        "কাইলৈ",

        # Punjabi
        "ਕੱਲ੍ਹ",
        "ਭਲਕੇ",

        # Urdu
        "کل",
    ]

    if re.search(
        r"\bkal\b",
        text
    ):
        return True

    if any(
        word in text
        for word in future_words
    ):
        return True

    return False


# =========================================================
# INTENT DETECTION
# =========================================================

def detect_intent(
    question: str,
    time_value: str,
    parameters: list,
):

    text = question.lower()

    # -----------------------------------------------------
    # Climate
    # -----------------------------------------------------

    if is_climate_question(question):
        return "climate"

    # -----------------------------------------------------
    # Flood-source data
    # -----------------------------------------------------

    flood_words = [
        "flood",
        "flooding",
        "flash flood",
        "बाढ़",
        "ବନ୍ୟା",
    ]

    if any(word in text for word in flood_words):
        return "flood"

    # -----------------------------------------------------
    # Alerts
    # -----------------------------------------------------

    alert_words = [
        "alert",
        "warning",
        "warnings",
        "danger",
        "hazard",
        "emergency",
        "चेतावनी",
        "सावधान",
        "इशारा",
    ]

    if any(
        word in text
        for word in alert_words
    ):
        return "alerts"

    # -----------------------------------------------------
    # Agriculture
    # -----------------------------------------------------

    agriculture_words = [
        "agriculture",
        "agriculture weather",
        "crop",
        "farming",
        "farmer",
        "irrigation",
        "फसल",
        "कृषि",
        "खेती",
    ]

    if any(
        word in text
        for word in agriculture_words
    ):
        return "agriculture"

    # -----------------------------------------------------
    # Aviation
    # -----------------------------------------------------

    aviation_words = [
        "aviation",
        "flight",
        "airport",
        "aircraft",
        "pilot",
    ]

    if any(
        word in text
        for word in aviation_words
    ):
        return "aviation"

    # -----------------------------------------------------
    # Marine
    # -----------------------------------------------------

    marine_words = [
        "marine",
        "sea",
        "ocean",
        "wave",
        "waves",
        "coastal",
        "समुद्र",
        "लहर",
    ]

    if any(
        word in text
        for word in marine_words
    ):
        return "marine"

    # -----------------------------------------------------
    # Forecast
    # -----------------------------------------------------

    if is_future_question(
        question,
        time_value
    ):
        return "forecast"

    # -----------------------------------------------------
    # TODAY + RAIN
    # -----------------------------------------------------

    # A question such as:
    # "ଆଜି କଟକରେ ବର୍ଷା ହେବ କି?"
    #
    # asks whether rain will occur today,
    # therefore forecast data is more appropriate.

    if time_value == "today":

        future_weather_words = [
            "rain",
            "rainfall",
            "precipitation",

            "बारिश",
            "वर्षा",
            "पानी",

            "पाऊस",

            "বৃষ্টি",

            "વરસાદ",

            "ବର୍ଷା",

            "ਮੀਂਹ",

            "বৰষুণ",

            "بارش",
        ]

        if any(
            word in text
            for word in future_weather_words
        ):
            return "forecast"

        return "current_weather"

    # -----------------------------------------------------
    # Current-specific parameters
    # -----------------------------------------------------

    current_parameter_list = [
        "temperature",
        "humidity",
        "wind_speed",
        "wind_direction",
        "visibility",
        "pressure",
    ]

    if any(
        parameter in parameters
        for parameter in current_parameter_list
    ):

        if time_value in [
            "last_month",
            "last_year",
            "historical",
        ]:
            return "climate"

        return "current_weather"

    # -----------------------------------------------------
    # Explicit current weather
    # -----------------------------------------------------

    current_words = [
        "current weather",
        "current",
        "right now",
        "now",
        "currently",

        "अभी",
        "वर्तमान",

        "आत्ता",

        "अहिले",

        "এখন",

        "હમણાં",

        "ଏବେ",

        "ਹੁਣ",

        "ابھی",
    ]

    if any(
        word in text
        for word in current_words
    ):
        return "current_weather"

    # -----------------------------------------------------
    # Generic weather
    # -----------------------------------------------------

    if "weather_condition" in parameters:
        return "current_weather"

    return "general_weather"


# =========================================================
# TOOL SELECTION
# =========================================================

def select_tool(intent: str):

    tool_map = {

        "current_weather":
            "get_current_weather",

        "forecast":
            "get_forecast",

        "alerts":
            "get_weather_alerts",

        "flood":
            "get_flood_data",

        "climate":
            "climate_analysis",

        "agriculture":
            "agriculture_weather",

        "aviation":
            "aviation_weather",

        "marine":
            "marine_weather",

        "general_weather":
            "get_current_weather",
    }

    return tool_map.get(
        intent,
        "get_current_weather"
    )


# =========================================================
# NORMALIZE LOCATION
# =========================================================

def normalize_location(location):

    if not location:
        return None

    location = location.strip()

    return LOCATION_ALIASES.get(
        location,
        location
    )


# =========================================================
# NORMALIZE TIME
# =========================================================

def normalize_time(time_value):

    if not time_value:
        return "now"

    mapping = {

        "कल": "tomorrow",
        "उद्या": "tomorrow",
        "भोलि": "tomorrow",
        "আগামীকাল": "tomorrow",
        "કાલે": "tomorrow",
        "ଆସନ୍ତାକାଲି": "tomorrow",
        "କାଲି": "tomorrow",
        "କାଲିକି": "tomorrow",
        "কাল": "tomorrow",
        "কালকে": "tomorrow",
        "કાલ": "tomorrow",
        "நாளை": "tomorrow",
        "நாளைக்கு": "tomorrow",
        "రేపు": "tomorrow",
        "రేపటికి": "tomorrow",
        "ನಾಳೆ": "tomorrow",
        "ನಾಳೆಗೆ": "tomorrow",
        "നാളെ": "tomorrow",
        "നാളെത്തേക്ക്": "tomorrow",
        "کل": "tomorrow",
        "কাইলৈ": "tomorrow",
        "ਕੱਲ੍ਹ": "tomorrow",
        "ਭਲਕੇ": "tomorrow",

        "आज": "today",
        "आजच": "today",
        "aaj": "today",
        "আজ": "today",
        "આજે": "today",
        "ଆଜି": "today",
        "ਅੱਜ": "today",
        "آج": "today",
        "இன்று": "today",
        "இன்னைக்கு": "today",
        "ఈ రోజు": "today",
        "ఈరోజు": "today",
        "ಇಂದು": "today",
        "ഇന്ന്": "today",

        "अभी": "now",
        "वर्तमान": "now",
        "आत्ता": "now",
        "अहिले": "now",
        "এখন": "now",
        "હમણાં": "now",
        "ଏବେ": "now",
        "ବର୍ତ୍ତମାନ": "now",
        "ਹੁਣ": "now",
        "ابھی": "now",
        "இப்போது": "now",
        "இப்போ": "now",
        "இప్పుడు": "now",
        "ಈಗ": "now",
        "ഇപ്പോൾ": "now",
        "ଆଜି ରାତି": "tonight",
        "ଆଜି ରାତିରେ": "tonight",
        "ଆଜି ସନ୍ଧ୍ୟାରେ": "tonight",
        "আজ রাতে": "tonight",
        "આજે રાત્રે": "tonight",
        "आज रात": "tonight",
        "आज रात्री": "tonight",
        "আজ रात": "tonight",
        "tonight": "tonight",
        "this evening": "tonight",
    }

    return mapping.get(
        time_value,
        time_value
    )


# =========================================================
# ANALYZE QUESTION
# =========================================================

def analyze_question(question: str):

    if not isinstance(
        question,
        str
    ):
        raise ValueError(
            "Question must be a string."
        )

    question = question.strip()

    # -----------------------------------------------------
    # Empty question
    # -----------------------------------------------------

    if not question:

        return {
            "question": question,
            "language": "English",
            "intent": "general_weather",
            "location": None,
            "time": "now",
            "parameters": [
                "weather_condition"
            ],
            "suggested_tool":
                "get_current_weather",
            "answer": None,
        }

    # -----------------------------------------------------
    # 1. Language
    # -----------------------------------------------------

    language = detect_language(
        question
    )

    # -----------------------------------------------------
    # 2. Location
    # -----------------------------------------------------

    location = detect_location(
        question
    )

    location = normalize_location(
        location
    )

    # -----------------------------------------------------
    # 3. Time
    # -----------------------------------------------------

    time_value = detect_time_from_question(
        question
    )

    time_value = normalize_time(
        time_value
    )

    # -----------------------------------------------------
    # 4. Parameters
    # -----------------------------------------------------

    parameters = detect_parameters(
        question
    )

    # -----------------------------------------------------
    # 5. Intent
    # -----------------------------------------------------

    intent = detect_intent(
        question,
        time_value,
        parameters
    )

    # The rules cover known languages and common weather phrasing.
    # Llama is used only when they cannot classify the request.
    analysis_source = "rules"

    if needs_llm_fallback(question, intent):
        llm_result = get_llm_fallback(question)

        if llm_result is not None:
            intent = llm_result["intent"]
            analysis_source = "rules+llm"

            if llm_result["location"] is not None:
                location = llm_result["location"]

            if llm_result["time"]:
                time_value = normalize_time(llm_result["time"])

            if llm_result["parameters"]:
                parameters = llm_result["parameters"]

    # -----------------------------------------------------
    # 6. Tool
    # -----------------------------------------------------

    suggested_tool = select_tool(
        intent
    )

    # -----------------------------------------------------
    # Safety correction
    # -----------------------------------------------------

    if intent == "climate":

        suggested_tool = (
            "climate_analysis"
        )

    elif intent == "forecast":

        suggested_tool = (
            "get_forecast"
        )

    elif intent == "current_weather":

        suggested_tool = (
            "get_current_weather"
        )

    # -----------------------------------------------------
    # Final result
    # -----------------------------------------------------

    return {
        "question": question,
        "language": language,
        "intent": intent,
        "location": location,
        "time": time_value,
        "parameters": parameters,
        "suggested_tool": suggested_tool,
        "analysis_source": analysis_source,
        "answer": None,
    }


# =========================================================
# PRINT RESULT
# =========================================================

def print_result(result):

    print("\n======================================")
    print("       WEATHERGPT QUERY ANALYZER")
    print("======================================")

    print("\nQuestion:")
    print(result.get("question"))

    print("\nLanguage:")
    print(result.get("language"))

    print("\nIntent:")
    print(result.get("intent"))

    print("\nLocation:")
    print(result.get("location"))

    print("\nTime:")
    print(result.get("time"))

    print("\nParameters:")
    print(result.get("parameters"))

    print("\nSuggested Tool:")
    print(result.get("suggested_tool"))

    print("\nAnswer:")
    print(result.get("answer"))

    print("--------------------------------------")


# =========================================================
# MAIN TEST
# =========================================================

if __name__ == "__main__":

    test_questions = [

        # =================================================
        # English
        # =================================================

        "Will it rain tomorrow in Delhi?",

        "What is the current weather in Mumbai?",

        "What is the humidity in Kolkata?",

        "What will the temperature be tomorrow in Mumbai?",

        "Is there heavy rain tomorrow in Chennai?",

        # =================================================
        # Hinglish
        # =================================================

        "Kya kal Mumbai mein baarish hogi?",

        "Abhi Ranchi ka weather kaisa hai?",

        "Aaj Pune mein temperature kitna hai?",

        # =================================================
        # Hindi
        # =================================================

        "कल दिल्ली में बारिश होगी?",

        "अभी दिल्ली का मौसम कैसा है?",

        "अगले सप्ताह मुंबई का मौसम कैसा रहेगा?",

        "कल मुंबई का तापमान कितना होगा?",

        # =================================================
        # Odia
        # =================================================

        "ଆସନ୍ତାକାଲି ଭୁବନେଶ୍ୱରରେ ବର୍ଷା ହେବ କି?",

        "ଆଜି କଟକରେ ବର୍ଷା ହେବ କି?",

        "ଏବେ ଭୁବନେଶ୍ୱରର ପାଣିପାଗ କେମିତି ଅଛି?",

        # =================================================
        # Marathi
        # =================================================

        "आत्ता मुंबईचे हवामान कसे आहे?",

        "उद्या मुंबईत पाऊस पडेल का?",

        "उद्या मुंबईत तापमान किती असेल?",

        # =================================================
        # Nepali
        # =================================================

        "भोलि काठमाडौंमा पानी पर्ला?",

        "अहिले काठमाडौंको मौसम कस्तो छ?",

        "भोलि काठमाडौंको तापक्रम कति हुनेछ?",

        # =================================================
        # Climate
        # =================================================

        "What was the average temperature in Delhi last month?",

        "How much rainfall did Mumbai receive?",

        "What is the rainfall trend in Kolkata?",

        "How has temperature changed in Bhubaneswar?",

        "What was the average temperature in Delhi last year?",
    ]

    for question in test_questions:

        result = analyze_question(
            question
        )

        print_result(result)
