"""Prompt templates, safety guardrails, and clinical navigation rules."""
from typing import Dict

MANDATORY_DISCLAIMER_EN = (
    "Disclaimer: This assistant provides preliminary health-risk assessment and healthcare "
    "navigation guidance only. It is not a clinical diagnosis or treatment prescription. "
    "Please consult a licensed medical doctor for proper diagnosis and medical care."
)

MANDATORY_DISCLAIMER_HI = (
    "अस्वीकरण: यह सहायक केवल प्रारंभिक स्वास्थ्य जोखिम मूल्यांकन और स्वास्थ्य देखभाल नेविगेशन मार्गदर्शन प्रदान करता है। "
    "यह कोई चिकित्सीय निदान या दवा का नुस्खा नहीं है। कृपया उचित जांच और परामर्श के लिए किसी योग्य चिकित्सक से संपर्क करें।"
)

MANDATORY_DISCLAIMERS = {
    "en": MANDATORY_DISCLAIMER_EN,
    "hi": MANDATORY_DISCLAIMER_HI,
    "mr": "अस्वीकरण: हा सहाय्यक केवळ प्राथमिक आरोग्य जोखीम मूल्यांकन आणि आरोग्य सेवा नेव्हिगेशन मार्गदर्शन प्रदान करतो. हे वैद्यकीय निदान किंवा उपचारांची प्रिस्क्रिप्शन नाही. योग्य वैद्यकीय सल्ल्यासाठी नेहमी नोंदणीकृत वैद्यकीय डॉक्टरांचा सल्ला घ्या.",
    "bn": "দাবিত্যাগ: এই সহায়ক কেবল প্রাথমিক স্বাস্থ্য-ঝুঁকি মূল্যায়ন এবং স্বাস্থ্যসেবা নেভিগেশন নির্দেশনা প্রদান করে। এটি কোনো ক্লিনিকাল রোগ নির্ণয় বা চিকিৎসার প্রেসক্রিপশন নয়। সঠিক রোগ নির্ণয় ও চিকিৎসার জন্য সর্বদা লাইসেন্সপ্রাপ্ত চিকিৎসকের পরামর্শ নিন।",
    "te": "నిరాకరణ: ఈ సహాయకుడు ప్రాథమిక ఆరోగ్య-ప్రమాద అంచనా మరియు ఆరోగ్య సంరక్షణ నావిగేషన్ మార్గదర్శకత్వాన్ని మాత్రమే అందిస్తుంది. ఇది వైద్య నిర్ధారణ లేదా చికిత్స ప్రిస్క్రిప్షన్ కాదు. సరైన వైద్య సంరక్షణ కోసం ఎల్లప్పుడూ లైసెన్స్ పొందిన వైద్యుడిని సంప్రదించండి.",
    "ta": "மறுப்பு: இந்த உதவியாளர் ஆரம்ப சுகாதார-ஆபத்து மதிப்பீடு மற்றும் சுகாதார வழிகாட்டுதலை மட்டுமே வழங்குகிறது. இது மருத்துவ நோயறிதல் அல்லது சிகிச்சை பரிந்துரை அல்ல. தகுந்த மருத்துவ ஆலோசனைக்கு எப்போதும் உரிமம் பெற்ற மருத்துவரை அணுகவும்.",
    "gu": "અસ્વીકરણ: આ સહાયક માત્ર પ્રારંભિક આરોગ્ય-જોખમ મૂલ્યાંકન અને આરોગ્યસંભાળ નેવિગેશન માર્ગદર્શન પૂરું પાડે છે. તે કોઈ તબીબી નિદાન અથવા સારવાર પ્રિસ્ક્રિપ્શન નથી. યોગ્ય તબીબી સલાહ માટે હંમેશા લાયસન્સ ધરાવતા ડૉક્ટરનો સંપર્ક કરો.",
    "kn": "ಹಕ್ಕುತ್ಯಾಗ: ಈ ಸಹಾಯಕವು ಪ್ರಾಥಮಿಕ ಆರೋಗ್ಯ-ಅಪಾಯದ ಮೌಲ್ಯಮಾಪನ ಮತ್ತು ಆರೋಗ್ಯ ನ್ಯಾವಿಗೇಷನ್ ಮಾರ್ಗದರ್ಶನವನ್ನು ಮಾತ್ರ ಒದಗಿಸುತ್ತದೆ. ಇದು ವೈದ್ಯಕೀಯ ರೋಗನಿರ್ಣಯ ಅಥವಾ ಚಿಕಿತ್ಸೆಯ ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ಅಲ್ಲ. ಸರಿಯಾದ ವೈದ್ಯಕೀಯ ಆರೈಕೆಗಾಗಿ ಯಾವಾಗಲೂ ಪರವಾನಗಿ ಪಡೆದ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
    "pa": "ਬੇਦਾਅਵਾ: ਇਹ ਸਹਾਇਕ ਸਿਰਫ਼ ਸ਼ੁਰੂਆਤੀ ਸਿਹਤ-ਖ਼ਤਰੇ ਦਾ ਮੁਲਾਂਕਣ ਅਤੇ ਸਿਹਤ ਸੰਭਾਲ ਮਾਰਗਦਰਸ਼ਨ ਪ੍ਰਦਾਨ ਕਰਦਾ ਹੈ। ਇਹ ਕੋਈ ਡਾਕਟਰੀ ਨਿਦਾਨ ਜਾਂ ਇਲਾਜ ਦਾ ਨੁਸਖ਼ਾ ਨਹੀਂ ਹੈ। ਸਹੀ ਡਾਕਟਰੀ ਦੇਖਭਾਲ ਲਈ ਹਮੇਸ਼ਾ ਇੱਕ ਲਾਇਸੰਸਸ਼ੁਦਾ ਡਾਕਟਰ ਨਾਲ ਸਲਾਹ ਕਰੋ।",
}

