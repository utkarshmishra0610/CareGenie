"""Symptom taxonomy and disease dataset helper module."""
import csv
import os
from typing import Dict, List, Set, Tuple

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "disease_symptoms.csv")


def load_dataset_metadata() -> Tuple[List[str], List[str], Dict[str, Set[str]]]:
    """Loads feature symptoms, disease labels, and disease-symptom mapping."""
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        symptoms = [s.strip().lower() for s in header[1:]]

        diseases: List[str] = []
        disease_symptoms_map: Dict[str, Set[str]] = {}

        for row in reader:
            if not row or not row[0].strip():
                continue
            disease_name = row[0].strip()
            diseases.append(disease_name)
            active_symptoms = {
                symptoms[i] for i, val in enumerate(row[1:]) if val.strip() == "1"
            }
            disease_symptoms_map[disease_name] = active_symptoms

    return symptoms, diseases, disease_symptoms_map


SYMPTOMS, DISEASES, DISEASE_SYMPTOMS_MAP = load_dataset_metadata()


COLLOQUIAL_SYMPTOM_MAP = {
    "cough": "coughing",
    "coughing": "coughing",
    "body pain": "muscle joint pain",
    "body ache": "muscle joint pain",
    "body aches": "muscle joint pain",
    "joint pain": "joint bone pain",
    "stomach ache": "stomach pain",
    "belly pain": "stomach pain",
    "tummy ache": "stomach pain",
    "shortness of breath": "shortness breath",
    "difficulty breathing": "difficulty breathing",
    "breathlessness": "shortness breath",
    "high fever": "fever",
    "tiredness": "fatigue",
    "exhaustion": "fatigue",
    "rash": "red rash",
}



def find_matching_symptoms(text: str) -> List[str]:
    """Matches text keywords against recognized symptoms, colloquial aliases, and Hindi terms."""
    clean_text = text.lower()
    matched: List[str] = []

    # 1. Check Hindi and Hinglish regional vocabulary
    try:
        from app.localization.i18n import HINDI_SYMPTOM_MAP
        for term, canonical in HINDI_SYMPTOM_MAP.items():
            if term.lower() in clean_text and canonical not in matched:
                matched.append(canonical)
    except ImportError:
        pass

    # 2. Check colloquial English aliases
    for alias, canonical in COLLOQUIAL_SYMPTOM_MAP.items():
        if alias in clean_text and canonical not in matched:
            matched.append(canonical)

    # 3. Check standardized dataset symptom features
    for symptom in SYMPTOMS:
        if symptom in clean_text and symptom not in matched:
            matched.append(symptom)

    return matched




def get_diseases_for_symptoms(user_symptoms: List[str]) -> List[Tuple[str, float]]:
    """Calculates symptom overlap score for each disease."""
    if not user_symptoms:
        return []

    user_set = {s.lower().strip() for s in user_symptoms}
    results = []

    for disease, disease_syms in DISEASE_SYMPTOMS_MAP.items():
        if not disease_syms:
            continue
        common = user_set.intersection(disease_syms)
        if common:
            overlap_score = len(common) / len(disease_syms)
            results.append((disease, overlap_score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results
