from app.response.weather_interpreter import interpret_weather


# =========================================================
# UTILITY
# =========================================================

def format_number(value):
    """Keep integers clean and avoid unnecessary decimals."""
    if value is None:
        return None
    try:
        value = float(value)
        if value.is_integer():
            return str(int(value))
        return str(round(value, 1))
    except (TypeError, ValueError):
        return str(value)


# =========================================================
# RAIN ANSWER
# =========================================================

def generate_rain_answer(
    language,
    location,
    probability,
    rainfall,
    heavy_rain
):
    """Generate deterministic rain response."""

    probability_text = format_number(probability)
    rainfall_text = format_number(rainfall)

    # Check if rain is unlikely (probability < 30% and rainfall <= 0.5 mm)
    is_rain_unlikely = False
    try:
        p_val = float(probability) if probability is not None else None
        r_val = float(rainfall) if rainfall is not None else None
        if not heavy_rain:
            if p_val is not None and p_val < 30 and (r_val is None or r_val <= 0.5):
                is_rain_unlikely = True
            elif p_val is None and r_val is not None and r_val <= 0.0:
                is_rain_unlikely = True
    except (TypeError, ValueError):
        pass

    # -----------------------------------------------------
    # ENGLISH
    # -----------------------------------------------------
    if language == "English":
        if is_rain_unlikely:
            if probability_text is not None:
                return f"Rain is unlikely in {location}. The chance of rain is {probability_text}%."
            return f"Rain is not expected in {location}."
        if heavy_rain:
            if probability_text is not None:
                return f"Heavy rain is expected in {location}. There is a {probability_text}% chance of rain."
            return f"Heavy rain is expected in {location}."
        if probability_text is not None and rainfall_text is not None:
            return f"Rain is expected in {location} with a {probability_text}% chance. Expected rainfall is about {rainfall_text} mm."
        if probability_text is not None:
            return f"Rain is expected in {location} with a {probability_text}% chance."
        if rainfall_text is not None:
            return f"Rainfall of about {rainfall_text} mm is expected in {location}."
        return f"Rain information is available for {location}."

    # -----------------------------------------------------
    # HINDI
    # -----------------------------------------------------
    if language == "Hindi":
        if is_rain_unlikely:
            if probability_text is not None:
                return f"{location} में बारिश होने की संभावना बहुत कम है। बारिश की संभावना केवल {probability_text}% है।"
            return f"{location} में बारिश होने की संभावना नहीं है।"
        if heavy_rain:
            if probability_text is not None:
                return f"{location} में भारी बारिश होने की संभावना है। बारिश की संभावना {probability_text}% है।"
            return f"{location} में भारी बारिश होने की संभावना है।"
        if probability_text is not None and rainfall_text is not None:
            return f"{location} में बारिश होने की संभावना {probability_text}% है। लगभग {rainfall_text} मिमी बारिश हो सकती है।"
        if probability_text is not None:
            return f"{location} में बारिश होने की संभावना {probability_text}% है।"
        if rainfall_text is not None:
            return f"{location} में लगभग {rainfall_text} मिमी बारिश हो सकती है।"
        return f"{location} के लिए बारिश की जानकारी उपलब्ध है।"

    # -----------------------------------------------------
    # HINGLISH
    # -----------------------------------------------------
    if language == "Hinglish":
        if is_rain_unlikely:
            if probability_text is not None:
                return f"{location} mein baarish hone ke chances kam hain. Rain probability sirf {probability_text}% hai."
            return f"{location} mein baarish expected nahi hai."
        if heavy_rain:
            if probability_text is not None:
                return f"{location} mein heavy baarish hone ki sambhavna hai. Rain probability {probability_text}% hai."
            return f"{location} mein heavy baarish hone ki sambhavna hai."
        if probability_text is not None and rainfall_text is not None:
            return f"{location} mein baarish hone ki sambhavna {probability_text}% hai. Lagbhag {rainfall_text} mm rainfall ho sakti hai."
        if probability_text is not None:
            return f"{location} mein baarish hone ki sambhavna {probability_text}% hai."
        if rainfall_text is not None:
            return f"{location} mein lagbhag {rainfall_text} mm rainfall ho sakti hai."
        return f"{location} ka rain information available hai."

    # -----------------------------------------------------
    # ODIA
    # -----------------------------------------------------
    if language == "Odia":
        if is_rain_unlikely:
            if probability_text is not None:
                return f"{location}ରେ ବର୍ଷା ହେବାର ସମ୍ଭାବନା ନାହିଁ। ବର୍ଷାର ସମ୍ଭାବନା ମାତ୍ର {probability_text}% ଅଛି।"
            return f"{location}ରେ ବର୍ଷା ହେବାର ସମ୍ଭାବନା ନାହିଁ।"
        if heavy_rain:
            if probability_text is not None:
                return f"{location}ରେ ପ୍ରବଳ ବର୍ଷା ହେବାର ସମ୍ଭାବନା ଅଛି। ବର୍ଷାର ସମ୍ଭାବନା {probability_text}% ଅଛି।"
            return f"{location}ରେ ପ୍ରବଳ ବର୍ଷା ହେବାର ସମ୍ଭାବନା ଅଛି।"
        if probability_text is not None and rainfall_text is not None:
            return f"{location}ରେ ବର୍ଷା ହେବାର ସମ୍ଭାବନା {probability_text}% ଅଛି। ପ୍ରାୟ {rainfall_text} ମିମି ବର୍ଷା ହୋଇପାରେ।"
        if probability_text is not None:
            return f"{location}ରେ ବର୍ଷା ହେବାର ସମ୍ଭାବନା {probability_text}% ଅଛି।"
        if rainfall_text is not None:
            return f"{location}ରେ ପ୍ରାୟ {rainfall_text} ମିମି ବର୍ଷା ହୋଇପାରେ।"
        return f"{location} ପାଇଁ ବର୍ଷା ସୂଚନା ଉପଲବ୍ଧ ଅଛି।"

    # -----------------------------------------------------
    # BENGALI
    # -----------------------------------------------------
    if language == "Bengali":
        if is_rain_unlikely:
            if probability_text is not None:
                return f"{location}-এ বৃষ্টির সম্ভাবনা খুব কম। বৃষ্টির সম্ভাবনা মাত্র {probability_text}%।"
            return f"{location}-এ বৃষ্টির সম্ভাবনা নেই।"
        if heavy_rain:
            return f"{location}-এ ভারী বৃষ্টির সম্ভাবনা রয়েছে।"
        if probability_text is not None and rainfall_text is not None:
            return f"{location}-এ বৃষ্টির সম্ভাবনা {probability_text}%। প্রায় {rainfall_text} মিমি বৃষ্টি হতে পারে।"
        if probability_text is not None:
            return f"{location}-এ বৃষ্টির সম্ভাবনা {probability_text}%।"
        return f"{location}-এর বৃষ্টির তথ্য পাওয়া গেছে।"

    # -----------------------------------------------------
    # GUJARATI
    # -----------------------------------------------------
    if language == "Gujarati":
        if is_rain_unlikely:
            if probability_text is not None:
                return f"{location} માં વરસાદની શક્યતા ઘણી ઓછી છે. વરસાદની શક્યતા માત્ર {probability_text}% છે."
            return f"{location} માં વરસાદની શક્યતા નથી."
        if heavy_rain:
            return f"{location} માં ભારે વરસાદની શક્યતા છે."
        if probability_text is not None:
            return f"{location} માં વરસાદની {probability_text}% શક્યતા છે."
        return f"{location} માટે વરસાદની માહિતી ઉપલબ્ધ છે."

    # -----------------------------------------------------
    # MARATHI
    # -----------------------------------------------------
    if language == "Marathi":
        if is_rain_unlikely:
            if probability_text is not None:
                return f"{location} मध्ये पावसाची शक्यता खूप कमी आहे. पावसाची शक्यता फक्त {probability_text}% आहे."
            return f"{location} मध्ये पावसाची शक्यता नाही."
        if heavy_rain:
            return f"{location} मध्ये मुसळधार पावसाची शक्यता आहे."
        if probability_text is not None:
            return f"{location} मध्ये पावसाची {probability_text}% शक्यता आहे."
        return f"{location} साठी पावसाची माहिती उपलब्ध आहे."

    # -----------------------------------------------------
    # PUNJABI
    # -----------------------------------------------------
    if language == "Punjabi":
        if is_rain_unlikely:
            if probability_text is not None:
                return f"{location} ਵਿੱਚ ਮੀਂਹ ਪੈਣ ਦੀ ਸੰਭਾਵਨਾ ਬਹੁਤ ਘੱਟ ਹੈ। ਮੀਂਹ ਦੀ ਸੰਭਾਵਨਾ ਸਿਰਫ਼ {probability_text}% ਹੈ।"
            return f"{location} ਵਿੱਚ ਮੀਂਹ ਪੈਣ ਦੀ ਸੰਭਾਵਨਾ ਨਹੀਂ ਹੈ।"
        if heavy_rain:
            return f"{location} ਵਿੱਚ ਭਾਰੀ ਮੀਂਹ ਦੀ ਸੰਭਾਵਨਾ ਹੈ।"
        if probability_text is not None:
            return f"{location} ਵਿੱਚ ਮੀਂਹ ਦੀ {probability_text}% ਸੰਭਾਵਨਾ ਹੈ।"
        return f"{location} ਲਈ ਮੀਂਹ ਦੀ ਜਾਣਕਾਰੀ ਉਪਲਬਧ ਹੈ।"

    # -----------------------------------------------------
    # TAMIL
    # -----------------------------------------------------
    if language == "Tamil":
        if is_rain_unlikely:
            if probability_text is not None:
                return f"{location} பகுதியில் மழை பெய்ய வாய்ப்பு குறைவு. மழைக்கான வாய்ப்பு {probability_text}% மட்டுமே."
            return f"{location} பகுதியில் மழை பெய்ய வாய்ப்பில்லை."
        if heavy_rain:
            return f"{location} பகுதியில் கனமழைக்கு வாய்ப்பு உள்ளது."
        if probability_text is not None:
            return f"{location} பகுதியில் மழைக்கு {probability_text}% வாய்ப்பு உள்ளது."
        return f"{location} வானிலை தகவல் கிடைக்கிறது."

    # -----------------------------------------------------
    # TELUGU
    # -----------------------------------------------------
    if language == "Telugu":
        if is_rain_unlikely:
            if probability_text is not None:
                return f"{location}లో వర్షం పడే అవకాశం చాలా తక్కువ. వర్ష సూచన కేవలం {probability_text}% మాత్రమే."
            return f"{location}లో వర్షం పడే అవకాశం లేదు."
        if heavy_rain:
            return f"{location}లో భారీ వర్షాలు కురిసే అవకాశం ఉంది."
        if probability_text is not None:
            return f"{location}లో వర్షం పడే అవకాశం {probability_text}% ఉంది."
        return f"{location} వాతావరణ సమాచారం అందుబాటులో ఉంది."

    # -----------------------------------------------------
    # KANNADA
    # -----------------------------------------------------
    if language == "Kannada":
        if is_rain_unlikely:
            if probability_text is not None:
                return f"{location}ನಲ್ಲಿ ಮಳೆ ಬರುವ ಸಾಧ್ಯತೆ ತೀರಾ ಕಡಿಮೆ. ಮಳೆಯ ಸಂಭವನೀಯತೆ ಕೇವಲ {probability_text}% ಆಗಿದೆ."
            return f"{location}ನಲ್ಲಿ ಮಳೆ ಬರುವ ಸಾಧ್ಯತೆ ಇಲ್ಲ."
        if heavy_rain:
            return f"{location}ನಲ್ಲಿ ಭಾರಿ ಮಳೆಯಾಗುವ ಸಾಧ್ಯತೆಯಿದೆ."
        if probability_text is not None:
            return f"{location}ನಲ್ಲಿ ಮಳೆಯಾಗುವ {probability_text}% ಸಾಧ್ಯತೆಯಿದೆ."
        return f"{location} ಹವಾಮಾನ ಮಾಹಿತಿ ಲಭ್ಯವಿದೆ."

    # -----------------------------------------------------
    # MALAYALAM
    # -----------------------------------------------------
    if language == "Malayalam":
        if is_rain_unlikely:
            if probability_text is not None:
                return f"{location}-ൽ മഴ പെയ്യാൻ സാധ്യത കുറവാണ്. മഴയുടെ സാധ്യത {probability_text}% മാത്രമാണ്."
            return f"{location}-ൽ മഴയ്ക്ക് സാധ്യതയില്ല."
        if heavy_rain:
            return f"{location} ൽ ശക്തമായ മഴയ്ക്ക് സാധ്യതയുണ്ട്."
        if probability_text is not None:
            return f"{location} ൽ മഴയ്ക്ക് {probability_text}% സാധ്യതയുണ്ട്."
        return f"{location} ലെ കാലാവസ്ഥാ വിവരങ്ങൾ ലഭ്യമാണ്."

    # -----------------------------------------------------
    # ASSAMESE
    # -----------------------------------------------------
    if language == "Assamese":
        if is_rain_unlikely:
            return f"{location}ত বৰষুণ হোৱাৰ সম্ভাৱনা কম।"
        if heavy_rain:
            return f"{location}ত প্ৰচণ্ড বৰষুণৰ সম্ভাৱনা আছে।"
        if probability_text is not None:
            return f"{location}ত বৰষুণৰ {probability_text}% সম্ভাৱনা আছে।"
        return f"{location}ৰ বতৰৰ তথ্য উপলব্ধ।"

    # -----------------------------------------------------
    # URDU
    # -----------------------------------------------------
    if language == "Urdu":
        if is_rain_unlikely:
            return f"{location} میں بارش کا امکان بہت کم ہے۔"
        if heavy_rain:
            return f"{location} میں شدید بارش کا امکان ہے۔"
        if probability_text is not None:
            return f"{location} میں بارش کے {probability_text}% امکانات ہیں۔"
        return f"{location} کے موسم کی معلومات دستیاب ہیں۔"

    # -----------------------------------------------------
    # NEPALI
    # -----------------------------------------------------
    if language == "Nepali":
        if is_rain_unlikely:
            return f"{location} मा वर्षा हुने सम्भावना कम छ।"
        if heavy_rain:
            return f"{location} मा भारी वर्षाको सम्भावना छ।"
        if probability_text is not None:
            return f"{location} मा वर्षाको {probability_text}% सम्भावना छ।"
        return f"{location} को मौसमसम्बन्धी जानकारी उपलब्ध छ।"

    return f"Rain information is available for {location}."