# Critical warning signs requiring emergency care recommendation
EMERGENCY_SIGNS = [
    {
        "keywords": [
            "chest pain", "heart attack", "crushing chest", "radiating arm", "cold sweat",
            "छाती में तेज दर्द", "सीने में तेज दर्द", "seene me tez dard", "dil ka daura",
            "छातीत तीव्र कळ", "छातीत असह्य वेदना", "বুকে তীব্র ব্যথা", "గుండెలో తీవ్రమైన నొప్పి",
            "நெஞ்சில் கடுமையான வலி", "છાતીમાં અસહ્ય દુખાવો", "ಎದೆಯಲ್ಲಿ ತೀವ್ರ ನೋವು", "ਛਾਤੀ ਵਿੱਚ ਤੇਜ਼ ਦਰਦ"
        ],
        "reason": "Potential acute cardiac emergency (heart attack / acute coronary syndrome)",
        "advice": "Seek immediate emergency medical care or call local emergency services immediately."
    },
    {
        "keywords": [
            "face drooping", "slurred speech", "one side body", "paralysis", "stroke",
            "लकवा", "lakwa", "bolne me dikkat", "behosh", "behoshi",
            "पक्षाघात", "প্যারালাইসিস", "పక్షవాతం", "பக்கவாதம்", "લકવો", "ಪಾರ್ಶ್ವವಾಯು", "ਅਧਰੰਗ"
        ],
        "reason": "Potential neurological emergency (stroke / acute brain ischemia)",
        "advice": "Seek immediate emergency medical attention (Call emergency services right away)."
    },
    {
        "keywords": [
            "cannot breathe", "severe shortness of breath", "choking", "gasping",
            "सांस रुकना", "saans ruk rahi", "saans lene me bahut dikkat",
            "श्वास कोंडणे", "শ্বাস বন্ধ হয়ে যাওয়া", "శ్వాస ఆడకపోవడం", "மூச்சுத் திணறல்",
            "શ્વાસ રુંધાવો", "ಉಸಿರುಗಟ್ಟುವಿಕೆ", "ਸਾਹ ਘੁੱਟਣਾ"
        ],
        "reason": "Acute respiratory distress or airway compromise",
        "advice": "Seek urgent emergency medical care immediately."
    },
    {
        "keywords": [
            "coughing blood", "vomiting blood", "blood loss childbirth",
            "खून की उल्टी", "khoon ki ulti", "khoon aana",
            "रक्ताची उलटी", "রক্ত বমি", "రక్తం వాంతి", "இரத்த வாந்தி",
            "લોહીની ઉલટી", "ರಕ್ತ ವಾಂತಿ", "ਖੂਨ ਦੀ ਉਲਟੀ"
        ],
        "reason": "Severe or acute hemorrhage",
        "advice": "Visit the nearest emergency healthcare facility without delay."
    },
    {
        "keywords": [
            "stiff neck", "photophobia", "seizure", "delirium", "unconscious",
            "दौरा", "daura", "gardhan me akad",
            "झटका", "খিঁচুনি", "మూర్ఛ", "வலிப்பு", "આંચકી", "ಫಿಟ್ಸ್", "ਦੌਰੇ"
        ],
        "reason": "Possible severe neurological or infectious emergency (e.g., meningitis or encephalitis)",
        "advice": "Seek immediate hospital emergency evaluation."
    }
]


