'use client'

import { createContext, useContext, useEffect, useMemo, useState } from 'react'

export const languages = [
  'English',
  'Hindi',
  'Bengali',
  'Tamil',
  'Telugu',
  'Marathi',
  'Gujarati',
  'Kannada',
  'Odia',
] as const

export type AppLanguage = (typeof languages)[number]

const languageLabels: Record<AppLanguage, string> = {
  English: 'English',
  Hindi: 'हिन्दी',
  Bengali: 'বাংলা',
  Tamil: 'தமிழ்',
  Telugu: 'తెలుగు',
  Marathi: 'मराठी',
  Gujarati: 'ગુજરાતી',
  Kannada: 'ಕನ್ನಡ',
  Odia: 'ଓଡ଼ିଆ',
}

const translations: Record<AppLanguage, Record<string, string>> = {
  English: {},
  Hindi: {
    Home: 'होम', Chat: 'चैट', 'Current Weather': 'वर्तमान मौसम', Forecast: 'पूर्वानुमान',
    'Weather Map': 'मौसम मानचित्र', Alerts: 'चेतावनियाँ', Climate: 'जलवायु', Advisories: 'सलाह',
    Settings: 'सेटिंग्स', 'Conversational Weather AI': 'संवादी मौसम AI', 'Ask WeatherGPT anything…': 'WeatherGPT से कुछ भी पूछें…',
    'Language & Units': 'भाषा और इकाइयाँ', 'App language': 'ऐप भाषा', 'Multilingual support for Indian languages': 'भारतीय भाषाओं के लिए बहुभाषी सहायता',
    'Temperature unit': 'तापमान इकाई', 'Display readings in Celsius or Fahrenheit': 'रीडिंग सेल्सियस या फ़ारेनहाइट में दिखाएँ',
    'Voice & Accessibility': 'आवाज़ और सुलभता', 'Voice input': 'आवाज़ से इनपुट', 'Ask questions by speaking — ideal for rural accessibility': 'बोलकर सवाल पूछें — ग्रामीण सुलभता के लिए उपयोगी',
    'Read responses aloud': 'जवाब ज़ोर से पढ़ें', 'Text-to-speech for WeatherGPT replies': 'WeatherGPT जवाबों के लिए टेक्स्ट-टू-स्पीच',
    Notifications: 'सूचनाएँ', 'Severe weather alerts': 'गंभीर मौसम चेतावनियाँ', 'Push warnings for storms, floods & cyclones': 'तूफान, बाढ़ और चक्रवात की सूचनाएँ',
    'Daily forecast summary': 'दैनिक पूर्वानुमान सारांश', 'A morning briefing at 7:00 AM': 'सुबह 7 बजे का संक्षिप्त विवरण',
    Appearance: 'दिखावट', 'Dark mode': 'डार्क मोड', 'Switch between light and dark themes': 'लाइट और डार्क थीम बदलें',
    'Personalise WeatherGPT for accessibility and your region': 'अपनी सुलभता और क्षेत्र के लिए WeatherGPT को निजीकृत करें',
    'Namaste! I am WeatherGPT, your conversational weather assistant. Ask me about forecasts, rainfall, storms, air quality, travel safety, or sector advisories — in plain language.': 'नमस्ते! मैं WeatherGPT, आपका संवादात्मक मौसम सहायक हूँ। पूर्वानुमान, बारिश, तूफान, वायु गुणवत्ता, यात्रा सुरक्षा या क्षेत्रीय सलाह के बारे में सरल भाषा में पूछें।',
    'Online · Multilingual': 'ऑनलाइन · बहुभाषी', 'Listening…': 'सुन रहा हूँ…', 'Ask WeatherGPT…': 'WeatherGPT से पूछें…',
  },
  Bengali: { Home: 'হোম', Chat: 'চ্যাট', Settings: 'সেটিংস', Forecast: 'পূর্বাভাস', Alerts: 'সতর্কতা', Climate: 'জলবায়ু', 'Current Weather': 'বর্তমান আবহাওয়া', 'Weather Map': 'আবহাওয়ার মানচিত্র', Advisories: 'পরামর্শ', 'Language & Units': 'ভাষা ও একক', 'App language': 'অ্যাপের ভাষা', 'Temperature unit': 'তাপমাত্রার একক', Appearance: 'চেহারা', 'Dark mode': 'ডার্ক মোড', 'Voice input': 'ভয়েস ইনপুট', 'Read responses aloud': 'উত্তর পড়ে শোনান', 'Online · Multilingual': 'অনলাইন · বহুভাষিক', 'Ask WeatherGPT…': 'WeatherGPT-কে জিজ্ঞাসা করুন…' },
  Tamil: { Home: 'முகப்பு', Chat: 'அரட்டை', Settings: 'அமைப்புகள்', Forecast: 'முன்னறிவிப்பு', Alerts: 'எச்சரிக்கைகள்', Climate: 'காலநிலை', 'Current Weather': 'தற்போதைய வானிலை', 'Weather Map': 'வானிலை வரைபடம்', Advisories: 'ஆலோசனைகள்', 'Language & Units': 'மொழி மற்றும் அலகுகள்', 'App language': 'பயன்பாட்டு மொழி', 'Temperature unit': 'வெப்பநிலை அலகு', Appearance: 'தோற்றம்', 'Dark mode': 'இருண்ட பயன்முறை', 'Voice input': 'குரல் உள்ளீடு', 'Read responses aloud': 'பதில்களை சத்தமாகப் படிக்கவும்', 'Online · Multilingual': 'ஆன்லைன் · பல்மொழி', 'Ask WeatherGPT…': 'WeatherGPT-யிடம் கேளுங்கள்…' },
  Telugu: { Home: 'హోమ్', Chat: 'చాట్', Settings: 'సెట్టింగ్‌లు', Forecast: 'వాతావరణ సూచన', Alerts: 'హెచ్చరికలు', Climate: 'వాతావరణం', 'Current Weather': 'ప్రస్తుత వాతావరణం', 'Weather Map': 'వాతావరణ పటం', Advisories: 'సలహాలు', 'Language & Units': 'భాష మరియు యూనిట్లు', 'App language': 'యాప్ భాష', 'Temperature unit': 'ఉష్ణోగ్రత యూనిట్', Appearance: 'రూపురేఖలు', 'Dark mode': 'డార్క్ మోడ్', 'Voice input': 'వాయిస్ ఇన్‌పుట్', 'Read responses aloud': 'సమాధానాలను బిగ్గరగా చదవండి', 'Online · Multilingual': 'ఆన్‌లైన్ · బహుభాషా', 'Ask WeatherGPT…': 'WeatherGPTని అడగండి…' },
  Marathi: { Home: 'मुख्यपृष्ठ', Chat: 'चॅट', Settings: 'सेटिंग्ज', Forecast: 'अंदाज', Alerts: 'सूचना', Climate: 'हवामान', 'Current Weather': 'सध्याचे हवामान', 'Weather Map': 'हवामान नकाशा', Advisories: 'सल्ला', 'Language & Units': 'भाषा आणि एकके', 'App language': 'अॅप भाषा', 'Temperature unit': 'तापमान एकक', Appearance: 'दिसणे', 'Dark mode': 'डार्क मोड', 'Voice input': 'आवाज इनपुट', 'Read responses aloud': 'उत्तरे मोठ्याने वाचा', 'Online · Multilingual': 'ऑनलाइन · बहुभाषिक', 'Ask WeatherGPT…': 'WeatherGPT ला विचारा…' },
  Gujarati: { Home: 'હોમ', Chat: 'ચેટ', Settings: 'સેટિંગ્સ', Forecast: 'આગાહી', Alerts: 'ચેતવણીઓ', Climate: 'આબોહવા', 'Current Weather': 'વર્તમાન હવામાન', 'Weather Map': 'હવામાન નકશો', Advisories: 'સલાહ', 'Language & Units': 'ભાષા અને એકમો', 'App language': 'એપ ભાષા', 'Temperature unit': 'તાપમાન એકમ', Appearance: 'દેખાવ', 'Dark mode': 'ડાર્ક મોડ', 'Voice input': 'અવાજ ઇનપુટ', 'Read responses aloud': 'જવાબો મોટેથી વાંચો', 'Online · Multilingual': 'ઓનલાઇન · બહુભાષી', 'Ask WeatherGPT…': 'WeatherGPTને પૂછો…' },
  Kannada: { Home: 'ಮುಖಪುಟ', Chat: 'ಚಾಟ್', Settings: 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು', Forecast: 'ಮುನ್ಸೂಚನೆ', Alerts: 'ಎಚ್ಚರಿಕೆಗಳು', Climate: 'ಹವಾಮಾನ', 'Current Weather': 'ಪ್ರಸ್ತುತ ಹವಾಮಾನ', 'Weather Map': 'ಹವಾಮಾನ ನಕ್ಷೆ', Advisories: 'ಸಲಹೆಗಳು', 'Language & Units': 'ಭಾಷೆ ಮತ್ತು ಘಟಕಗಳು', 'App language': 'ಅಪ್ಲಿಕೇಶನ್ ಭಾಷೆ', 'Temperature unit': 'ತಾಪಮಾನ ಘಟಕ', Appearance: 'ನೋಟ', 'Dark mode': 'ಡಾರ್ಕ್ ಮೋಡ್', 'Voice input': 'ಧ್ವನಿ ಇನ್‌ಪುಟ್', 'Read responses aloud': 'ಉತ್ತರಗಳನ್ನು ಗಟ್ಟಿಯಾಗಿ ಓದಿ', 'Online · Multilingual': 'ಆನ್‌ಲೈನ್ · ಬಹುಭಾಷಾ', 'Ask WeatherGPT…': 'WeatherGPT ಅನ್ನು ಕೇಳಿ…' },
  Odia: {
    Home: 'ହୋମ୍', Chat: 'ଚାଟ୍', 'Current Weather': 'ବର୍ତ୍ତମାନର ପାଣିପାଗ', Forecast: 'ପୂର୍ବାନୁମାନ',
    'Weather Map': 'ପାଣିପାଗ ମାନଚିତ୍ର', Alerts: 'ସତର୍କତା', Climate: 'ଜଳବାୟୁ', Advisories: 'ପରାମର୍ଶ',
    Settings: 'ସେଟିଂସ୍', 'Conversational Weather AI': 'କଥୋପକଥନମୂଳକ ପାଣିପାଗ AI',
    'Ask WeatherGPT anything…': 'WeatherGPT କୁ କିଛି ପଚାରନ୍ତୁ…', 'Language & Units': 'ଭାଷା ଏବଂ ଏକକ',
    'App language': 'ଆପ୍ ଭାଷା', 'Multilingual support for Indian languages': 'ଭାରତୀୟ ଭାଷା ପାଇଁ ବହୁଭାଷୀ ସହାୟତା',
    'Temperature unit': 'ତାପମାତ୍ରା ଏକକ', 'Display readings in Celsius or Fahrenheit': 'ସେଲସିୟସ୍ କିମ୍ବା ଫାରେନହାଇଟ୍‌ରେ ମାପ ଦେଖାନ୍ତୁ',
    'Voice & Accessibility': 'ସ୍ୱର ଏବଂ ସୁଗମତା', 'Voice input': 'ସ୍ୱର ଇନପୁଟ୍',
    'Ask questions by speaking — ideal for rural accessibility': 'କଥା କହି ପ୍ରଶ୍ନ ପଚାରନ୍ତୁ — ଗ୍ରାମୀଣ ସୁଗମତା ପାଇଁ ଉପଯୋଗୀ',
    'Read responses aloud': 'ଉତ୍ତରଗୁଡ଼ିକୁ ଉଚ୍ଚସ୍ୱରରେ ପଢ଼ନ୍ତୁ', 'Text-to-speech for WeatherGPT replies': 'WeatherGPT ଉତ୍ତର ପାଇଁ ଟେକ୍ସଟ୍-ଟୁ-ସ୍ପିଚ୍',
    Notifications: 'ବିଜ୍ଞପ୍ତି', 'Severe weather alerts': 'ତୀବ୍ର ପାଣିପାଗ ସତର୍କତା', 'Daily forecast summary': 'ଦୈନିକ ପୂର୍ବାନୁମାନ ସାରାଂଶ',
    Appearance: 'ଦୃଶ୍ୟ', 'Dark mode': 'ଡାର୍କ ମୋଡ୍', 'Switch between light and dark themes': 'ଲାଇଟ୍ ଏବଂ ଡାର୍କ ଥିମ୍ ବଦଳାନ୍ତୁ',
    'Online · Multilingual': 'ଅନଲାଇନ୍ · ବହୁଭାଷୀ', 'Listening…': 'ଶୁଣୁଛି…', 'Ask WeatherGPT…': 'WeatherGPT କୁ ପଚାରନ୍ତୁ…',
    'The assistant took too long to respond. Please try again.': 'ସହାୟକଙ୍କ ଉତ୍ତର ଦେବାକୁ ଅଧିକ ସମୟ ଲାଗିଲା। ଦୟାକରି ପୁଣି ଚେଷ୍ଟା କରନ୍ତୁ।',
    'The assistant connection was interrupted. Please try again.': 'ସହାୟକଙ୍କ ସଂଯୋଗ ବିଚ୍ଛିନ୍ନ ହୋଇଛି। ଦୟାକରି ପୁଣି ଚେଷ୍ଟା କରନ୍ତୁ।',
    'The live assistant is unavailable.': 'ଲାଇଭ୍ ସହାୟକ ଉପଲବ୍ଧ ନାହିଁ।',
    'Choose location': 'ଅବସ୍ଥାନ ବାଛନ୍ତୁ', 'Choose a location': 'ଏକ ଅବସ୍ଥାନ ବାଛନ୍ତୁ', Close: 'ବନ୍ଦ କରନ୍ତୁ',
    'Search city, district, or village': 'ସହର, ଜିଲ୍ଲା କିମ୍ବା ଗାଁ ଖୋଜନ୍ତୁ', 'Searching locations…': 'ଅବସ୍ଥାନ ଖୋଜାଯାଉଛି…',
    'Use current device location': 'ବର୍ତ୍ତମାନ ଡିଭାଇସ୍ ଅବସ୍ଥାନ ବ୍ୟବହାର କରନ୍ତୁ', 'Location search failed.': 'ଅବସ୍ଥାନ ଖୋଜା ବିଫଳ ହେଲା।',
  },
}

// Shared copy used by the live-data screens. Keeping these keys in one place
// prevents a page from silently falling back to English when new data arrives.
const commonTranslations: Record<AppLanguage, Record<string, string>> = {
  English: {},
  Hindi: {
    'Enable location': 'स्थान सक्षम करें', 'Locating…': 'स्थान खोजा जा रहा है…', 'Finding your area…': 'आपका क्षेत्र खोजा जा रहा है…',
    'Finding your current area…': 'आपका वर्तमान क्षेत्र खोजा जा रहा है…', 'Your location': 'आपका स्थान', 'Location access needed': 'स्थान की अनुमति आवश्यक है',
    'Ask WeatherGPT anything…': 'WeatherGPT से कुछ भी पूछें…', 'More': 'अधिक', 'Details': 'विवरण', 'View all': 'सभी देखें',
    'Current Weather': 'वर्तमान मौसम', '7-day outlook': '7-दिन का पूर्वानुमान', 'Next 12 hours': 'अगले 12 घंटे',
    'Active alerts': 'सक्रिय चेतावनियाँ', 'Humidity': 'नमी', 'Wind': 'हवा', 'Pressure': 'दबाव', 'Visibility': 'दृश्यता',
    'UV Index': 'UV सूचकांक', 'Dew Point': 'ओसांक', 'Sunrise': 'सूर्योदय', 'Sunset': 'सूर्यास्त', 'Feels like': 'महसूस होता है',
    'Unavailable': 'उपलब्ध नहीं', 'Temperature': 'तापमान', 'Rainfall': 'वर्षा', 'Rain chance': 'वर्षा की संभावना',
    'Risk': 'जोखिम', 'Forecast': 'पूर्वानुमान', 'Weather Map': 'मौसम मानचित्र', 'Extreme Weather Alerts': 'चरम मौसम चेतावनियाँ',
    'Severe': 'गंभीर', 'Warnings': 'चेतावनियाँ', 'Total active': 'कुल सक्रिय', 'Climate Analysis': 'जलवायु विश्लेषण',
    'Warming rate': 'तापमान वृद्धि दर', 'Wettest month': 'सबसे अधिक वर्षा वाला महीना', 'Monthly climate history': 'मासिक जलवायु इतिहास',
    'Historical warming trend': 'ऐतिहासिक तापमान वृद्धि', 'Advisories': 'सलाह', 'Agriculture': 'कृषि', 'Aviation': 'विमानन',
    'Marine': 'समुद्री', 'Urban planning': 'शहरी योजना', 'Emergency planning': 'आपातकालीन योजना', 'General safety': 'सामान्य सुरक्षा',
    'low': 'कम', 'medium': 'मध्यम', 'high': 'उच्च', 'critical': 'गंभीर', 'Until conditions change': 'परिस्थितियाँ बदलने तक',
    'Loading WeatherGPT…': 'WeatherGPT लोड हो रहा है…',
  },
  Bengali: {
    'Enable location': 'অবস্থান চালু করুন', 'Locating…': 'অবস্থান খোঁজা হচ্ছে…', 'Your location': 'আপনার অবস্থান',
    'More': 'আরও', 'Details': 'বিস্তারিত', 'View all': 'সব দেখুন', 'Next 12 hours': 'পরবর্তী ১২ ঘণ্টা',
    '7-day outlook': '৭ দিনের পূর্বাভাস', 'Active alerts': 'সক্রিয় সতর্কতা', 'Humidity': 'আর্দ্রতা', 'Wind': 'বাতাস',
    'Pressure': 'চাপ', 'Visibility': 'দৃশ্যমানতা', 'Sunrise': 'সূর্যোদয়', 'Sunset': 'সূর্যাস্ত', 'Feels like': 'অনুভূত',
    'Forecast': 'পূর্বাভাস', 'Severe': 'তীব্র', 'Warnings': 'সতর্কতা', 'Total active': 'মোট সক্রিয়', 'Climate Analysis': 'জলবায়ু বিশ্লেষণ',
    'Warming rate': 'উষ্ণায়নের হার', 'Wettest month': 'সর্বাধিক বৃষ্টির মাস', 'Monthly climate history': 'মাসিক জলবায়ুর ইতিহাস',
    'Historical warming trend': 'ঐতিহাসিক উষ্ণায়ন প্রবণতা', 'Agriculture': 'কৃষি', 'Aviation': 'বিমান চলাচল',
    'Marine': 'সামুদ্রিক', 'Urban planning': 'শহর পরিকল্পনা', 'General safety': 'সাধারণ নিরাপত্তা', 'low': 'কম', 'medium': 'মাঝারি', 'high': 'উচ্চ', 'critical': 'গুরুতর',
  },
  Tamil: {
    'Enable location': 'இருப்பிடத்தை இயக்கவும்', 'Locating…': 'இருப்பிடம் தேடப்படுகிறது…', 'Your location': 'உங்கள் இருப்பிடம்',
    'More': 'மேலும்', 'Details': 'விவரங்கள்', 'View all': 'அனைத்தையும் காண்க', 'Next 12 hours': 'அடுத்த 12 மணி நேரம்',
    '7-day outlook': '7 நாள் முன்னறிவிப்பு', 'Active alerts': 'செயலில் உள்ள எச்சரிக்கைகள்', 'Humidity': 'ஈரப்பதம்', 'Wind': 'காற்று',
    'Pressure': 'அழுத்தம்', 'Visibility': 'தெரிவுநிலை', 'Sunrise': 'சூரிய உதயம்', 'Sunset': 'சூரிய அஸ்தமனம்', 'Feels like': 'உணரப்படும்',
    'Forecast': 'முன்னறிவிப்பு', 'Severe': 'கடுமையான', 'Warnings': 'எச்சரிக்கைகள்', 'Total active': 'மொத்த செயலில்', 'Climate Analysis': 'காலநிலை பகுப்பாய்வு',
    'Warming rate': 'வெப்பமயமாதல் விகிதம்', 'Wettest month': 'அதிக மழை மாதம்', 'Monthly climate history': 'மாதாந்திர காலநிலை வரலாறு',
    'Historical warming trend': 'வரலாற்று வெப்பமயமாதல் போக்கு', 'Agriculture': 'விவசாயம்', 'Aviation': 'விமானப் போக்குவரத்து',
    'Marine': 'கடல்', 'Urban planning': 'நகர்ப்புற திட்டமிடல்', 'General safety': 'பொது பாதுகாப்பு', 'low': 'குறைவு', 'medium': 'நடுத்தரம்', 'high': 'அதிகம்', 'critical': 'மிகவும் தீவிரம்',
  },
  Telugu: {
    'Enable location': 'స్థానాన్ని ప్రారంభించండి', 'Locating…': 'స్థానం కనుగొంటోంది…', 'Your location': 'మీ స్థానం',
    'More': 'మరిన్ని', 'Details': 'వివరాలు', 'View all': 'అన్నీ చూడండి', 'Next 12 hours': 'తదుపరి 12 గంటలు',
    '7-day outlook': '7 రోజుల సూచన', 'Active alerts': 'క్రియాశీల హెచ్చరికలు', 'Humidity': 'తేమ', 'Wind': 'గాలి',
    'Pressure': 'పీడనం', 'Visibility': 'దృశ్యమానత', 'Sunrise': 'సూర్యోదయం', 'Sunset': 'సూర్యాస్తమయం', 'Feels like': 'అనుభూతి',
    'Forecast': 'వాతావరణ సూచన', 'Severe': 'తీవ్రమైన', 'Warnings': 'హెచ్చరికలు', 'Total active': 'మొత్తం క్రియాశీల', 'Climate Analysis': 'వాతావరణ విశ్లేషణ',
    'Warming rate': 'వేడెక్కే రేటు', 'Wettest month': 'అత్యధిక వర్షపాతం నెల', 'Monthly climate history': 'నెలవారీ వాతావరణ చరిత్ర',
    'Historical warming trend': 'చారిత్రక వేడెక్కే ధోరణి', 'Agriculture': 'వ్యవసాయం', 'Aviation': 'విమానయానం',
    'Marine': 'సముద్ర', 'Urban planning': 'నగర ప్రణాళిక', 'General safety': 'సాధారణ భద్రత', 'low': 'తక్కువ', 'medium': 'మధ్యస్థం', 'high': 'ఎక్కువ', 'critical': 'తీవ్రమైన',
  },
  Marathi: {
    'Enable location': 'स्थान सुरू करा', 'Locating…': 'स्थान शोधत आहे…', 'Your location': 'तुमचे स्थान', 'More': 'अधिक',
    'Details': 'तपशील', 'View all': 'सर्व पहा', 'Next 12 hours': 'पुढील १२ तास', '7-day outlook': '७ दिवसांचा अंदाज',
    'Active alerts': 'सक्रिय सूचना', 'Humidity': 'आर्द्रता', 'Wind': 'वारा', 'Pressure': 'दाब', 'Visibility': 'दृश्यता',
    'Sunrise': 'सूर्योदय', 'Sunset': 'सूर्यास्त', 'Feels like': 'जाणवते', 'Severe': 'गंभीर', 'Warnings': 'सूचना',
    'Total active': 'एकूण सक्रिय', 'Climate Analysis': 'हवामान विश्लेषण', 'Warming rate': 'तापमान वाढीचा दर',
    'Wettest month': 'सर्वाधिक पावसाचा महिना', 'Monthly climate history': 'मासिक हवामान इतिहास', 'Historical warming trend': 'ऐतिहासिक तापमान वाढ',
    'Agriculture': 'शेती', 'Aviation': 'विमान वाहतूक', 'Marine': 'सागरी', 'Urban planning': 'शहरी नियोजन', 'General safety': 'सामान्य सुरक्षितता',
    'low': 'कमी', 'medium': 'मध्यम', 'high': 'जास्त', 'critical': 'अत्यंत गंभीर',
  },
  Gujarati: {
    'Enable location': 'સ્થાન સક્ષમ કરો', 'Locating…': 'સ્થાન શોધી રહ્યા છીએ…', 'Your location': 'તમારું સ્થાન', 'More': 'વધુ',
    'Details': 'વિગતો', 'View all': 'બધું જુઓ', 'Next 12 hours': 'આગામી 12 કલાક', '7-day outlook': '7 દિવસની આગાહી',
    'Active alerts': 'સક્રિય ચેતવણીઓ', 'Humidity': 'ભેજ', 'Wind': 'પવન', 'Pressure': 'દબાણ', 'Visibility': 'દૃશ્યતા',
    'Sunrise': 'સૂર્યોદય', 'Sunset': 'સૂર્યાસ્ત', 'Feels like': 'લાગે છે', 'Severe': 'ગંભીર', 'Warnings': 'ચેતવણીઓ',
    'Total active': 'કુલ સક્રિય', 'Climate Analysis': 'આબોહવા વિશ્લેષણ', 'Warming rate': 'ગરમી વધવાનો દર', 'Wettest month': 'સૌથી વધુ વરસાદનો મહિનો',
    'Monthly climate history': 'માસિક આબોહવા ઇતિહાસ', 'Historical warming trend': 'ઐતિહાસિક ગરમી વધવાની વૃત્તિ', 'Agriculture': 'કૃષિ',
    'Aviation': 'ઉડ્ડયન', 'Marine': 'દરિયાઈ', 'Urban planning': 'શહેરી આયોજન', 'General safety': 'સામાન્ય સલામતી', 'low': 'ઓછું', 'medium': 'મધ્યમ', 'high': 'ઊંચું', 'critical': 'ગંભીર',
  },
  Kannada: {
    'Enable location': 'ಸ್ಥಳವನ್ನು ಸಕ್ರಿಯಗೊಳಿಸಿ', 'Locating…': 'ಸ್ಥಳ ಹುಡುಕಲಾಗುತ್ತಿದೆ…', 'Your location': 'ನಿಮ್ಮ ಸ್ಥಳ', 'More': 'ಇನ್ನಷ್ಟು',
    'Details': 'ವಿವರಗಳು', 'View all': 'ಎಲ್ಲವನ್ನೂ ನೋಡಿ', 'Next 12 hours': 'ಮುಂದಿನ 12 ಗಂಟೆಗಳು', '7-day outlook': '7 ದಿನಗಳ ಮುನ್ಸೂಚನೆ',
    'Active alerts': 'ಸಕ್ರಿಯ ಎಚ್ಚರಿಕೆಗಳು', 'Humidity': 'ತೇವಾಂಶ', 'Wind': 'ಗಾಳಿ', 'Pressure': 'ಒತ್ತಡ', 'Visibility': 'ಗೋಚರತೆ',
    'Sunrise': 'ಸೂರ್ಯೋದಯ', 'Sunset': 'ಸೂರ್ಯಾಸ್ತ', 'Feels like': 'ಅನುಭವ', 'Severe': 'ತೀವ್ರ', 'Warnings': 'ಎಚ್ಚರಿಕೆಗಳು',
    'Total active': 'ಒಟ್ಟು ಸಕ್ರಿಯ', 'Climate Analysis': 'ಹವಾಮಾನ ವಿಶ್ಲೇಷಣೆ', 'Warming rate': 'ಬೆಚ್ಚಗಾಗುವ ದರ', 'Wettest month': 'ಅತಿ ಹೆಚ್ಚು ಮಳೆಯ ತಿಂಗಳು',
    'Monthly climate history': 'ಮಾಸಿಕ ಹವಾಮಾನ ಇತಿಹಾಸ', 'Historical warming trend': 'ಐತಿಹಾಸಿಕ ಬೆಚ್ಚಗಾಗುವ ಪ್ರವೃತ್ತಿ', 'Agriculture': 'ಕೃಷಿ',
    'Aviation': 'ವಿಮಾನಯಾನ', 'Marine': 'ಸಾಗರ', 'Urban planning': 'ನಗರ ಯೋಜನೆ', 'General safety': 'ಸಾಮಾನ್ಯ ಸುರಕ್ಷತೆ', 'low': 'ಕಡಿಮೆ', 'medium': 'ಮಧ್ಯಮ', 'high': 'ಹೆಚ್ಚು', 'critical': 'ಅತ್ಯಂತ ತೀವ್ರ',
  },
  Odia: {
    'Enable location': 'ଅବସ୍ଥାନ ସକ୍ରିୟ କରନ୍ତୁ', 'Locating…': 'ଅବସ୍ଥାନ ଖୋଜାଯାଉଛି…', 'Finding your area…': 'ଆପଣଙ୍କ ଅଞ୍ଚଳ ଖୋଜାଯାଉଛି…',
    'Finding your current area…': 'ଆପଣଙ୍କ ବର୍ତ୍ତମାନ ଅଞ୍ଚଳ ଖୋଜାଯାଉଛି…', 'Your location': 'ଆପଣଙ୍କ ଅବସ୍ଥାନ', 'Location access needed': 'ଅବସ୍ଥାନ ଅନୁମତି ଆବଶ୍ୟକ',
    More: 'ଅଧିକ', Details: 'ବିବରଣୀ', 'View all': 'ସବୁ ଦେଖନ୍ତୁ', 'Next 12 hours': 'ପରବର୍ତ୍ତୀ ୧୨ ଘଣ୍ଟା',
    '7-day outlook': '୭ ଦିନର ପୂର୍ବାନୁମାନ', 'Active alerts': 'ସକ୍ରିୟ ସତର୍କତା', Humidity: 'ଆର୍ଦ୍ରତା', Wind: 'ପବନ',
    Pressure: 'ଚାପ', Visibility: 'ଦୃଶ୍ୟତା', 'UV Index': 'UV ସୂଚକାଙ୍କ', 'Dew Point': 'ଶିଶିର ବିନ୍ଦୁ', Sunrise: 'ସୂର୍ଯ୍ୟୋଦୟ', Sunset: 'ସୂର୍ଯ୍ୟାସ୍ତ',
    'Feels like': 'ଅନୁଭବ ହେଉଛି', Temperature: 'ତାପମାତ୍ରା', Rainfall: 'ବର୍ଷା', 'Rain chance': 'ବର୍ଷାର ସମ୍ଭାବନା', Risk: 'ବିପଦ',
    'Extreme Weather Alerts': 'ଚରମ ପାଣିପାଗ ସତର୍କତା', Severe: 'ତୀବ୍ର', Warnings: 'ସତର୍କତା', 'Total active': 'ମୋଟ ସକ୍ରିୟ',
    'Climate Analysis': 'ଜଳବାୟୁ ବିଶ୍ଳେଷଣ', 'Warming rate': 'ଉଷ୍ମତା ବୃଦ୍ଧି ହାର', 'Wettest month': 'ସବୁଠାରୁ ଅଧିକ ବର୍ଷାର ମାସ',
    'Monthly climate history': 'ମାସିକ ଜଳବାୟୁ ଇତିହାସ', 'Historical warming trend': 'ଐତିହାସିକ ଉଷ୍ମତା ବୃଦ୍ଧି ପ୍ରବୃତ୍ତି',
    Agriculture: 'କୃଷି', Aviation: 'ବିମାନ ଚଳାଚଳ', Marine: 'ସାମୁଦ୍ରିକ', 'Urban planning': 'ସହର ଯୋଜନା',
    'General safety': 'ସାଧାରଣ ସୁରକ୍ଷା', low: 'କମ୍', medium: 'ମଧ୍ୟମ', high: 'ଅଧିକ', critical: 'ଅତ୍ୟନ୍ତ ତୀବ୍ର',
    'Loading WeatherGPT…': 'WeatherGPT ଲୋଡ୍ ହେଉଛି…', Retry: 'ପୁଣି ଚେଷ୍ଟା କରନ୍ତୁ', Updated: 'ଅଦ୍ୟତନ',
    Source: 'ଉତ୍ସ', 'Data provenance:': 'ଡାଟା ଉତ୍ସ:', 'Air Quality': 'ବାୟୁର ଗୁଣବତ୍ତା', 'Hourly trend': 'ଘଣ୍ଟା ପ୍ରବୃତ୍ତି',
    'Avg high': 'ହାରାହାରି ସର୍ବାଧିକ', 'Avg low': 'ହାରାହାରି ସର୍ବନିମ୍ନ', 'Mean temp': 'ହାରାହାରି ତାପମାତ୍ରା',
    Temp: 'ତାପମାତ୍ରା', 'Precipitation probability': 'ବର୍ଷାର ସମ୍ଭାବନା', 'Aggregated from daily data': 'ଦୈନିକ ଡାଟାରୁ ସଂଗୃହୀତ',
  },
}

for (const language of languages) {
  translations[language] = { ...commonTranslations[language], ...translations[language] }
}

const screenCopy: Record<AppLanguage, Record<string, string>> = {
  English: {},
  Hindi: {
    'Your region': 'आपका क्षेत्र', 'Current area': 'वर्तमान क्षेत्र', 'your current area': 'आपका वर्तमान क्षेत्र',
    'Extreme Weather Alerts': 'चरम मौसम चेतावनियाँ', 'Live forecast hazard detection and official alert feeds when configured': 'लाइव पूर्वानुमान खतरे की पहचान और उपलब्ध आधिकारिक चेतावनी फ़ीड',
    'Verify official IMD bulletins': 'आधिकारिक IMD बुलेटिन सत्यापित करें', 'These links open public IMD pages. WeatherGPT does not convert automated forecast risk into an official government warning.': 'ये लिंक सार्वजनिक IMD पृष्ठ खोलते हैं। WeatherGPT स्वचालित पूर्वानुमान जोखिम को आधिकारिक सरकारी चेतावनी में नहीं बदलता।',
    'Official warning': 'आधिकारिक चेतावनी', 'WeatherGPT intelligence': 'WeatherGPT इंटेलिजेंस', 'Open official bulletin': 'आधिकारिक बुलेटिन खोलें',
    'Live weather centered on': 'लाइव मौसम केंद्रित है:', 'Enable location to center the live map on your current position': 'अपने वर्तमान स्थान पर मानचित्र केंद्रित करने के लिए स्थान सक्षम करें',
    'Weather radar around you': 'आपके आसपास मौसम रडार', 'What this map shows': 'यह मानचित्र क्या दिखाता है', 'INSAT satellite data': 'INSAT उपग्रह डेटा',
    'Loading live MOSDAC catalog metadata…': 'लाइव MOSDAC कैटलॉग मेटाडेटा लोड हो रहा है…', 'Live granule metadata available. Pixel imagery is not exposed by this catalog endpoint.': 'लाइव ग्रैन्यूल मेटाडेटा उपलब्ध है। इस कैटलॉग एंडपॉइंट से पिक्सेल इमेजरी उपलब्ध नहीं है।',
    'No satellite catalog metadata available.': 'उपग्रह कैटलॉग मेटाडेटा उपलब्ध नहीं है।', 'Finding your location…': 'आपका स्थान खोजा जा रहा है…', 'Use my current location': 'मेरा वर्तमान स्थान उपयोग करें',
    'Live points near': 'लाइव बिंदु यहाँ:', 'Nearby live points': 'नज़दीकी लाइव बिंदु', 'Allow location access to load weather points near you.': 'अपने पास के मौसम बिंदु लोड करने के लिए स्थान की अनुमति दें।',
    'Loading live observations…': 'लाइव अवलोकन लोड हो रहे हैं…', 'Loading live weather for your location…': 'आपके स्थान का लाइव मौसम लोड हो रहा है…',
    'Unable to load live weather': 'लाइव मौसम लोड नहीं हो सका', Retry: 'पुनः प्रयास करें', Updated: 'अपडेट किया गया', 'Data provenance:': 'डेटा स्रोत:', Source: 'स्रोत',
    'Air Quality': 'वायु गुणवत्ता', 'Hourly trend': 'प्रति घंटा रुझान', 'historical daily observations, aggregated locally into monthly and annual climate statistics.': 'दैनिक ऐतिहासिक अवलोकनों को स्थानीय रूप से मासिक और वार्षिक जलवायु आँकड़ों में बदला गया है।',
    'Loading live historical climate data for': 'लाइव ऐतिहासिक जलवायु डेटा लोड हो रहा है:', 'Enable location to load climate history for your area.': 'अपने क्षेत्र का जलवायु इतिहास लोड करने के लिए स्थान सक्षम करें।',
    'Unable to load climate history': 'जलवायु इतिहास लोड नहीं हो सका', 'Live alert from the weather data service.': 'मौसम डेटा सेवा से लाइव चेतावनी।',
    'Relative': 'सापेक्ष', 'Steady': 'स्थिर', 'Apparent': 'अनुभूत', 'Local time': 'स्थानीय समय', 'Not available': 'उपलब्ध नहीं',
    'Very low visibility': 'बहुत कम दृश्यता', 'Reduced visibility': 'कम दृश्यता', 'Clear visibility': 'साफ़ दृश्यता', 'Low exposure risk': 'कम संपर्क जोखिम',
    'Moderate — use protection': 'मध्यम — सुरक्षा अपनाएँ', 'High — use protection': 'उच्च — सुरक्षा अपनाएँ', 'Very high — avoid midday sun': 'बहुत उच्च — दोपहर की धूप से बचें',
    'Air quality is good': 'वायु गुणवत्ता अच्छी है', 'Acceptable for most people': 'अधिकांश लोगों के लिए स्वीकार्य', 'Sensitive groups should limit exposure': 'संवेदनशील समूह संपर्क सीमित करें',
    'Avoid prolonged outdoor exertion': 'लंबे समय तक बाहर मेहनत करने से बचें', 'Air quality unavailable': 'वायु गुणवत्ता उपलब्ध नहीं',
    'Live guidance for': 'लाइव मार्गदर्शन:', 'your current location': 'आपका वर्तमान स्थान', 'Enable location to generate weather-conditioned guidance': 'मौसम आधारित मार्गदर्शन के लिए स्थान सक्षम करें',
    'Allow location access to receive guidance based on current weather hazards near you.': 'अपने पास के वर्तमान मौसम खतरों पर आधारित मार्गदर्शन पाने के लिए स्थान की अनुमति दें।',
    'Analysing current weather and generating grounded guidance…': 'वर्तमान मौसम का विश्लेषण और विश्वसनीय मार्गदर्शन तैयार किया जा रहा है…',
    'Unable to load live advisories': 'लाइव सलाह लोड नहीं हो सकी', 'No active hazard-based advisories': 'कोई सक्रिय खतरा-आधारित सलाह नहीं',
    "Current conditions do not meet the intelligence engine's thresholds for a safety or sector advisory.": 'वर्तमान परिस्थितियाँ सुरक्षा या क्षेत्रीय सलाह के लिए इंटेलिजेंस इंजन की सीमा तक नहीं पहुँची हैं।',
    'Valid until': 'मान्य:', Generated: 'तैयार किया गया', 'from live weather by the WeatherGPT Intelligence Engine. Guidance is decision support, not an official warning.': 'WeatherGPT इंटेलिजेंस इंजन द्वारा लाइव मौसम से। यह मार्गदर्शन निर्णय सहायता है, आधिकारिक चेतावनी नहीं।',
    'Need a tailored advisory?': 'क्या आपको विशेष सलाह चाहिए?', 'Ask WeatherGPT about your crop, flight, vessel, commute, or city ward for guidance grounded in the latest weather context.': 'अपने खेत, उड़ान, नाव, यात्रा या शहर के क्षेत्र के बारे में नवीनतम मौसम पर आधारित मार्गदर्शन के लिए WeatherGPT से पूछें।',
    'Powered by IMD, GFS & WRF': 'IMD, GFS और WRF द्वारा संचालित', 'Agriculture': 'कृषि', 'Aviation': 'विमानन', 'Marine': 'समुद्री', 'Urban planning': 'शहरी योजना', 'Emergency planning': 'आपातकालीन योजना', 'General safety': 'सामान्य सुरक्षा',
    'Avg high': 'औसत अधिकतम', 'Avg low': 'औसत न्यूनतम', 'Mean temp': 'औसत तापमान', 'Temp': 'तापमान', 'Precipitation probability': 'वर्षा की संभावना',
    'Aggregated from daily data': 'दैनिक डेटा से एकत्रित', 'Annual rainfall': 'वार्षिक वर्षा', 'Historical total': 'ऐतिहासिक कुल', 'Calculated from archive': 'अभिलेख से गणना',
    'Historical archive': 'ऐतिहासिक अभिलेख', 'NOAA GFS has': 'NOAA GFS में', 'real model points available.': 'वास्तविक मॉडल बिंदु उपलब्ध हैं।',
    'NOAA GFS · live model data': 'NOAA GFS · लाइव मॉडल डेटा', 'waiting for ingestion': 'डेटा प्राप्त होने की प्रतीक्षा', 'wind': 'हवा',
    'Data provenance': 'डेटा स्रोत', 'Live weather data': 'लाइव मौसम डेटा', 'Confidence': 'विश्वसनीयता', 'Retrieved': 'प्राप्त किया गया',
  },
  Bengali: {
    'Your region': 'আপনার অঞ্চল', 'Extreme Weather Alerts': 'চরম আবহাওয়ার সতর্কতা', 'Verify official IMD bulletins': 'সরকারি IMD বুলেটিন যাচাই করুন',
    'Official warning': 'সরকারি সতর্কতা', 'WeatherGPT intelligence': 'WeatherGPT বুদ্ধিমত্তা', 'Open official bulletin': 'সরকারি বুলেটিন খুলুন',
    'Weather radar around you': 'আপনার চারপাশের আবহাওয়া রাডার', 'What this map shows': 'এই মানচিত্রে যা দেখা যায়', 'INSAT satellite data': 'INSAT উপগ্রহ তথ্য',
    'Finding your location…': 'আপনার অবস্থান খোঁজা হচ্ছে…', 'Use my current location': 'আমার বর্তমান অবস্থান ব্যবহার করুন', 'Nearby live points': 'কাছাকাছি লাইভ পয়েন্ট',
    'Loading live observations…': 'লাইভ পর্যবেক্ষণ লোড হচ্ছে…', 'Air Quality': 'বায়ুর গুণমান', 'Hourly trend': 'ঘণ্টাভিত্তিক প্রবণতা',
    Retry: 'আবার চেষ্টা করুন', Updated: 'আপডেট হয়েছে', Source: 'উৎস', 'Data provenance:': 'ডেটার উৎস:',
    Humidity: 'আর্দ্রতা', Wind: 'বাতাস', Pressure: 'চাপ', Visibility: 'দৃশ্যমানতা', 'UV Index': 'UV সূচক', 'Dew Point': 'শিশিরাঙ্ক', Sunrise: 'সূর্যোদয়', Sunset: 'সূর্যাস্ত',
  },
  Tamil: {
    'Your region': 'உங்கள் பகுதி', 'Extreme Weather Alerts': 'தீவிர வானிலை எச்சரிக்கைகள்', 'Verify official IMD bulletins': 'அதிகாரப்பூர்வ IMD அறிவிப்புகளைச் சரிபார்க்கவும்',
    'Official warning': 'அதிகாரப்பூர்வ எச்சரிக்கை', 'WeatherGPT intelligence': 'WeatherGPT நுண்ணறிவு', 'Open official bulletin': 'அதிகாரப்பூர்வ அறிவிப்பைத் திறக்கவும்',
    'Weather radar around you': 'உங்களைச் சுற்றியுள்ள வானிலை ரேடார்', 'What this map shows': 'இந்த வரைபடம் காட்டுவது', 'INSAT satellite data': 'INSAT செயற்கைக்கோள் தரவு',
    'Finding your location…': 'உங்கள் இருப்பிடம் தேடப்படுகிறது…', 'Use my current location': 'என் தற்போதைய இருப்பிடத்தைப் பயன்படுத்தவும்', 'Nearby live points': 'அருகிலுள்ள நேரடி புள்ளிகள்',
    'Loading live observations…': 'நேரடி கண்காணிப்புகள் ஏற்றப்படுகின்றன…', 'Air Quality': 'காற்றின் தரம்', 'Hourly trend': 'மணிநேர போக்கு',
    Retry: 'மீண்டும் முயற்சி', Updated: 'புதுப்பிக்கப்பட்டது', Source: 'மூலம்', 'Data provenance:': 'தரவு ஆதாரம்:',
    Humidity: 'ஈரப்பதம்', Wind: 'காற்று', Pressure: 'அழுத்தம்', Visibility: 'தெரிவுநிலை', 'UV Index': 'UV குறியீடு', 'Dew Point': 'பனிப்புள்ளி', Sunrise: 'சூரிய உதயம்', Sunset: 'சூரிய அஸ்தமனம்',
  },
  Telugu: {
    'Your region': 'మీ ప్రాంతం', 'Extreme Weather Alerts': 'తీవ్రమైన వాతావరణ హెచ్చరికలు', 'Verify official IMD bulletins': 'అధికారిక IMD బులెటిన్‌లను ధృవీకరించండి',
    'Official warning': 'అధికారిక హెచ్చరిక', 'WeatherGPT intelligence': 'WeatherGPT మేధస్సు', 'Open official bulletin': 'అధికారిక బులెటిన్ తెరవండి',
    'Weather radar around you': 'మీ చుట్టూ వాతావరణ రాడార్', 'What this map shows': 'ఈ పటం చూపేది', 'INSAT satellite data': 'INSAT ఉపగ్రహ డేటా',
    'Finding your location…': 'మీ స్థానాన్ని కనుగొంటోంది…', 'Use my current location': 'నా ప్రస్తుత స్థానాన్ని ఉపయోగించండి', 'Nearby live points': 'సమీపంలోని లైవ్ పాయింట్లు',
    'Loading live observations…': 'లైవ్ పరిశీలనలు లోడ్ అవుతున్నాయి…', 'Air Quality': 'గాలి నాణ్యత', 'Hourly trend': 'గంటవారీ ధోరణి',
    Retry: 'మళ్లీ ప్రయత్నించండి', Updated: 'నవీకరించబడింది', Source: 'మూలం', 'Data provenance:': 'డేటా మూలం:',
    Humidity: 'తేమ', Wind: 'గాలి', Pressure: 'పీడనం', Visibility: 'దృశ్యమానత', 'UV Index': 'UV సూచిక', 'Dew Point': 'మంచు బిందువు', Sunrise: 'సూర్యోదయం', Sunset: 'సూర్యాస్తమయం',
  },
  Marathi: {
    'Your region': 'तुमचा प्रदेश', 'Extreme Weather Alerts': 'अत्यंत हवामान सूचना', 'Verify official IMD bulletins': 'अधिकृत IMD बुलेटिन तपासा',
    'Official warning': 'अधिकृत इशारा', 'WeatherGPT intelligence': 'WeatherGPT बुद्धिमत्ता', 'Open official bulletin': 'अधिकृत बुलेटिन उघडा',
    'Weather radar around you': 'तुमच्या आसपासचे हवामान रडार', 'What this map shows': 'हा नकाशा काय दाखवतो', 'INSAT satellite data': 'INSAT उपग्रह डेटा',
    'Finding your location…': 'तुमचे स्थान शोधत आहे…', 'Use my current location': 'माझे वर्तमान स्थान वापरा', 'Nearby live points': 'जवळचे थेट बिंदू',
    'Loading live observations…': 'थेट निरीक्षणे लोड होत आहेत…', 'Air Quality': 'हवेची गुणवत्ता', 'Hourly trend': 'तासाचा कल',
    Retry: 'पुन्हा प्रयत्न करा', Updated: 'अद्यतनित', Source: 'स्रोत', 'Data provenance:': 'डेटा स्रोत:',
    Humidity: 'आर्द्रता', Wind: 'वारा', Pressure: 'दाब', Visibility: 'दृश्यता', 'UV Index': 'UV निर्देशांक', 'Dew Point': 'दवबिंदू', Sunrise: 'सूर्योदय', Sunset: 'सूर्यास्त',
  },
  Gujarati: {
    'Your region': 'તમારો પ્રદેશ', 'Extreme Weather Alerts': 'આત્યંતિક હવામાન ચેતવણીઓ', 'Verify official IMD bulletins': 'સત્તાવાર IMD બુલેટિન ચકાસો',
    'Official warning': 'સત્તાવાર ચેતવણી', 'WeatherGPT intelligence': 'WeatherGPT બુદ્ધિ', 'Open official bulletin': 'સત્તાવાર બુલેટિન ખોલો',
    'Weather radar around you': 'તમારી આસપાસનું હવામાન રડાર', 'What this map shows': 'આ નકશો શું બતાવે છે', 'INSAT satellite data': 'INSAT ઉપગ્રહ ડેટા',
    'Finding your location…': 'તમારું સ્થાન શોધી રહ્યા છીએ…', 'Use my current location': 'મારું વર્તમાન સ્થાન વાપરો', 'Nearby live points': 'નજીકના લાઇવ પોઇન્ટ્સ',
    'Loading live observations…': 'લાઇવ અવલોકનો લોડ થઈ રહ્યા છે…', 'Air Quality': 'હવાની ગુણવત્તા', 'Hourly trend': 'કલાકદીઠ વલણ',
    Retry: 'ફરી પ્રયાસ કરો', Updated: 'અપડેટ થયું', Source: 'સ્રોત', 'Data provenance:': 'ડેટા સ્રોત:',
    Humidity: 'ભેજ', Wind: 'પવન', Pressure: 'દબાણ', Visibility: 'દૃશ્યતા', 'UV Index': 'UV સૂચકાંક', 'Dew Point': 'ઝાકળ બિંદુ', Sunrise: 'સૂર્યોદય', Sunset: 'સૂર્યાસ્ત',
  },
  Kannada: {
    'Your region': 'ನಿಮ್ಮ ಪ್ರದೇಶ', 'Extreme Weather Alerts': 'ತೀವ್ರ ಹವಾಮಾನ ಎಚ್ಚರಿಕೆಗಳು', 'Verify official IMD bulletins': 'ಅಧಿಕೃತ IMD ಬುಲೆಟಿನ್‌ಗಳನ್ನು ಪರಿಶೀಲಿಸಿ',
    'Official warning': 'ಅಧಿಕೃತ ಎಚ್ಚರಿಕೆ', 'WeatherGPT intelligence': 'WeatherGPT ಬುದ್ಧಿಮತ್ತೆ', 'Open official bulletin': 'ಅಧಿಕೃತ ಬುಲೆಟಿನ್ ತೆರೆಯಿರಿ',
    'Weather radar around you': 'ನಿಮ್ಮ ಸುತ್ತಲಿನ ಹವಾಮಾನ ರಾಡಾರ್', 'What this map shows': 'ಈ ನಕ್ಷೆ ತೋರಿಸುವುದು', 'INSAT satellite data': 'INSAT ಉಪಗ್ರಹ ಡೇಟಾ',
    'Finding your location…': 'ನಿಮ್ಮ ಸ್ಥಳ ಹುಡುಕಲಾಗುತ್ತಿದೆ…', 'Use my current location': 'ನನ್ನ ಪ್ರಸ್ತುತ ಸ್ಥಳ ಬಳಸಿ', 'Nearby live points': 'ಹತ್ತಿರದ ಲೈವ್ ಪಾಯಿಂಟ್‌ಗಳು',
    'Loading live observations…': 'ಲೈವ್ ವೀಕ್ಷಣೆಗಳು ಲೋಡ್ ಆಗುತ್ತಿವೆ…', 'Air Quality': 'ಗಾಳಿಯ ಗುಣಮಟ್ಟ', 'Hourly trend': 'ಗಂಟೆಯ ಪ್ರವೃತ್ತಿ',
    Retry: 'ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ', Updated: 'ನವೀಕರಿಸಲಾಗಿದೆ', Source: 'ಮೂಲ', 'Data provenance:': 'ಡೇಟಾ ಮೂಲ:',
    Humidity: 'ತೇವಾಂಶ', Wind: 'ಗಾಳಿ', Pressure: 'ಒತ್ತಡ', Visibility: 'ಗೋಚರತೆ', 'UV Index': 'UV ಸೂಚ್ಯಂಕ', 'Dew Point': 'ಇಬ್ಬನಿ ಬಿಂದು', Sunrise: 'ಸೂರ್ಯೋದಯ', Sunset: 'ಸೂರ್ಯಾಸ್ತ',
  },
  Odia: {
    'Your region': 'ଆପଣଙ୍କ ଅଞ୍ଚଳ', 'your current area': 'ଆପଣଙ୍କ ବର୍ତ୍ତମାନ ଅଞ୍ଚଳ', 'Verify official IMD bulletins': 'ସରକାରୀ IMD ବୁଲେଟିନ୍ ଯାଞ୍ଚ କରନ୍ତୁ',
    'Official warning': 'ସରକାରୀ ସତର୍କତା', 'WeatherGPT intelligence': 'WeatherGPT ବୁଦ୍ଧିମତ୍ତା', 'Open official bulletin': 'ସରକାରୀ ବୁଲେଟିନ୍ ଖୋଲନ୍ତୁ',
    'Weather radar around you': 'ଆପଣଙ୍କ ଚାରିପାଖର ପାଣିପାଗ ରାଡାର', 'What this map shows': 'ଏହି ମାନଚିତ୍ର ଯାହା ଦେଖାଏ',
    'INSAT satellite data': 'INSAT ଉପଗ୍ରହ ଡାଟା', 'Finding your location…': 'ଆପଣଙ୍କ ଅବସ୍ଥାନ ଖୋଜାଯାଉଛି…',
    'Use my current location': 'ମୋ ବର୍ତ୍ତମାନ ଅବସ୍ଥାନ ବ୍ୟବହାର କରନ୍ତୁ', 'Nearby live points': 'ନିକଟସ୍ଥ ଲାଇଭ୍ ବିନ୍ଦୁ',
    'Loading live observations…': 'ଲାଇଭ୍ ଅବଲୋକନ ଲୋଡ୍ ହେଉଛି…', 'Powered by IMD, GFS & WRF': 'IMD, GFS ଏବଂ WRF ଦ୍ୱାରା ପରିଚାଳିତ',
    'Live guidance for': 'ଲାଇଭ୍ ମାର୍ଗଦର୍ଶନ:', 'your current location': 'ଆପଣଙ୍କ ବର୍ତ୍ତମାନ ଅବସ୍ଥାନ',
    'No active hazard-based advisories': 'କୌଣସି ସକ୍ରିୟ ବିପଦ-ଆଧାରିତ ପରାମର୍ଶ ନାହିଁ',
    'Need a tailored advisory?': 'ଆପଣଙ୍କୁ ବିଶେଷ ପରାମର୍ଶ ଦରକାର କି?', 'Valid until': 'ପର୍ଯ୍ୟନ୍ତ ବୈଧ',
  },
}

for (const language of languages) {
  translations[language] = { ...translations[language], ...screenCopy[language] }
}

type LanguageContextValue = {
  language: AppLanguage
  setLanguage: (language: AppLanguage) => void
  t: (text: string) => string
  label: (language: AppLanguage) => string
}

const LanguageContext = createContext<LanguageContextValue | null>(null)

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<AppLanguage>('English')

  useEffect(() => {
    const saved = window.localStorage.getItem('weathergpt.language')
    if (saved && languages.includes(saved as AppLanguage)) setLanguageState(saved as AppLanguage)
  }, [])

  const setLanguage = (next: AppLanguage) => {
    setLanguageState(next)
    window.localStorage.setItem('weathergpt.language', next)
  }

  useEffect(() => {
    const locale = language === 'English'
      ? 'en'
      : language === 'Odia'
        ? 'or'
        : language
    document.documentElement.lang = locale
  }, [language])

  // A few data widgets are rendered by reusable chart/map components and
  // cannot receive the context directly. Localize their exact text nodes too.
  useEffect(() => {
    if (language === 'English') return
    const translate = () => {
      const dictionary = translations[language]
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)
      const nodes: Text[] = []
      let node: Node | null
      while ((node = walker.nextNode())) {
        if (node.textContent?.trim() && node.parentElement?.tagName !== 'SCRIPT' && node.parentElement?.tagName !== 'STYLE') {
          nodes.push(node as Text)
        }
      }
      for (const textNode of nodes) {
        const original = textNode.textContent?.trim()
        if (!original) continue
        const translated = dictionary[original]
        if (translated) textNode.textContent = textNode.textContent?.replace(original, translated) ?? translated
      }
    }
    translate()
    const observer = new MutationObserver(translate)
    observer.observe(document.body, { childList: true, subtree: true })
    return () => observer.disconnect()
  }, [language])

  const value = useMemo(() => ({
    language,
    setLanguage,
    t: (text: string) => translations[language][text] ?? text,
    label: (value: AppLanguage) => languageLabels[value],
  }), [language])

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (!context) throw new Error('useLanguage must be used within LanguageProvider')
  return context
}