# =========================================================
# HEAVY RAIN NOT EXPECTED
# =========================================================

def generate_heavy_rain_not_expected_answer(
    language,
    location,
    probability,
    rainfall
):
    """
    Used when the USER asks about heavy rain,
    but Weather Intelligence says heavy rain is NOT expected.
    """

    probability_text = format_number(probability)
    rainfall_text = format_number(rainfall)

    if language == "English":
        answer = f"Heavy rain is not expected in {location}."
        if probability_text is not None:
            answer += f" Rain is possible with a {probability_text}% chance."
        if rainfall_text is not None:
            answer += f" Expected rainfall is about {rainfall_text} mm."
        return answer

    if language == "Hindi":
        answer = f"{location} में भारी बारिश होने की संभावना नहीं है।"
        if probability_text is not None:
            answer += f" बारिश की संभावना {probability_text}% है।"
        if rainfall_text is not None:
            answer += f" लगभग {rainfall_text} मिमी बारिश हो सकती है।"
        return answer

    if language == "Hinglish":
        answer = f"{location} mein heavy baarish expected nahi hai."
        if probability_text is not None:
            answer += f" Rain ki probability {probability_text}% hai."
        if rainfall_text is not None:
            answer += f" Lagbhag {rainfall_text} mm rainfall ho sakti hai."
        return answer

    if language == "Odia":
        answer = f"{location}ରେ ପ୍ରବଳ ବର୍ଷା ହେବାର ସମ୍ଭାବନା ନାହିଁ।"
        if probability_text is not None:
            answer += f" ବର୍ଷାର ସମ୍ଭାବନା {probability_text}% ଅଛି।"
        if rainfall_text is not None:
            answer += f" ପ୍ରାୟ {rainfall_text} ମିମି ବର୍ଷା ହୋଇପାରେ।"
        return answer

    if language == "Bengali":
        answer = f"{location}-এ ভারী বৃষ্টির সম্ভাবনা নেই।"
        if probability_text is not None:
            answer += f" বৃষ্টির সম্ভাবনা {probability_text}% রয়েছে।"
        return answer

    if language == "Gujarati":
        answer = f"{location} માં ભારે વરસાદની શક્યતા નથી."
        if probability_text is not None:
            answer += f" વરસાદની શક્યતા {probability_text}% છે."
        return answer

    if language == "Marathi":
        answer = f"{location} मध्ये मुसळधार पावसाची शक्यता नाही."
        if probability_text is not None:
            answer += f" पावसाची शक्यता {probability_text}% आहे."
        return answer

    if language == "Punjabi":
        answer = f"{location} ਵਿੱਚ ਭਾਰੀ ਮੀਂਹ ਦੀ ਸੰਭਾਵਨਾ ਨਹੀਂ ਹੈ।"
        if probability_text is not None:
            answer += f" ਮੀਂਹ ਦੀ ਸੰਭਾਵਨਾ {probability_text}% ਹੈ।"
        return answer

    if language == "Tamil":
        answer = f"{location} பகுதியில் கனமழை பெய்ய வாய்ப்பில்லை."
        if probability_text is not None:
            answer += f" மழைக்கான வாய்ப்பு {probability_text}% உள்ளது."
        return answer

    if language == "Telugu":
        answer = f"{location}లో భారీ వర్షాలు కురిసే అవకాశం లేదు."
        if probability_text is not None:
            answer += f" వర్ష సూచన {probability_text}% ఉంది."
        return answer

    if language == "Kannada":
        answer = f"{location}ನಲ್ಲಿ ಭಾರಿ ಮಳೆಯಾಗುವ ಸಾಧ್ಯತೆ ಇಲ್ಲ."
        if probability_text is not None:
            answer += f" ಮಳೆಯಾಗುವ ಸಾಧ್ಯತೆ {probability_text}% ಇದೆ."
        return answer

    if language == "Malayalam":
        answer = f"{location}-ൽ ശക്തമായ മഴയ്ക്ക് സാധ്യതയില്ല."
        if probability_text is not None:
            answer += f" മഴയ്ക്ക് {probability_text}% സാധ്യതയുണ്ട്."
        return answer

    if language == "Assamese":
        return f"{location}ত প্ৰচণ্ড বৰষুণৰ সম্ভাৱনা নাই।"

    if language == "Urdu":
        return f"{location} میں شدید بارش کا امکان نہیں ہے۔"

    return f"Heavy rain is not expected in {location}. Rain information is available."


