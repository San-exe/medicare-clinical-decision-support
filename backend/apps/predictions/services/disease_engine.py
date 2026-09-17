import math
from typing import List, Dict, Any

DISEASE_PROFILES = {
    "Influenza": {
        "prior": 0.12,
        "severity": "moderate",
        "weights": {
            "fever": 2.8,
            "chills": 2.2,
            "fatigue": 2.5,
            "body_aches": 2.7,
            "headache": 1.9,
            "cough": 1.6,
            "sore_throat": 1.1,
            "rhinorrhea": 0.5,
        },
        "red_flags": ["dyspnea", "chest_pain"],
        "recommendation": "Rest, hydration, antiviral therapy within 48h if indicated. Seek urgent care if breathing difficulty develops.",
    },
    "Common Cold": {
        "prior": 0.25,
        "severity": "low",
        "weights": {
            "rhinorrhea": 3.0,
            "sore_throat": 2.5,
            "cough": 1.8,
            "fatigue": 0.8,
            "fever": 0.5,  # typically low grade or absent in adults
            "headache": 0.6,
        },
        "red_flags": ["dyspnea", "chest_pain"],
        "recommendation": "Symptomatic relief with rest, fluids, and over-the-counter decongestants. Self-limiting in 7-10 days.",
    },
    "Pneumonia": {
        "prior": 0.05,
        "severity": "high",
        "weights": {
            "dyspnea": 3.2,
            "fever": 2.9,
            "cough": 2.8,
            "chest_pain": 2.6,
            "chills": 2.0,
            "fatigue": 1.8,
        },
        "red_flags": ["chest_pain", "dyspnea"],
        "recommendation": "Requires urgent medical assessment, chest auscultation/imaging, and prompt antimicrobial therapy.",
    },
    "Type 2 Diabetes": {
        "prior": 0.10,
        "severity": "moderate",
        "weights": {
            "polyuria": 3.4,
            "polydipsia": 3.5,
            "fatigue": 1.8,
            "blurred_vision": 2.1,
            "weight_loss": 2.0,
        },
        "red_flags": [],
        "recommendation": "Schedule fasting blood glucose and HbA1c screening with a primary care physician.",
    },
    "Hypertension": {
        "prior": 0.15,
        "severity": "moderate",
        "weights": {
            "headache": 1.9,
            "dizziness": 2.2,
            "blurred_vision": 2.0,
            "chest_pain": 1.5,
            "fatigue": 1.0,
        },
        "red_flags": ["chest_pain", "blurred_vision"],
        "recommendation": "Monitor blood pressure consecutively. Seek emergency care if systolic > 180 mmHg or symptomatic crisis occurs.",
    },
    "Migraine": {
        "prior": 0.08,
        "severity": "moderate",
        "weights": {
            "headache": 3.8,
            "photophobia": 3.5,
            "nausea": 2.6,
            "dizziness": 1.5,
            "fatigue": 1.2,
        },
        "red_flags": [],
        "recommendation": "Rest in a quiet, dark environment. Consider triptans or NSAIDs as prescribed by your neurologist.",
    },
    "Acute Gastroenteritis": {
        "prior": 0.10,
        "severity": "moderate",
        "weights": {
            "diarrhea": 3.8,
            "nausea": 3.2,
            "fatigue": 1.5,
            "fever": 1.2,
            "body_aches": 1.0,
        },
        "red_flags": [],
        "recommendation": "Oral rehydration solution (ORS) is paramount to prevent electrolyte depletion. Monitor for severe dehydration.",
    },
    "Bronchial Asthma": {
        "prior": 0.07,
        "severity": "high",
        "weights": {
            "dyspnea": 3.5,
            "cough": 2.5,
            "chest_pain": 2.0,
            "fatigue": 1.2,
        },
        "red_flags": ["dyspnea", "chest_pain"],
        "recommendation": "Use prescribed inhaled bronchodilator rescue inhaler. Seek immediate emergency care if peak flow drops severely.",
    },
}


def predict_diseases(feature_vector: Dict[str, int]) -> Dict[str, Any]:
    """
    Executes multi-class disease prediction over binary/multi-hot feature vector.
    Returns normalized probabilities summing strictly to 1.0 and ranked differential diagnoses.
    """
    raw_scores = {}
    present_symptoms = [sym for sym, val in feature_vector.items() if val > 0]

    for disease, profile in DISEASE_PROFILES.items():
        # Start with log prior
        score = math.log(profile["prior"])

        # Accumulate symptom weights
        weights = profile["weights"]
        for symptom in present_symptoms:
            if symptom in weights:
                score += weights[symptom]
            else:
                # Slight penalty for unrelated present symptoms
                score -= 0.15

        # Penalty for missing core defining symptoms
        for core_sym, w in weights.items():
            if w >= 2.5 and core_sym not in present_symptoms:
                score -= 0.35

        raw_scores[disease] = score

    # Softmax normalization for calibrated probabilities
    max_score = max(raw_scores.values())
    exp_scores = {d: math.exp(s - max_score) for d, s in raw_scores.items()}
    total_exp = sum(exp_scores.values())

    ranked = []
    for disease, exp_s in exp_scores.items():
        prob = exp_s / total_exp
        profile = DISEASE_PROFILES[disease]

        # Determine severity dynamically
        severity = profile["severity"]
        if any(rf in present_symptoms for rf in profile["red_flags"]):
            if "chest_pain" in present_symptoms or ("dyspnea" in present_symptoms and "fever" in present_symptoms):
                severity = "critical"
            else:
                severity = "high"

        ranked.append({
            "disease": disease,
            "probability": round(prob, 4),
            "severity": severity,
            "recommendation": profile["recommendation"],
        })

    # Sort descending by probability
    ranked.sort(key=lambda x: x["probability"], reverse=True)

    # Ensure probabilities sum strictly to 1.0
    prob_sum = sum(item["probability"] for item in ranked)
    if prob_sum > 0:
        # Re-normalize slight rounding residue
        diff = 1.0 - prob_sum
        ranked[0]["probability"] = round(ranked[0]["probability"] + diff, 4)

    top_prediction = ranked[0]

    return {
        "top_prediction": top_prediction,
        "ranked_diagnoses": ranked,
        "present_symptoms": present_symptoms,
        "model_metadata": {
            "model_name": "MediCare-Clinical-Inference-Engine",
            "model_version": "2.1.0-baseline",
            "total_classes": len(DISEASE_PROFILES),
            "features_evaluated": len(present_symptoms),
        },
    }