# Specialty recommendation mapping
SPECIALTY_RULES: Dict[str, str] = {
    # Cardiac / Vascular
    "Coronary Heart Disease": "Cardiologist",
    "Myocardial Infarction (Heart Attack)": "Cardiologist / Emergency Medicine",
    "Pericarditis": "Cardiologist",
    "Congestive heart disease": "Cardiologist",
    "Varicose Veins": "Vascular Specialist / General Surgeon",
    "Raynaud's Phenomenon": "Rheumatologist",
    # Respiratory / ENT
    "Asthma": "Pulmonologist",
    "Bronchitis": "Pulmonologist / General Physician",
    "Chronic obstructive pulmonary disease (COPD)": "Pulmonologist",
    "Pneumonia": "Pulmonologist / General Physician",
    "Tuberculosis": "Pulmonologist / Infectious Disease Specialist",
    "Common cold": "General Physician",
    "Influenza": "General Physician",
    "Laryngitis": "ENT Specialist",
    "Tonsillitis": "ENT Specialist",
    "Quinsy": "ENT Specialist",
    "Ear infection": "ENT Specialist",
    "Tinnitus": "ENT Specialist",
    "Nasal Polyps": "ENT Specialist",
    # Dermatology
    "Eczema": "Dermatologist",
    "Psoriasis": "Dermatologist",
    "Scabies": "Dermatologist",
    "Urticaria": "Dermatologist / Allergist",
    "Vitiligo": "Dermatologist",
    "Warts": "Dermatologist",
    "Melanoma": "Dermatologist / Oncologist",
    "Impetigo": "Dermatologist",
    "Shingles": "Dermatologist / General Physician",
    # Gastrointestinal
    "GERD": "Gastroenterologist",
    "Stomach ulcers": "Gastroenterologist",
    "Colitis": "Gastroenterologist",
    "Inflammatory Bowel Disease": "Gastroenterologist",
    "Irritable bowel syndrome": "Gastroenterologist",
    "Celiacs disease": "Gastroenterologist",
    "Hepatitis A": "Gastroenterologist / Hepatologist",
    "Hepatitis B": "Gastroenterologist / Hepatologist",
    "Hepatitis C": "Gastroenterologist / Hepatologist",
    "Jaundice": "Gastroenterologist / General Physician",
    "Food Poisoning": "General Physician",
    "Amoebiasis": "General Physician / Gastroenterologist",
    "Cholera": "Infectious Disease / General Physician",
    "Dysentery": "General Physician",
    "Appendicitis": "General Surgeon",
    # Neurology
    "Migraine": "Neurologist",
    "Epilepsy": "Neurologist",
    "Parkinson's Disease": "Neurologist",
    "Multiple sclerosis": "Neurologist",
    "Stroke": "Neurologist / Emergency Medicine",
    "Bell's Palsy": "Neurologist",
    "Sciatica": "Orthopedic / Neurologist",
    "Myasthenia gravis": "Neurologist",
    "Dementia": "Neurologist / Geriatrician",
    "Alzheimer": "Neurologist / Geriatrician",
    # Musculoskeletal
    "Arthritis": "Rheumatologist / Orthopedic",
    "Osteoarthritis": "Orthopedic Surgeon",
    "Osteoporosis": "Orthopedic / Endocrinologist",
    "Osteomyelitis": "Orthopedic Surgeon / Infectious Disease Specialist",
    "Fibromyalgia": "Rheumatologist",
    "Tennis elbow": "Orthopedic / Physiotherapist",
    "Carpal Tunnel Syndrome": "Orthopedic / Neurologist",
    "Shin splints": "Sports Medicine / Orthopedic",
    # Endocrinology
    "Diabetes Mellitus": "Endocrinologist",
    "Hyperthyroidism": "Endocrinologist",
    "Hypothyroid": "Endocrinologist",
    "Goitre": "Endocrinologist",
    # Ophthalmology
    "Glaucoma": "Ophthalmologist",
    "Cataract": "Ophthalmologist",
    "Myopia": "Ophthalmologist / Optometrist",
    "Hypermetropia": "Ophthalmologist / Optometrist",
    "Astigmatism": "Ophthalmologist",
    "Presbyopia": "Ophthalmologist",
    "Diabetic Retinopathy": "Ophthalmologist / Retina Specialist",
    "Chalazion": "Ophthalmologist",
    "Iritis": "Ophthalmologist",
    "Corneal Abrasion": "Ophthalmologist",
    # Gynecology / Obstetrics
    "Polycystic ovary syndrome (PCOS)": "Gynecologist",
    "Endometriosis": "Gynecologist",
    "Fibroids": "Gynecologist",
    "High risk pregnancy": "Obstetrician / Gynecologist",
    "Eclampsia": "Obstetrician / Gynecologist",
    "Ectopic pregnancy": "Obstetrician / Gynecologist",
    "Pelvic inflammatory disease": "Gynecologist",
    "Premenstrual syndrome": "Gynecologist",
    # Infectious Diseases
    "Dengue": "General Physician / Infectious Disease Specialist",
    "Malaria": "General Physician / Infectious Disease Specialist",
    "Chikungunya Fever": "General Physician",
    "COVID-19": "General Physician / Pulmonologist",
    "Coronavirus disease 2019 (COVID-19)": "General Physician / Pulmonologist",
    "Typhoid": "General Physician",
    "Paratyphoid fever": "General Physician",
    "Rabies": "Emergency Medicine / Infectious Disease",
    "Tetanus": "Emergency Medicine / Infectious Disease",
    "Sepsis": "Emergency Medicine / Critical Care",
    # Dental
    "Cavities": "Dentist",
    "Bleeding Gums": "Dentist / Periodontist",
    "Bad Breath (Halitosis)": "Dentist",
    # Oncology
    "Cancer": "Oncologist",
    "Breast Cancer / Carcinoma": "Oncologist / Breast Surgeon",
    "Lung cancer": "Oncologist / Pulmonologist",
    "Colorectal Cancer": "Oncologist / Gastroenterologist",
    "Leukemia": "Hematologist / Oncologist",
    "Lymphoma": "Hematologist / Oncologist",
    # Psychiatry
    "Anxiety": "Psychiatrist / Clinical Psychologist",
    "Depression": "Psychiatrist / Clinical Psychologist",
    "Postpartum depression/ Perinatal depression": "Psychiatrist / Obstetrician",
    "Insomnia": "Sleep Specialist / General Physician",
    "Obsessive Compulsive Disorder": "Psychiatrist",
    "Schizophrenia": "Psychiatrist",
    "Autism": "Pediatrician / Child Psychiatrist",
}