# =========================================================
# TEMPERATURE ANSWER
# =========================================================

def generate_temperature_answer(
    language,
    location,
    temperature,
    temperature_max,
    temperature_min,
):
    """Generate temperature response."""

    temperature_text = format_number(temperature)
    max_text = format_number(temperature_max)
    min_text = format_number(temperature_min)

    # CURRENT TEMPERATURE
    if temperature_text is not None:
        if language == "English":
            return f"The current temperature in {location} is {temperature_text}°C."
        if language == "Hindi":
            return f"{location} में वर्तमान तापमान {temperature_text}°C है।"
        if language == "Hinglish":
            return f"{location} mein current temperature {temperature_text}°C hai."
        if language == "Odia":
            return f"{location}ରେ ବର୍ତ୍ତମାନ ତାପମାତ୍ରା {temperature_text}°C ଅଛି।"
        if language == "Bengali":
            return f"{location}-এ বর্তমান তাপমাত্রা {temperature_text}°C।"
        if language == "Gujarati":
            return f"{location} માં વર્તમાન તાપમાન {temperature_text}°C છે."
        if language == "Marathi":
            return f"{location} मध्ये सध्याचे तापमान {temperature_text}°C आहे."
        if language == "Punjabi":
            return f"{location} ਵਿੱਚ ਮੌਜੂਦਾ ਤਾਪਮਾਨ {temperature_text}°C ਹੈ।"
        if language == "Tamil":
            return f"{location} பகுதியில் தற்போதைய வெப்பநிலை {temperature_text}°C ஆகும்."
        if language == "Telugu":
            return f"{location}లో ప్రస్తుత ఉష్ణోగ్రత {temperature_text}°C."
        if language == "Kannada":
            return f"{location}ನಲ್ಲಿ ಪ್ರಸ್ತುತ ತಾಪಮಾನ {temperature_text}°C ಆಗಿದೆ."
        if language == "Malayalam":
            return f"{location}-ൽ നിലവിലെ താപനില {temperature_text}°C ആണ്."
        if language == "Assamese":
            return f"{location}ত বৰ্তমানৰ তাপমাত্ৰা {temperature_text}°C।"
        if language == "Urdu":
            return f"{location} میں موجودہ درجہ حرارت {temperature_text}°C ہے۔"

    # FORECAST TEMPERATURE
    if max_text is not None and min_text is not None:
        if language == "English":
            return f"The temperature in {location} is expected to range from {min_text}°C to {max_text}°C."
        if language == "Hindi":
            return f"{location} में तापमान {min_text}°C से {max_text}°C के बीच रहने की संभावना है।"
        if language == "Hinglish":
            return f"{location} mein temperature {min_text}°C se {max_text}°C ke beech rehne ki sambhavna hai."
        if language == "Odia":
            return f"{location}ରେ ତାପମାତ୍ରା {min_text}°C ରୁ {max_text}°C ମଧ୍ୟରେ ରହିପାରେ।"
        if language == "Bengali":
            return f"{location}-এ তাপমাত্রা {min_text}°C থেকে {max_text}°C এর মধ্যে থাকতে পারে।"
        if language == "Gujarati":
            return f"{location} માં તાપમાન {min_text}°C થી {max_text}°C વચ્ચે રહેવાની શક્યતા છે."
        if language == "Marathi":
            return f"{location} मध्ये तापमान {min_text}°C ते {max_text}°C दरम्यान राहण्याचा अंदाज आहे."
        if language == "Punjabi":
            return f"{location} ਵਿੱਚ ਤਾਪਮਾਨ {min_text}°C ਤੋਂ {max_text}°C ਵਿਚਕਾਰ ਰਹਿਣ ਦੀ ਸੰਭਾਵਨਾ ਹੈ।"
        if language == "Tamil":
            return f"{location} பகுதியில் வெப்பநிலை {min_text}°C முதல் {max_text}°C வரை இருக்கும் என எதிர்பார்க்கப்படுகிறது."
        if language == "Telugu":
            return f"{location}లో ఉష్ణోగ్రత {min_text}°C నుండి {max_text}°C మధ్య ఉండే అవకాశం ఉంది."
        if language == "Kannada":
            return f"{location}ನಲ್ಲಿ ತಾಪಮಾನವು {min_text}°C ಇಂದ {max_text}°C ವರೆಗೆ ಇರುವ ಸಾಧ್ಯತೆಯಿದೆ."
        if language == "Malayalam":
            return f"{location}-ൽ താപനില {min_text}°C മുതൽ {max_text}°C വരെ ആയിരിക്കാൻ സാധ്യതയുണ്ട്."
        if language == "Assamese":
            return f"{location}ত তাপমাত্ৰা {min_text}°C ৰ পৰা {max_text}°C ৰ ভিতৰত থাকিব পাৰে।"
        if language == "Urdu":
            return f"{location} میں درجہ حرارت {min_text}°C سے {max_text}°C کے درمیان رہنے کی توقع ہے۔"

    return None


