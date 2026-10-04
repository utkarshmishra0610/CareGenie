"""AI health assistance, structured symptom extraction, and emergency triage service."""
import re
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.ai.adaptive import AdaptiveQuestionEngine
from app.ai.prompts import (
    EMERGENCY_SIGNS,
    MANDATORY_DISCLAIMER_EN,
    MANDATORY_DISCLAIMERS,
    SPECIALTY_RULES,
)
from app.models.chat import ChatSession
from app.prediction.symptom_data import (
    find_matching_symptoms,
    get_diseases_for_symptoms,
)
from app.schemas.ai import AIHealthResponse, StructuredSymptoms
from app.schemas.chat import ChatMessageCreate
from app.services import chat_service


def extract_duration(text: str) -> Optional[str]:
    """Extracts reported duration pattern from patient text."""
    # Strip age mentions like '21 years old', '21 yrs old' before duration extraction
    cleaned = re.sub(r"\b\d+\s*(?:years? old|yrs? old|y/o)\b", "", text, flags=re.IGNORECASE)
    pattern = r"\b(?:for|since|last|past)?\s*(\d+\s*(?:days?|weeks?|months?|hours?|years?))\b"
    match = re.search(pattern, cleaned, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    if "yesterday" in text.lower():
        return "1 day"
    if "today" in text.lower():
        return "less than 24 hours"
    return None



def extract_severity(text: str) -> Optional[str]:
    """Extracts reported severity descriptor."""
    clean = text.lower()
    if any(w in clean for w in ["severe", "extreme", "unbearable", "very high", "terrible", "intense"]):
        return "severe"
    if any(w in clean for w in ["moderate", "medium", "somewhat", "quite"]):
        return "moderate"
    if any(w in clean for w in ["mild", "slight", "little", "low"]):
        return "mild"
    return None


def extract_age_gender(text: str) -> Tuple[Optional[int], Optional[str]]:
    """Extracts patient age and gender if explicitly mentioned."""
    clean = text.lower()
    age: Optional[int] = None
    gender: Optional[str] = None

    # Age extraction
    age_match = re.search(r"\b(?:i am|age|aged|i'm)?\s*(\d{1,3})\s*(?:years? old|yrs?|y/o)?\b", clean)
    if age_match:
        val = int(age_match.group(1))
        if 0 < val < 125:
            age = val

    # Gender extraction
    if re.search(r"\b(female|woman|girl)\b", clean):
        gender = "female"
    elif re.search(r"\b(male|man|boy)\b", clean):
        gender = "male"

    return age, gender


def check_emergency(symptoms: List[str], text: str) -> Tuple[bool, List[str], Optional[str]]:
    """Evaluates whether any red-flag emergency symptoms are present."""
    combined_text = (text + " " + " ".join(symptoms)).lower()
    triggered_reasons: List[str] = []
    advice: Optional[str] = None

    for emergency in EMERGENCY_SIGNS:
        for kw in emergency["keywords"]:
            if kw in combined_text:
                triggered_reasons.append(emergency["reason"])
                advice = emergency["advice"]
                break

    is_emergency = len(triggered_reasons) > 0
    return is_emergency, list(set(triggered_reasons)), advice


def extract_structured_symptoms(
    text: str, existing_symptoms: Optional[List[str]] = None
) -> StructuredSymptoms:
    """Extracts structured clinical information from free-text patient message."""
    new_symptoms = find_matching_symptoms(text)
    combined_symptoms = list(dict.fromkeys((existing_symptoms or []) + new_symptoms))

    duration = extract_duration(text)
    severity = extract_severity(text)
    age, gender = extract_age_gender(text)
    is_emergency, reasons, _ = check_emergency(combined_symptoms, text)

    primary = combined_symptoms[:3] if combined_symptoms else []
    additional = combined_symptoms[3:] if len(combined_symptoms) > 3 else []

    return StructuredSymptoms(
        symptoms=primary,
        duration=duration,
        severity=severity,
        additionalSymptoms=additional,
        age=age,
        gender=gender,
        is_emergency=is_emergency,
        emergency_reasons=reasons,
    )


def determine_suggested_specialty(
    condition_candidates: List[Tuple[str, float]], symptoms: List[str]
) -> str:
    """Maps candidate conditions and symptoms to recommended specialty."""
    if condition_candidates:
        top_condition = condition_candidates[0][0]
        if top_condition in SPECIALTY_RULES:
            return SPECIALTY_RULES[top_condition]

    # Fallback to General Physician
    return "General Physician"


def generate_conversational_response(
    user_text: str,
    structured: StructuredSymptoms,
    suggested_specialty: str,
    language: str = "en",
    adaptive_step: Optional[Dict[str, Any]] = None,
) -> AIHealthResponse:
    """Generates safety-compliant, empathetic health guidance without prescriptions."""
    lang_code = (language or "en").lower()
    disclaimer = MANDATORY_DISCLAIMERS.get(lang_code, MANDATORY_DISCLAIMER_EN)

    # Regional Emergency Responses
    EMERGENCY_REPLIES = {
        "hi": ("⚠️ **तत्काल चिकित्सा देखभाल की आवश्यकता (Seek Urgent Medical Care)**\n\n"
               "आपके द्वारा बताए गए लक्षणों में संभावित गंभीर चेतावनी संकेत शामिल हैं:\n"
               f"- {', '.join(structured.emergency_reasons)}\n\n"
               "कृपया बिना किसी देरी के नजदीकी आपातकालीन अस्पताल या आपातकालीन चिकित्सा सेवा से तुरंत संपर्क करें।"),
        "mr": ("⚠️ **तातडीने वैद्यकीय मदत घ्या (Seek Urgent Medical Care)**\n\n"
               "आपण वर्णन केलेल्या लक्षणांमध्ये गंभीर चेतावणी चिन्हे समाविष्ट आहेत:\n"
               f"- {', '.join(structured.emergency_reasons)}\n\n"
               "कृपया विलंब न करता जवळच्या आपत्कालीन रुग्णालयात जा किंवा आपत्कालीन सेवांशी (112 / 102) संपर्क साधा."),
        "bn": ("⚠️ **অবিলম্বে জরুরি চিকিৎসা সেবা নিন (Seek Urgent Medical Care)**\n\n"
               "আপনার বর্ণিত লক্ষণগুলির মধ্যে গুরুতর সতর্কতামূলক সংকেত রয়েছে:\n"
               f"- {', '.join(structured.emergency_reasons)}\n\n"
               "অবিলম্বে নিকটস্থ জরুরি হাসপাতালে যান অথবা জরুরি সেবায় (112 / 102) যোগাযোগ করুন।"),
        "te": ("⚠️ **తక్షణ అత్యవసర వైద్య సంరక్షణ అవసరం (Seek Urgent Medical Care)**\n\n"
               "మీరు వివరించిన లక్షణాలలో తీవ్రమైన హెచ్చరిక సంకేతాలు ఉన్నాయి:\n"
               f"- {', '.join(structured.emergency_reasons)}\n\n"
               "దయచేసి ఆలస్యం చేయకుండా సమీపంలోని అత్యవసర ఆసుపత్రికి వెళ్లండి లేదా అత్యవసర సేవలకు (112) కాల్ చేయండి."),
        "ta": ("⚠️ **உடனடி அவசர மருத்துவ சிகிச்சை தேவை (Seek Urgent Medical Care)**\n\n"
               "நீங்கள் விவரித்த அறிகுறிகளில் தீவிர எச்சரிக்கை அறிகுறிகள் உள்ளன:\n"
               f"- {', '.join(structured.emergency_reasons)}\n\n"
               "தயவுசெய்து உடனடியாக அருகிலுள்ள அவசர மருத்துவமனைக்குச் செல்லுங்கள் அல்லது அவசர சேவைகளை (112) அழைக்கவும்."),
        "gu": ("⚠️ **તાત્કાલિક કટોકટી તબીબી સહાય મેળવો (Seek Urgent Medical Care)**\n\n"
               "તમે વર્ણવેલ લક્ષણોમાં ગંભીર ચેતવણી સંકેતો શામેલ છે:\n"
               f"- {', '.join(structured.emergency_reasons)}\n\n"
               "કૃપા કરીને વિલંબ કર્યા વિના નજીકની કટોકટી હોસ્પિટલની મુલાકાત લો અથવા કટોકટી સેવાઓ (112) નો સંપર્ક કરો."),
        "kn": ("⚠️ **ತಕ್ಷಣದ ತುರ್ತು ವೈದ್ಯಕೀಯ ಚಿಕಿತ್ಸೆ ಅಗತ್ಯವಿದೆ (Seek Urgent Medical Care)**\n\n"
               "ನೀವು ವಿವರಿಸಿದ ರೋಗಲಕ್ಷಣಗಳಲ್ಲಿ ಗಂಭೀರ ಎಚ್ಚರಿಕೆ ಚಿಹ್ನೆಗಳು ಸೇರಿವೆ:\n"
               f"- {', '.join(structured.emergency_reasons)}\n\n"
               "ದಯವಿಟ್ಟು ವಿಳಂಬವಿಲ್ಲದೆ ಹತ್ತಿರದ ತುರ್ತು ಆಸ್ಪತ್ರೆಗೆ ಭೇಟಿ ನೀಡಿ ಅಥವಾ ತುರ್ತು ಸೇವೆಗಳಿಗೆ (112) ಕರೆ ಮಾಡಿ."),
        "pa": ("⚠️ **ਤੁਰੰਤ ਐਮਰਜੈਂਸੀ ਡਾਕਟਰੀ ਦੇਖਭਾਲ ਦੀ ਲੋੜ (Seek Urgent Medical Care)**\n\n"
               "ਤੁਹਾਡੇ ਦੁਆਰਾ ਦੱਸੇ ਗਏ ਲੱਛਣਾਂ ਵਿੱਚ ਗੰਭੀਰ ਚੇਤਾਵਨੀ ਸੰਕੇਤ ਸ਼ਾਮਲ ਹਨ:\n"
               f"- {', '.join(structured.emergency_reasons)}\n\n"
               "ਕਿਰਪਾ ਕਰਕੇ ਬਿਨਾਂ ਦੇਰੀ ਦੇ ਨਜ਼ਦੀਕੀ ਐਮਰਜੈਂਸੀ ਹਸਪਤਾਲ ਜਾਓ ਜਾਂ ਐਮਰਜੈਂਸੀ ਸੇਵਾਵਾਂ (112) 'ਤੇ ਸੰਪਰਕ ਕਰੋ।"),
    }

    # Emergency Handling
    if structured.is_emergency:
        reply = EMERGENCY_REPLIES.get(
            lang_code,
            "⚠️ **Seek Urgent Medical Care**\n\n"
            "The symptoms you described include potentially serious warning signs:\n"
            f"- {', '.join(structured.emergency_reasons)}\n\n"
            "Please proceed immediately to the nearest emergency healthcare facility or "
            "contact emergency medical services without delay."
        )
        return AIHealthResponse(
            reply_text=reply,
            structured_symptoms=structured,
            detected_emergency=True,
            emergency_advice="Please seek emergency hospital care immediately.",
            suggested_specialty="Emergency Medicine",
            disclaimer=disclaimer,
            is_ready_for_prediction=False,
            follow_up_question=None,
            candidate_conditions=[],
            missing_fields=[],
            question_turn=1,
        )

    # Standard Conversational Response
    all_syms = structured.symptoms + structured.additionalSymptoms
    syms_str = ", ".join(all_syms) if all_syms else "health symptoms"

    GREETING_LINES = {
        "hi": f"मैंने आपके बताए गए लक्षणों को दर्ज कर लिया है: **{syms_str}**।",
        "mr": f"मी तुम्ही सांगितलेली लक्षणे नोंदवली आहेत: **{syms_str}**।",
        "bn": f"আমি আপনার উল্লিখিত লক্ষণগুলি রেকর্ড করেছি: **{syms_str}**।",
        "te": f"నేను మీరు పేర్కొన్న లక్షణాలను నమోదు చేసాను: **{syms_str}**.",
        "ta": f"நீங்கள் குறிப்பிட்ட அறிகுறிகளை நான் பதிவு செய்துள்ளேன்: **{syms_str}**.",
        "gu": f"મેં તમારા જણાવેલા લક્ષણો નોંધી લીધા છે: **{syms_str}**.",
        "kn": f"ನೀವು ವರದಿ ಮಾಡಿದ ರೋಗಲಕ್ಷಣಗಳನ್ನು ನಾನು ದಾಖಲಿಸಿದ್ದೇನೆ: **{syms_str}**.",
        "pa": f"ਮੈਂ ਤੁਹਾਡੇ ਦੱਸੇ ਗਏ ਲੱਛਣਾਂ ਨੂੰ ਦਰਜ ਕਰ ਲਿਆ ਹੈ: **{syms_str}**।",
    }
    SPECIALTY_LINES = {
        "hi": f"\nप्रारंभिक मूल्यांकन के आधार पर, आप उचित चिकित्सीय परीक्षण के लिए **{suggested_specialty}** से परामर्श करने पर विचार कर सकते हैं।",
        "mr": f"\nप्राथमिक मूल्यांकनानुसार, आपण योग्य वैद्यकीय तपासणीसाठी **{suggested_specialty}** चा सल्ला घेण्याचा विचार करू शकता.",
        "bn": f"\nপ্রাথমিক মূল্যায়নের ভিত্তিতে, আপনি উপযুক্ত চিকিৎসার জন্য **{suggested_specialty}**-এর সাথে পরামর্শ করার কথা বিবেচনা করতে পারেন।",
        "te": f"\nప్రాథమిక అంచనా ఆధారంగా, మీరు సరైన వైద్య పరీక్ష కోసం **{suggested_specialty}** ని సంప్రదించడాన్ని పరిశీలించవచ్చు.",
        "ta": f"\nஆரம்ப மதிப்பீட்டின் அடிப்படையில், நீங்கள் முறையான மருத்துவ பரிசோதனைக்கு **{suggested_specialty}**-ஐ அணுகுவது நல்லது.",
        "gu": f"\nપ્રારંભિક મૂલ્યાંકનના આધારે, તમે યોગ્ય તબીબી તપાસ માટે **{suggested_specialty}** ની સલાહ લેવાનું વિચારી શકો છો.",
        "kn": f"\nಪ್ರಾಥಮಿಕ ಮೌಲ್ಯಮಾಪನದ ಆಧಾರದ ಮೇಲೆ, ನೀವು ಸರಿಯಾದ ವೈದ್ಯಕೀಯ ತಪಾಸಣೆಗಾಗಿ **{suggested_specialty}** ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಬಹುದು.",
        "pa": f"\nਸ਼ੁਰੂਆਤੀ ਮੁਲਾਂਕਣ ਦੇ ਆਧਾਰ 'ਤੇ, ਤੁਸੀਂ ਸਹੀ ਡਾਕਟਰੀ ਜਾਂਚ ਲਈ **{suggested_specialty}** ਨਾਲ ਸਲਾਹ ਕਰਨ ਬਾਰੇ ਵਿਚਾਰ ਕਰ ਸਕਦੇ ਹੋ।",
    }

    greeting = GREETING_LINES.get(
        lang_code,
        f"Thank you for sharing. I have recorded your symptoms: **{syms_str}**."
    )
    specialty_text = SPECIALTY_LINES.get(
        lang_code,
        f"\nBased on preliminary evaluation, you may consider consulting a **{suggested_specialty}** for professional medical evaluation."
    )

    reply_lines = [greeting]
    if structured.duration:
        dur_label = {
            "hi": "अवधि", "mr": "कालावधी", "bn": "সময়কাল", "te": "వ్యవధి",
            "ta": "கால அளவு", "gu": "સમયગાળો", "kn": "ಅವಧಿ", "pa": "ਸਮਾਂ"
        }.get(lang_code, "Duration noted")
        reply_lines.append(f"{dur_label}: **{structured.duration}**।")
    if structured.severity:
        sev_label = {
            "hi": "तीव्रता", "mr": "तीव्रता", "bn": "তীব্রতা", "te": "తీవ్రత",
            "ta": "தீவிரம்", "gu": "તીવ્રતા", "kn": "ತೀವ್ರತೆ", "pa": "ਤੀਬਰਤਾ"
        }.get(lang_code, "Reported intensity")
        reply_lines.append(f"{sev_label}: **{structured.severity}**।")

    reply_lines.append(specialty_text)

    follow_up_q = None
    is_ready = False
    candidates = []
    missing = []
    q_turn = 1

    if adaptive_step:
        follow_up_q = adaptive_step.get("next_question")
        is_ready = adaptive_step.get("is_ready_for_prediction", False)
        candidates = adaptive_step.get("candidate_conditions", [])
        missing = adaptive_step.get("missing_fields", [])
        q_turn = adaptive_step.get("question_turn", 1)
        if follow_up_q:
            reply_lines.append(f"\n\n❓ {follow_up_q}")

    full_reply = " ".join(reply_lines)

    return AIHealthResponse(
        reply_text=full_reply,
        structured_symptoms=structured,
        detected_emergency=False,
        emergency_advice=None,
        suggested_specialty=suggested_specialty,
        disclaimer=disclaimer,
        follow_up_question=follow_up_q,
        is_ready_for_prediction=is_ready,
        candidate_conditions=candidates,
        missing_fields=missing,
        question_turn=q_turn,
    )


def process_chat_turn(
    db: Session, session: ChatSession, user_message_text: str
) -> AIHealthResponse:
    """Executes a complete chat interaction turn: records messages and returns AI response."""
    # 1. Retrieve prior session symptoms
    prior_messages = chat_service.get_session_messages(db, session.user_id, session.id) or []
    prior_symptoms: List[str] = []
    for msg in prior_messages:
        if msg.extra_metadata and "detected_symptoms" in msg.extra_metadata:
            prior_symptoms.extend(msg.extra_metadata["detected_symptoms"])

    # 2. Extract structured symptoms
    structured = extract_structured_symptoms(
        user_message_text, existing_symptoms=prior_symptoms
    )
    all_detected = list(dict.fromkeys(structured.symptoms + structured.additionalSymptoms))

    # 3. Find candidate conditions and suggested specialty
    candidates = get_diseases_for_symptoms(all_detected)
    suggested_specialty = determine_suggested_specialty(candidates, all_detected)

    # 4. Adaptive Questioning Logic
    adaptive_step = AdaptiveQuestionEngine.determine_next_step(
        session=session,
        current_text=user_message_text,
        structured=structured,
        language=session.language,
    )

    # 5. Record user message
    user_msg_in = ChatMessageCreate(
        sender="user",
        content=user_message_text,
        extra_metadata={
            "detected_symptoms": all_detected,
            "duration": structured.duration,
            "severity": structured.severity,
        },
    )
    chat_service.add_message(db, session=session, message_in=user_msg_in)

    # 6. Generate AI response
    ai_response = generate_conversational_response(
        user_text=user_message_text,
        structured=structured,
        suggested_specialty=suggested_specialty,
        language=session.language,
        adaptive_step=adaptive_step,
    )

    # 7. Record assistant message
    assistant_msg_in = ChatMessageCreate(
        sender="assistant",
        content=ai_response.reply_text,
        extra_metadata={
            "structured_symptoms": structured.model_dump(),
            "suggested_specialty": suggested_specialty,
            "is_emergency": structured.is_emergency,
            "disclaimer": ai_response.disclaimer,
            "asked_symptom": adaptive_step.get("asked_symptom"),
            "is_ready_for_prediction": ai_response.is_ready_for_prediction,
            "candidate_conditions": ai_response.candidate_conditions,
            "question_turn": ai_response.question_turn,
        },
    )
    chat_service.add_message(db, session=session, message_in=assistant_msg_in)

    return ai_response
