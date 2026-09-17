import re
from typing import List, Dict, Union, Any

CANONICAL_SYMPTOMS = [
    "fever",
    "cough",
    "fatigue",
    "headache",
    "dyspnea",
    "chest_pain",
    "sore_throat",
    "rhinorrhea",
    "polyuria",
    "polydipsia",
    "dizziness",
    "nausea",
    "photophobia",
    "body_aches",
    "blurred_vision",
    "diarrhea",
    "chills",
    "weight_loss",
]

SYMPTOM_SYNONYMS: Dict[str, str] = {
    # Fever
    "fever": "fever",
    "high temperature": "fever",
    "feverish": "fever",
    "pyrexia": "fever",
    "temp": "fever",
    "elevated temperature": "fever",
    "burning up": "fever",
    # Cough
    "cough": "cough",
    "coughing": "cough",
    "dry cough": "cough",
    "hacking cough": "cough",
    "productive cough": "cough",
    "phlegm": "cough",
    "barking cough": "cough",
    # Fatigue
    "fatigue": "fatigue",
    "tired": "fatigue",
    "tiredness": "fatigue",
    "exhaustion": "fatigue",
    "lethargy": "fatigue",
    "weakness": "fatigue",
    "drowsiness": "fatigue",
    "feeling weak": "fatigue",
    # Headache
    "headache": "headache",
    "head ache": "headache",
    "head hurting": "headache",
    "throbbing headache": "headache",
    "throbbing head": "headache",
    "head is throbbing": "headache",
    "head throbbing": "headache",
    "pain in head": "headache",
    "head pain": "headache",
    "migraine": "headache",
    # Dyspnea / Breathlessness
    "dyspnea": "dyspnea",
    "shortness of breath": "dyspnea",
    "breathless": "dyspnea",
    "breathlessness": "dyspnea",
    "difficulty breathing": "dyspnea",
    "hard to breathe": "dyspnea",
    "wheezing": "dyspnea",
    "wheeze": "dyspnea",
    # Chest Pain
    "chest pain": "chest_pain",
    "chest tightness": "chest_pain",
    "tight chest": "chest_pain",
    "pressure in chest": "chest_pain",
    "chest ache": "chest_pain",
    "angina": "chest_pain",
    "chest discomfort": "chest_pain",
    # Sore Throat
    "sore throat": "sore_throat",
    "throat pain": "sore_throat",
    "scratchy throat": "sore_throat",
    "pain swallowing": "sore_throat",
    "pharyngitis": "sore_throat",
    # Rhinorrhea / Runny nose / Sneezing
    "rhinorrhea": "rhinorrhea",
    "runny nose": "rhinorrhea",
    "sneezing": "rhinorrhea",
    "nasal congestion": "rhinorrhea",
    "stuffy nose": "rhinorrhea",
    "congestion": "rhinorrhea",
    "blocked nose": "rhinorrhea",
    # Polyuria
    "polyuria": "polyuria",
    "frequent urination": "polyuria",
    "peeing often": "polyuria",
    "excessive urination": "polyuria",
    "urinating frequently": "polyuria",
    "peeing constantly": "polyuria",
    # Polydipsia
    "polydipsia": "polydipsia",
    "excessive thirst": "polydipsia",
    "always thirsty": "polydipsia",
    "extreme thirst": "polydipsia",
    "thirsty": "polydipsia",
    # Dizziness
    "dizziness": "dizziness",
    "dizzy": "dizziness",
    "lightheaded": "dizziness",
    "lightheadedness": "dizziness",
    "vertigo": "dizziness",
    "feeling faint": "dizziness",
    # Nausea / Vomiting
    "nausea": "nausea",
    "nauseous": "nausea",
    "vomiting": "nausea",
    "throwing up": "nausea",
    "puking": "nausea",
    "queasy": "nausea",
    "upset stomach": "nausea",
    # Photophobia
    "photophobia": "photophobia",
    "sensitive to light": "photophobia",
    "light sensitivity": "photophobia",
    "eye hurt in light": "photophobia",
    # Body Aches / Myalgia
    "body aches": "body_aches",
    "body ache": "body_aches",
    "muscle pain": "body_aches",
    "myalgia": "body_aches",
    "muscle ache": "body_aches",
    "joint pain": "body_aches",
    "aching body": "body_aches",
    # Blurred Vision
    "blurred vision": "blurred_vision",
    "blurry vision": "blurred_vision",
    "hazy vision": "blurred_vision",
    "fuzzy vision": "blurred_vision",
    # Diarrhea
    "diarrhea": "diarrhea",
    "loose stools": "diarrhea",
    "watery stools": "diarrhea",
    "stomach cramps": "diarrhea",
    # Chills
    "chills": "chills",
    "shivering": "chills",
    "shivers": "chills",
    "cold sweats": "chills",
    # Weight Loss
    "weight loss": "weight_loss",
    "losing weight": "weight_loss",
    "unexplained weight loss": "weight_loss",
}