# =========================================================
# HUMIDITY ANSWER
# =========================================================

def generate_humidity_answer(
    language,
    location,
    humidity
):
    """Generate humidity response."""

    humidity_text = format_number(humidity)
    if humidity_text is None:
        return None

    if language == "English":
        return f"The current humidity in {location} is {humidity_text}%."
    if language == "Hindi":
        return f"{location} में वर्तमान आर्द्रता {humidity_text}% है।"
    if language == "Hinglish":
        return f"{location} mein current humidity {humidity_text}% hai."
    if language == "Odia":
        return f"{location}ରେ ବର୍ତ୍ତମାନ ଆର୍ଦ୍ରତା {humidity_text}% ଅଛି।"
    if language == "Bengali":
        return f"{location}-এ বর্তমান আর্দ্রতা {humidity_text}%।"
    if language == "Gujarati":
        return f"{location} માં વર્તમાન ભેજનું પ્રમાણ {humidity_text}% છે."
    if language == "Marathi":
        return f"{location} मध्ये सध्याची आर्द्रता {humidity_text}% आहे."
    if language == "Punjabi":
        return f"{location} ਵਿੱਚ ਮੌਜੂਦਾ ਨਮੀ {humidity_text}% ਹੈ।"
    if language == "Tamil":
        return f"{location} பகுதியில் தற்போதைய ஈரப்பதம் {humidity_text}% ஆகும்."
    if language == "Telugu":
        return f"{location}లో ప్రస్తుత తేమ శాతం {humidity_text}%."
    if language == "Kannada":
        return f"{location}ನಲ್ಲಿ ಪ್ರಸ್ತುತ ತೇವಾಂಶ {humidity_text}% ಆಗಿದೆ."
    if language == "Malayalam":
        return f"{location}-ൽ നിലവിലെ ഈർപ്പം {humidity_text}% ആണ്."
    if language == "Assamese":
        return f"{location}ত বৰ্তমানৰ আৰ্দ্ৰতা {humidity_text}%।"
    if language == "Urdu":
        return f"{location} میں موجودہ نمی {humidity_text}% ہے۔"

    return f"The humidity in {location} is {humidity_text}%."


