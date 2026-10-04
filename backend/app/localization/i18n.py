"""Multilingual localization and regional Hindi/Hinglish symptom mapping engine."""
import json
import os
from typing import Any, Dict

LOCALE_DIR = os.path.dirname(__file__)

_LOCALES: Dict[str, Dict[str, Any]] = {}


def load_locales():
    """Loads localized JSON catalogs from disk dynamically."""
    global _LOCALES
    _LOCALES.clear()
    if os.path.exists(LOCALE_DIR):
        for fname in os.listdir(LOCALE_DIR):
            if fname.endswith(".json"):
                code = fname[:-5].lower()
                path = os.path.join(LOCALE_DIR, fname)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        _LOCALES[code] = json.load(f)
                except Exception as e:
                    print(f"Error loading locale {fname}: {e}")


load_locales()


def get_locale_data(lang: str = "en") -> Dict[str, Any]:
    """Retrieves full localization catalog for specified language."""
    code = lang.lower() if lang.lower() in _LOCALES else "en"
    return _LOCALES.get(code, _LOCALES.get("en", {}))


def translate(key: str, lang: str = "en", default: str = "") -> str:
    """Fetches localized string for a dot-delimited key (e.g. 'ui.send')."""
    catalog = get_locale_data(lang)
    parts = key.split(".")
    curr = catalog
    for p in parts:
        if isinstance(curr, dict) and p in curr:
            curr = curr[p]
        else:
            return default or key
    return str(curr) if curr is not None else default or key