CATALOG_METADATA = [
    {"id": "fever", "label": "Fever / Pyrexia", "category": "General"},
    {"id": "cough", "label": "Cough", "category": "Respiratory"},
    {"id": "fatigue", "label": "Fatigue / Lethargy", "category": "General"},
    {"id": "headache", "label": "Headache / Migraine", "category": "Neurological"},
    {"id": "dyspnea", "label": "Shortness of Breath", "category": "Respiratory"},
    {"id": "chest_pain", "label": "Chest Pain / Tightness", "category": "Cardiovascular"},
    {"id": "sore_throat", "label": "Sore Throat", "category": "ENT"},
    {"id": "rhinorrhea", "label": "Runny Nose / Congestion", "category": "ENT"},
    {"id": "polyuria", "label": "Frequent Urination", "category": "Metabolic / Renal"},
    {"id": "polydipsia", "label": "Excessive Thirst", "category": "Metabolic"},
    {"id": "dizziness", "label": "Dizziness / Lightheadedness", "category": "Neurological"},
    {"id": "nausea", "label": "Nausea / Vomiting", "category": "Gastrointestinal"},
    {"id": "photophobia", "label": "Sensitivity to Light", "category": "Neurological / Optical"},
    {"id": "body_aches", "label": "Muscle & Body Aches", "category": "General"},
    {"id": "blurred_vision", "label": "Blurred Vision", "category": "Optical"},
    {"id": "diarrhea", "label": "Diarrhea / Abdominal Cramps", "category": "Gastrointestinal"},
    {"id": "chills", "label": "Chills / Shivering", "category": "General"},
    {"id": "weight_loss", "label": "Unexplained Weight Loss", "category": "Metabolic / General"},
]


def clean_text(text: str) -> str:
    """Normalizes case, whitespace, and strips punctuation."""
    lowered = text.lower()
    cleaned = re.sub(r"[^\w\s-]", " ", lowered)
    return " ".join(cleaned.split())


def parse_symptoms(input_data: Union[str, List[str]]) -> Dict[str, Any]:
    """
    Parses noisy free text or list of symptom strings into a canonical feature vector.
    Returns canonical symptoms, multi-hot feature vector, and unmatched tokens.
    """
    if isinstance(input_data, str):
        raw_items = [input_data]
        # Also split common delimiters (commas, 'and', semicolons, periods)
        sub_items = re.split(r"[,;.\n]|\band\b", input_data)
        raw_items.extend([s.strip() for s in sub_items if s.strip()])
    elif isinstance(input_data, (list, tuple)):
        raw_items = list(input_data)
    else:
        raw_items = [str(input_data)]

    detected_canonical = set()
    unmapped = []

    # Sort synonyms by length descending so longer phrases match first
    sorted_synonyms = sorted(SYMPTOM_SYNONYMS.items(), key=lambda x: len(x[0]), reverse=True)

    for item in raw_items:
        cleaned = clean_text(item)
        if not cleaned:
            continue

        matched_any = False
        # 1. Exact or substring match in cleaned item
        for phrase, canonical in sorted_synonyms:
            # Match whole words or boundary phrases
            pattern = r"(?:^|\b)" + re.escape(phrase) + r"(?:\b|$)"
            if re.search(pattern, cleaned):
                detected_canonical.add(canonical)
                matched_any = True

        if not matched_any and len(cleaned.split()) <= 4:
            # Check if this short token was unmatched
            if cleaned not in unmapped:
                unmapped.append(cleaned)

    canonical_list = [c for c in CANONICAL_SYMPTOMS if c in detected_canonical]
    feature_vector = {c: (1 if c in detected_canonical else 0) for c in CANONICAL_SYMPTOMS}

    return {
        "canonical_symptoms": canonical_list,
        "feature_vector": feature_vector,
        "unmapped_tokens": unmapped,
        "total_symptoms_detected": len(canonical_list),
    }


def get_canonical_symptom_catalog() -> List[Dict[str, str]]:
    """Returns catalog of all registered canonical symptoms."""
    return CATALOG_METADATA


def suggest_related_symptoms(canonical_symptoms: List[str]) -> List[str]:
    """Suggests relevant symptoms to ask the patient about based on input symptoms."""
    symptom_set = set(canonical_symptoms)
    suggestions = []

    if "cough" in symptom_set and "dyspnea" not in symptom_set:
        suggestions.append("dyspnea")
    if "fever" in symptom_set and "chills" not in symptom_set:
        suggestions.append("chills")
    if "fever" in symptom_set and "body_aches" not in symptom_set:
        suggestions.append("body_aches")
    if "polyuria" in symptom_set and "polydipsia" not in symptom_set:
        suggestions.append("polydipsia")
    if "headache" in symptom_set and "photophobia" not in symptom_set:
        suggestions.append("photophobia")
    if "nausea" in symptom_set and "diarrhea" not in symptom_set:
        suggestions.append("diarrhea")
    if "chest_pain" in symptom_set and "dyspnea" not in symptom_set:
        suggestions.append("dyspnea")

    return [s for s in suggestions if s in CANONICAL_SYMPTOMS and s not in symptom_set]