# =========================================================
# WEATHER ANSWER
# =========================================================

def generate_weather_answer(
    language,
    facts,
    parameters=None,
    intelligence=None,
    question=""
):
    """
    Generate final answer using:
    1. User requested parameters
    2. Weather facts
    3. Weather Intelligence Engine
    """

    location = facts.get("location") or "the requested location"

    probability = facts.get("rain_probability")
    rainfall = facts.get("rainfall_mm")

    temperature = facts.get("temperature_c")
    temperature_max = facts.get("temperature_max_c")
    temperature_min = facts.get("temperature_min_c")

    humidity = facts.get("humidity")

    # -----------------------------------------------------
    # Intelligence information
    # -----------------------------------------------------
    intelligence = intelligence or {}
    forecast_analysis = intelligence.get("forecast_analysis", {})
    rain_analysis = forecast_analysis.get("rain_analysis", {})

    intelligence_heavy_rain = rain_analysis.get("heavy_rain", False) or bool(facts.get("heavy_rain"))
    hazards = intelligence.get("hazards", [])
    if any(
        hazard.get("hazard_type") == "heavy_rainfall"
        for hazard in hazards
        if isinstance(hazard, dict)
    ):
        intelligence_heavy_rain = True

    # -----------------------------------------------------
    # User parameters
    # -----------------------------------------------------
    parameters = parameters or []
    normalized_parameters = {str(parameter).lower() for parameter in parameters}
    question_lower = question.lower()

    # 1. HUMIDITY
    if "humidity" in normalized_parameters:
        humidity_answer = generate_humidity_answer(language, location, humidity)
        if humidity_answer:
            return humidity_answer

    # 2. TEMPERATURE
    if "temperature" in normalized_parameters:
        temperature_answer = generate_temperature_answer(
            language, location, temperature, temperature_max, temperature_min
        )
        if temperature_answer:
            return temperature_answer

    # 3. HEAVY RAIN QUESTION
    heavy_rain_requested = (
        "heavy rain" in question_lower
        or "heavy rainfall" in question_lower
        or "heavy baarish" in question_lower
        or "heavy बारिश" in question_lower
        or "भारी बारिश" in question
        or "मूसलाधार बारिश" in question
        or "ଭାରୀ ବର୍ଷା" in question
        or "ପ୍ରବଳ ବର୍ଷା" in question
        or "ବବଳ ବର୍ଷା" in question
        or "মুষলধারে বৃষ্টি" in question
        or "ভারী বৃষ্টি" in question
        or "ভীষণ বৃষ্টি" in question
        or "ભારે વરસાદ" in question
        or "मुसळधार पाऊस" in question
        or "கனமழை" in question
        or "மிக கனமழை" in question
        or "భారీ వర్షం" in question
        or "తీవ్ర వర్షం" in question
        or "ಭಾರೀ ಮಳೆ" in question
        or "കനത്ത മഴ" in question
        or "ਭਾਰੀ ਮੀਂਹ" in question
    )

    if heavy_rain_requested:
        if intelligence_heavy_rain:
            return generate_rain_answer(language, location, probability, rainfall, True)
        return generate_heavy_rain_not_expected_answer(language, location, probability, rainfall)

    # 4. NORMAL RAIN QUESTION
    if (
        "rainfall" in normalized_parameters
        or "rain" in normalized_parameters
        or "precipitation" in normalized_parameters
        or "weather_condition" in normalized_parameters
    ):
        return generate_rain_answer(
            language, location, probability, rainfall, intelligence_heavy_rain
        )

    # 5. FALLBACK
    if probability is not None or rainfall is not None:
        return generate_rain_answer(
            language, location, probability, rainfall, intelligence_heavy_rain
        )

    temperature_answer = generate_temperature_answer(
        language, location, temperature, temperature_max, temperature_min
    )
    if temperature_answer:
        return temperature_answer

    humidity_answer = generate_humidity_answer(language, location, humidity)
    if humidity_answer:
        return humidity_answer

    # GENERIC FALLBACK
    if language == "Hindi":
        return f"{location} के लिए मौसम की जानकारी उपलब्ध है।"
    if language == "Hinglish":
        return f"{location} ka weather data available hai."
    if language == "Odia":
        return f"{location} ପାଇଁ ପାଣିପାଗ ସୂଚନା ଉପଲବ୍ଧ ଅଛି।"
    if language == "Bengali":
        return f"{location}-এর আবহাওয়ার তথ্য উপলব্ধ রয়েছে।"
    if language == "Gujarati":
        return f"{location} માટે હવામાનની માહિતી ઉપલબ્ધ છે."
    if language == "Marathi":
        return f"{location} साठी हवामानाची माहिती उपलब्ध आहे."
    if language == "Punjabi":
        return f"{location} ਲਈ ਮੌਸਮ ਦੀ ਜਾਣਕਾਰੀ ਉਪਲਬਧ ਹੈ।"
    if language == "Tamil":
        return f"{location} வானிலை தகவல் கிடைக்கிறது."
    if language == "Telugu":
        return f"{location} వాతావరణ సమాచారం అందుబాటులో ఉంది."
    if language == "Kannada":
        return f"{location} ಹವಾಮಾನ ಮಾಹಿತಿ ಲಭ್ಯವಿದೆ."
    if language == "Malayalam":
        return f"{location} ലെ കാലാവസ്ഥാ വിവരങ്ങൾ ലഭ്യമാണ്."
    if language == "Assamese":
        return f"{location}ৰ বতৰৰ তথ্য উপলব্ধ।"
    if language == "Urdu":
        return f"{location} کے موسم کی معلومات دستیاب ہیں۔"

    return f"Weather information is available for {location}."