REGIONAL_SYMPTOM_MAP: Dict[str, str] = {
    # --- Hindi (हिन्दी) & Hinglish ---
    "बुखार": "fever",
    "तेज बुखार": "fever",
    "खांसी": "coughing",
    "सूखी खांसी": "dry cough",
    "सिर दर्द": "headache",
    "सिरदर्द": "headache",
    "बदन दर्द": "muscle joint pain",
    "बदनदर्द": "muscle joint pain",
    "जोड़ों का दर्द": "joint bone pain",
    "जोड़ दर्द": "joint bone pain",
    "पेट दर्द": "stomach pain",
    "पेट में दर्द": "stomach pain",
    "छाती में दर्द": "chest pain",
    "सीने में दर्द": "chest pain",
    "सांस लेने में तकलीफ": "difficulty breathing",
    "सांस फूलना": "difficulty breathing",
    "सांस लेने में कठिनाई": "difficulty breathing",
    "उल्टी": "vomiting",
    "दस्त": "diarrhea",
    "चक्कर": "dizziness",
    "चक्कर आना": "dizziness",
    "थकान": "fatigue",
    "कमजोरी": "fatigue",
    "गले में खराश": "sore throat",
    "खुजली": "itchiness",
    "लाल चकत्ते": "red rash",

    # Latin / Hinglish transliteration symptoms
    "bukhar": "fever",
    "bukhaar": "fever",
    "tez bukhar": "fever",
    "khansi": "coughing",
    "khaasi": "coughing",
    "sukhi khansi": "dry cough",
    "sar dard": "headache",
    "sir dard": "headache",
    "sardard": "headache",
    "sirdard": "headache",
    "badan dard": "muscle joint pain",
    "badandard": "muscle joint pain",
    "jism dard": "muscle joint pain",
    "jodon ka dard": "joint bone pain",
    "jod dard": "joint bone pain",
    "pet dard": "stomach pain",
    "pet me dard": "stomach pain",
    "chhati me dard": "chest pain",
    "seene me dard": "chest pain",
    "seene me jalan": "burning stabbing pain",
    "saans phoolna": "difficulty breathing",
    "saans lene me taklif": "difficulty breathing",
    "saans lene me dikkat": "difficulty breathing",
    "ulti": "vomiting",
    "dast": "diarrhea",
    "chakkar": "dizziness",
    "chakkar aana": "dizziness",
    "thakan": "fatigue",
    "thakawat": "fatigue",
    "kamzori": "fatigue",
    "gale me kharash": "sore throat",
    "khujli": "itchiness",
    "chakatte": "red rash",

    # --- Marathi (मराठी) ---
    "ताप": "fever",
    "खोकला": "coughing",
    "कोरडा खोकला": "dry cough",
    "डोकेदुखी": "headache",
    "डोके दुखणे": "headache",
    "अंगदुखी": "muscle joint pain",
    "पोटदुखी": "stomach pain",
    "पोटात दुखणे": "stomach pain",
    "छातीत दुखणे": "chest pain",
    "छातीत भरून येणे": "chest pain",
    "श्वास घेण्यास त्रास": "difficulty breathing",
    "दम लागणे": "difficulty breathing",
    "उलट्या": "vomiting",
    "उलटी": "vomiting",
    "जुलाब": "diarrhea",
    "हगवण": "diarrhea",
    "चक्कर येणे": "dizziness",
    "थकवा": "fatigue",
    "अशक्तपणा": "fatigue",
    "घसा खवखवणे": "sore throat",
    "खाज": "itchiness",
    "लाल पुरळ": "red rash",
    # Marathi transliteration
    "dokedukhi": "headache",
    "potat dukhne": "stomach pain",
    "angdukhi": "muscle joint pain",
    "chhatit dukhne": "chest pain",
    "dam laagne": "difficulty breathing",

    # --- Bengali (বাংলা) ---
    "জ্বর": "fever",
    "কাশি": "coughing",
    "শুকনো কাশি": "dry cough",
    "মাথা ব্যথা": "headache",
    "মাথাব্যথা": "headache",
    "গা ব্যথা": "muscle joint pain",
    "শরীর ব্যথা": "muscle joint pain",
    "পেট ব্যথা": "stomach pain",
    "পেটে ব্যথা": "stomach pain",
    "বুকে ব্যথা": "chest pain",
    "শ্বাসকষ্ট": "difficulty breathing",
    "শ্বাস নিতে কষ্ট": "difficulty breathing",
    "বমি": "vomiting",
    "ডায়রিয়া": "diarrhea",
    "পাতলা পায়খানা": "diarrhea",
    "মাথা ঘোরা": "dizziness",
    "ক্লান্তি": "fatigue",
    "দুর্বলতা": "fatigue",
    "গলা ব্যথা": "sore throat",
    "চুলকানি": "itchiness",
    "লাল ফুসকুড়ি": "red rash",
    # Bengali transliteration
    "matha betha": "headache",
    "pete betha": "stomach pain",
    "buke betha": "chest pain",
    "shwaskosto": "difficulty breathing",

    # --- Telugu (తెలుగు) ---
    "జ్వరం": "fever",
    "దగ్గు": "coughing",
    "పొడి దగ్గు": "dry cough",
    "తలనొప్పి": "headache",
    "ఒళ్లు నొప్పులు": "muscle joint pain",
    "కడుపు నొప్పి": "stomach pain",
    "గుండె నొప్పి": "chest pain",
    "ఛాతీ నొప్పి": "chest pain",
    "శ్వాస తీసుకోవడంలో ఇబ్బంది": "difficulty breathing",
    "ఆయాసం": "difficulty breathing",
    "వాంతులు": "vomiting",
    "విరేచనాలు": "diarrhea",
    "కళ్ళు తిరగడం": "dizziness",
    "అలసట": "fatigue",
    "నీరసం": "fatigue",
    "గొంతు నొప్పి": "sore throat",
    "దురద": "itchiness",
    "ఎర్రటి దద్దుర్లు": "red rash",
    # Telugu transliteration
    "jwaram": "fever",
    "daggu": "coughing",
    "talanopi": "headache",
    "kadupu noppi": "stomach pain",
    "chati noppi": "chest pain",

    # --- Tamil (தமிழ்) ---
    "காய்ச்சல்": "fever",
    "இருமல்": "coughing",
    "வறட்டு இருமல்": "dry cough",
    "தலைவலி": "headache",
    "உடல் வலி": "muscle joint pain",
    "வயிற்று வலி": "stomach pain",
    "மார்பு வலி": "chest pain",
    "நெஞ்சு வலி": "chest pain",
    "மூச்சுத் திணறல்": "difficulty breathing",
    "வாந்தி": "vomiting",
    "வயிற்றுப்போக்கு": "diarrhea",
    "தலைச்சுற்றல்": "dizziness",
    "சோர்வு": "fatigue",
    "தொண்டை வலி": "sore throat",
    "அரிப்பு": "itchiness",
    "சிவப்பு தடிப்புகள்": "red rash",
    # Tamil transliteration
    "kaaichal": "fever",
    "irumal": "coughing",
    "thalaivali": "headache",
    "vayitru vali": "stomach pain",
    "nenju vali": "chest pain",
    "moochu thinaral": "difficulty breathing",

    # --- Gujarati (ગુજરાતી) ---
    "તાવ": "fever",
    "ઉધરસ": "coughing",
    "સૂકી ઉધરસ": "dry cough",
    "માથાનો દુખાવો": "headache",
    "અંગનો દુખાવો": "muscle joint pain",
    "શરીરનો દુખાવો": "muscle joint pain",
    "પેટમાં દુખાવો": "stomach pain",
    "છાતીમાં દુખાવો": "chest pain",
    "શ્વાસ લેવામાં તકલીફ": "difficulty breathing",
    "દમ ચડવો": "difficulty breathing",
    "ઉલટી": "vomiting",
    "ઝાડા": "diarrhea",
    "ચક્કર": "dizziness",
    "થાક": "fatigue",
    "નબળાઈ": "fatigue",
    "ગળામાં દુખાવો": "sore throat",
    "ખંજવાળ": "itchiness",
    "લાલ ચકામા": "red rash",
    # Gujarati transliteration
    "taav": "fever",
    "udharas": "coughing",
    "mathano dukhavo": "headache",
    "petma dukhavo": "stomach pain",
    "chhatima dukhavo": "chest pain",

    # --- Kannada (ಕನ್ನಡ) ---
    "ಜ್ವರ": "fever",
    "ಕೆಮ್ಮು": "coughing",
    "ಒಣ ಕೆಮ್ಮು": "dry cough",
    "ತಲೆನೋವು": "headache",
    "ಮೈಕೈ ನೋವು": "muscle joint pain",
    "ಹೊಟ್ಟೆ ನೋವು": "stomach pain",
    "ಎದೆ ನೋವು": "chest pain",
    "ಉಸಿರಾಟದ ತೊಂದರೆ": "difficulty breathing",
    "ಉಬ್ಬಸ": "difficulty breathing",
    "ವಾಂತಿ": "vomiting",
    "ಭೇದಿ": "diarrhea",
    "ತಲೆತಿರುಗುವಿಕೆ": "dizziness",
    "ಆಯಾಸ": "fatigue",
    "ದಣಿವು": "fatigue",
    "ಗಂಟಲು ನೋವು": "sore throat",
    "ತುರಿಕೆ": "itchiness",
    "ಕೆಂಪು ದದ್ದುಗಳು": "red rash",

    # --- Punjabi (ਪੰਜਾਬੀ) ---
    "ਬੁਖਾਰ": "fever",
    "ਖੰਘ": "coughing",
    "ਸੁੱਕੀ ਖੰਘ": "dry cough",
    "ਸਿਰ ਦਰਦ": "headache",
    "ਸਿਰਪੀੜ": "headache",
    "ਸਰੀਰ ਦਰਦ": "muscle joint pain",
    "ਪੇਟ ਦਰਦ": "stomach pain",
    "ਢਿੱਡ ਪੀੜ": "stomach pain",
    "ਛਾਤੀ ਵਿੱਚ ਦਰਦ": "chest pain",
    "ਸਾਹ ਲੈਣ ਵਿੱਚ ਤਕਲੀਫ਼": "difficulty breathing",
    "ਸਾਹ ਫੁੱਲਣਾ": "difficulty breathing",
    "ਉਲਟੀ": "vomiting",
    "ਦਸਤ": "diarrhea",
    "ਚੱਕਰ": "dizziness",
    "ਥਕਾਵਟ": "fatigue",
    "ਕਮਜ਼ੋਰੀ": "fatigue",
    "ਗਲੇ ਵਿੱਚ ਦਰਦ": "sore throat",
    "ਖਾਰਸ਼": "itchiness",
    "ਲਾਲ ਧੱਫੜ": "red rash",
}

# Alias for backward compatibility
HINDI_SYMPTOM_MAP = REGIONAL_SYMPTOM_MAP