# =========================================================
# FINAL ANSWER
# =========================================================

def generate_climate_answer(tool_result: dict) -> str:
    """Create a concise answer from Member 3 climate analysis."""
    data = tool_result.get("data", {})
    if tool_result.get("status") != "intelligence_data":
        return data.get("message", "Climate analysis is unavailable.")
    results = data.get("climate_analysis", [])
    if not results:
        return "No climate analysis was returned for the requested period."
    summaries = []
    for result in results:
        metric = str(result.get("metric", "metric")).lower()
        average = format_number(result.get("average_value"))
        baseline = format_number(result.get("baseline_value"))
        anomaly = format_number(result.get("anomaly"))
        trend = str(result.get("trend", "stable")).lower()
        summaries.append(
            f"{metric.title()}: average {average}, baseline {baseline}, "
            f"anomaly {anomaly}, trend {trend}."
        )
    return " ".join(summaries)


def generate_final_answer(
    question: str,
    analysis: dict,
    tool_result: dict,
    intelligence: dict = None
) -> str:
    """
    Generate final answer.
    Weather facts come directly from the weather tool.
    Intelligence comes from Weather Intelligence Engine.
    """
    if tool_result.get("tool") == "get_climate_analysis":
        return generate_climate_answer(tool_result)

    language = analysis.get("language", "English")
    parameters = analysis.get("parameters", [])

    facts = interpret_weather(tool_result)

    # Ensure location is populated from analysis if tool_result lacked it
    if not facts.get("location") and analysis.get("location"):
        facts["location"] = analysis["location"]

    return generate_weather_answer(
        language=language,
        facts=facts,
        parameters=parameters,
        intelligence=intelligence,
        question=question
    )
