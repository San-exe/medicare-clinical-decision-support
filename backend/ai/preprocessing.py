"""
MediCare Clinical Decision Support System - Phase 1 Dynamic Clinical Preprocessor
Standardizes unstructured symptom descriptions alongside structured clinical vitals.
Enforces deterministic feature vector ordering aligned with versioned schema.json.
"""

from __future__ import annotations

import difflib
import json
import math
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional, Set, Tuple, Union

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.json")

# ---------------------------------------------------------------------------
# Canonical Clinical Symptoms & Comprehensive Synonym Catalog
# ---------------------------------------------------------------------------

CANONICAL_SYMPTOMS: List[str] = [
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

# Contrastive conjunctions that terminate negation scope immediately
CONTRASTIVE_CONJUNCTIONS: Set[str] = {
    "but",
    "however",
    "although",
    "though",
    "yet",
    "nevertheless",
    "nonetheless",
    "except",
    "while",
    "whereas",
}

# Negation triggers
NEGATION_TRIGGERS: List[str] = [
    "no history of",
    "negative for",
    "ruled out",
    "rules out",
    "no signs of",
    "denies any",
    "free of",
    "never had",
    "denies",
    "denied",
    "without",
    "absent",
    "neither",
    "never",
    "not",
    "no",
]

SYMPTOM_SYNONYMS: Dict[str, str] = {
    # Fever / Pyrexia
    "fever": "fever",
    "pyrexia": "fever",
    "high temperature": "fever",
    "feverish": "fever",
    "elevated temperature": "fever",
    "burning up": "fever",
    "febrile": "fever",
    "hot to touch": "fever",
    "elevated temp": "fever",
    "high temp": "fever",
    "pyrexial": "fever",

    # Cough
    "cough": "cough",
    "coughing": "cough",
    "dry cough": "cough",
    "hacking cough": "cough",
    "productive cough": "cough",
    "phlegm": "cough",
    "sputum": "cough",
    "barking cough": "cough",
    "persistent cough": "cough",
    "wet cough": "cough",
    "coughing fits": "cough",

    # Fatigue / Lethargy
    "fatigue": "fatigue",
    "tired": "fatigue",
    "tiredness": "fatigue",
    "exhaustion": "fatigue",
    "lethargy": "fatigue",
    "lethargic": "fatigue",
    "weakness": "fatigue",
    "feeling weak": "fatigue",
    "asthenia": "fatigue",
    "malaise": "fatigue",
    "worn out": "fatigue",
    "drowsy": "fatigue",
    "drowsiness": "fatigue",
    "lack of energy": "fatigue",
    "low energy": "fatigue",

    # Headache / Cephalalgia
    "headache": "headache",
    "head ache": "headache",
    "cephalalgia": "headache",
    "migraine": "headache",
    "throbbing headache": "headache",
    "throbbing head": "headache",
    "head is throbbing": "headache",
    "head throbbing": "headache",
    "pain in head": "headache",
    "head pain": "headache",
    "head hurting": "headache",
    "tension headache": "headache",
    "temporal headache": "headache",

    # Dyspnea / Shortness of breath
    "dyspnea": "dyspnea",
    "dyspnoea": "dyspnea",
    "shortness of breath": "dyspnea",
    "short of breath": "dyspnea",
    "sob": "dyspnea",
    "breathless": "dyspnea",
    "breathlessness": "dyspnea",
    "difficulty breathing": "dyspnea",
    "hard to breathe": "dyspnea",
    "trouble breathing": "dyspnea",
    "wheezing": "dyspnea",
    "wheeze": "dyspnea",
    "stridor": "dyspnea",
    "air hunger": "dyspnea",
    "respiratory distress": "dyspnea",

    # Chest Pain / Angina
    "chest pain": "chest_pain",
    "chest tightness": "chest_pain",
    "tight chest": "chest_pain",
    "pressure in chest": "chest_pain",
    "chest ache": "chest_pain",
    "angina": "chest_pain",
    "angina pectoris": "chest_pain",
    "chest discomfort": "chest_pain",
    "retrosternal pain": "chest_pain",
    "substernal pain": "chest_pain",
    "squeezing chest pain": "chest_pain",
    "heavy chest": "chest_pain",
    "pain in chest": "chest_pain",

    # Sore Throat / Pharyngitis
    "sore throat": "sore_throat",
    "throat pain": "sore_throat",
    "pharyngitis": "sore_throat",
    "scratchy throat": "sore_throat",
    "raw throat": "sore_throat",
    "pain swallowing": "sore_throat",
    "painful swallowing": "sore_throat",
    "odynophagia": "sore_throat",
    "throat irritation": "sore_throat",
    "inflamed throat": "sore_throat",

    # Rhinorrhea / Congestion
    "rhinorrhea": "rhinorrhea",
    "rhinorrhoea": "rhinorrhea",
    "runny nose": "rhinorrhea",
    "sneezing": "rhinorrhea",
    "nasal congestion": "rhinorrhea",
    "stuffy nose": "rhinorrhea",
    "congestion": "rhinorrhea",
    "blocked nose": "rhinorrhea",
    "post nasal drip": "rhinorrhea",
    "catarrh": "rhinorrhea",
    "coryza": "rhinorrhea",
    "congested": "rhinorrhea",

    # Polyuria
    "polyuria": "polyuria",
    "frequent urination": "polyuria",
    "peeing often": "polyuria",
    "excessive urination": "polyuria",
    "urinating frequently": "polyuria",
    "peeing constantly": "polyuria",
    "nocturia": "polyuria",
    "urinary frequency": "polyuria",
    "constant urination": "polyuria",

    # Polydipsia
    "polydipsia": "polydipsia",
    "excessive thirst": "polydipsia",
    "always thirsty": "polydipsia",
    "extreme thirst": "polydipsia",
    "thirsty": "polydipsia",
    "abnormally thirsty": "polydipsia",
    "unquenchable thirst": "polydipsia",
    "increased thirst": "polydipsia",

    # Dizziness / Vertigo
    "dizziness": "dizziness",
    "dizzy": "dizziness",
    "lightheaded": "dizziness",
    "lightheadedness": "dizziness",
    "vertigo": "dizziness",
    "feeling faint": "dizziness",
    "unsteadiness": "dizziness",
    "woozy": "dizziness",
    "wooziness": "dizziness",
    "presyncope": "dizziness",
    "feeling dizzy": "dizziness",

    # Nausea / Vomiting
    "nausea": "nausea",
    "nauseous": "nausea",
    "nauseated": "nausea",
    "vomiting": "nausea",
    "emesis": "nausea",
    "throwing up": "nausea",
    "puking": "nausea",
    "queasy": "nausea",
    "upset stomach": "nausea",
    "sick to stomach": "nausea",

    # Photophobia
    "photophobia": "photophobia",
    "sensitive to light": "photophobia",
    "light sensitivity": "photophobia",
    "eye hurt in light": "photophobia",
    "eyes hurt in bright light": "photophobia",
    "photophobic": "photophobia",
    "intolerant to light": "photophobia",

    # Body Aches / Myalgia
    "body aches": "body_aches",
    "body ache": "body_aches",
    "muscle pain": "body_aches",
    "myalgia": "body_aches",
    "muscle ache": "body_aches",
    "aching muscles": "body_aches",
    "joint pain": "body_aches",
    "arthralgia": "body_aches",
    "aching body": "body_aches",
    "sore muscles": "body_aches",
    "aches all over": "body_aches",

    # Blurred Vision
    "blurred vision": "blurred_vision",
    "blurry vision": "blurred_vision",
    "hazy vision": "blurred_vision",
    "fuzzy vision": "blurred_vision",
    "loss of visual clarity": "blurred_vision",
    "impaired vision": "blurred_vision",

    # Diarrhea
    "diarrhea": "diarrhea",
    "diarrhoea": "diarrhea",
    "loose stools": "diarrhea",
    "watery stools": "diarrhea",
    "stomach cramps": "diarrhea",
    "loose motions": "diarrhea",
    "frequent bowel movements": "diarrhea",

    # Chills / Rigors
    "chills": "chills",
    "shivering": "chills",
    "shivers": "chills",
    "cold sweats": "chills",
    "rigors": "chills",
    "teeth chattering": "chills",
    "feeling chilly": "chills",

    # Weight Loss
    "weight loss": "weight_loss",
    "losing weight": "weight_loss",
    "unexplained weight loss": "weight_loss",
    "involuntary weight loss": "weight_loss",
    "rapid weight loss": "weight_loss",
    "cachexia": "weight_loss",
}

# ---------------------------------------------------------------------------
# Preprocessed Output Dataclass
# ---------------------------------------------------------------------------

@dataclass
class PreprocessedClinicalData:
    feature_order: List[str]
    imputed_vector: List[float]
    raw_vector: List[float]
    imputed_dict: Dict[str, float]
    raw_dict: Dict[str, float]
    canonical_symptoms: List[str]
    negated_symptoms: List[str]
    unmapped_tokens: List[str]
    vitals_raw: Dict[str, Any]
    vitals_imputed: Dict[str, float]
    imputed_fields: List[str]
    schema_version: str

    def to_dict(self) -> Dict[str, Any]:
        """Serializes preprocessed result to dictionary with clean NaN representation."""
        result = asdict(self)
        return result

    def get_feature_vector(self, imputed: bool = True) -> List[float]:
        """Returns ordered feature vector, either with normal imputation or preserving NaN."""
        return list(self.imputed_vector) if imputed else list(self.raw_vector)


# ---------------------------------------------------------------------------
# Clinical Preprocessor Implementation
# ---------------------------------------------------------------------------

class ClinicalPreprocessor:
    """
    Dynamic clinical preprocessor for disease-risk prediction and SHAP explainability.
    Standardizes unstructured text/symptom lists + structured vitals into deterministic vectors.
    """

    def __init__(
        self,
        schema_path: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
    ):
        self.schema_path = schema_path or SCHEMA_PATH
        if schema is not None:
            self.schema = schema
        else:
            self.schema = self._load_schema()
        self.feature_order: List[str] = self.schema.get("feature_order", [])
        self.features_spec: Dict[str, Any] = self.schema.get("features", {})
        self.version: str = self.schema.get("version", "1.0.0")

        # Compile synonym matching catalog (sorted longest phrase first)
        self.sorted_synonyms: List[Tuple[str, str]] = sorted(
            SYMPTOM_SYNONYMS.items(), key=lambda x: len(x[0]), reverse=True
        )

    def _load_schema(self) -> Dict[str, Any]:
        if os.path.exists(self.schema_path):
            with open(self.schema_path, "r", encoding="utf-8") as f:
                return json.load(f)
        raise FileNotFoundError(f"Schema file not found at: {self.schema_path}")

    @staticmethod
    def clean_text(text: str) -> str:
        """Normalizes case, whitespace, and strips special characters except clause boundaries."""
        lowered = text.lower()
        cleaned = re.sub(r"[^\w\s;.,-]", " ", lowered)
        return " ".join(cleaned.split())

    # -----------------------------------------------------------------------
    # Symptom Extraction with Bounded Negation & Contrastive Boundary
    # -----------------------------------------------------------------------

    def parse_symptoms(
        self, input_data: Union[str, List[str], Tuple[str, ...], Set[str]]
    ) -> Dict[str, Any]:
        """
        Parses symptom descriptions into canonical positive and negated symptoms.
        Enforces a bounded negation window (max 3-4 words) that breaks immediately
        on contrastive conjunctions ('but', 'however', ';', etc.).
        """
        if not input_data:
            return {
                "canonical_symptoms": [],
                "negated_symptoms": [],
                "unmapped_tokens": [],
                "symptom_vector": {c: 0.0 for c in CANONICAL_SYMPTOMS},
            }

        # Normalize input to list of clauses/tokens
        if isinstance(input_data, str):
            raw_clauses = [input_data]
        elif isinstance(input_data, (list, tuple, set)):
            raw_clauses = [str(item) for item in input_data if str(item).strip()]
        else:
            raw_clauses = [str(input_data)]

        positive_symptoms: Set[str] = set()
        negated_symptoms: Set[str] = set()
        unmapped_tokens: List[str] = []

        for raw_item in raw_clauses:
            cleaned = self.clean_text(raw_item)
            if not cleaned:
                continue

            # Split raw item into sentences/major clauses by period, semicolon, or newline
            major_clauses = re.split(r"[;.\n]+", cleaned)

            for major_clause in major_clauses:
                major_clause = major_clause.strip()
                if not major_clause:
                    continue

                # Tokenize into word tokens and strip trailing/leading punctuation
                tokens = [t.strip(",;.:-") for t in major_clause.split() if t.strip(",;.:-")]
                n = len(tokens)
                if n == 0:
                    continue

                # Process tokens with bounded negation tracking
                # Active negation state: (is_negated: bool, words_remaining: int)
                active_negation = False
                negation_budget = 0

                i = 0
                while i < n:
                    token = tokens[i]

                    # 1. Check for contrastive conjunctions -> Break negation immediately
                    if token in CONTRASTIVE_CONJUNCTIONS:
                        active_negation = False
                        negation_budget = 0
                        i += 1
                        continue

                    # 2. Check for negation triggers
                    found_neg_trigger = False
                    for trigger in NEGATION_TRIGGERS:
                        trig_words = trigger.split()
                        k = len(trig_words)
                        if i + k <= n and tokens[i : i + k] == trig_words:
                            active_negation = True
                            negation_budget = 4  # Window of 4 words
                            i += k
                            found_neg_trigger = True
                            break

                    if found_neg_trigger:
                        continue

                    # 3. Check for multi-word or single-word symptom match starting at token i
                    matched_canonical = None
                    matched_word_count = 0

                    # Try matching phrases of decreasing lengths (up to 4 words)
                    for phrase_len in range(min(4, n - i), 0, -1):
                        sub_phrase = " ".join(tokens[i : i + phrase_len])

                        # Exact synonym lookup
                        if sub_phrase in SYMPTOM_SYNONYMS:
                            matched_canonical = SYMPTOM_SYNONYMS[sub_phrase]
                            matched_word_count = phrase_len
                            break

                        # Standardized slug match (e.g. "chest_pain")
                        if sub_phrase.replace(" ", "_") in CANONICAL_SYMPTOMS:
                            matched_canonical = sub_phrase.replace(" ", "_")
                            matched_word_count = phrase_len
                            break

                        # Fuzzy match for single tokens >= 4 characters
                        if phrase_len == 1 and len(sub_phrase) >= 4:
                            fuzzy_match = self._fuzzy_match_symptom(sub_phrase)
                            if fuzzy_match:
                                matched_canonical = fuzzy_match
                                matched_word_count = 1
                                break

                    if matched_canonical:
                        if active_negation and negation_budget > 0:
                            negated_symptoms.add(matched_canonical)
                        else:
                            positive_symptoms.add(matched_canonical)

                        # Advance index and decrement negation budget
                        i += matched_word_count
                        if active_negation:
                            negation_budget -= matched_word_count
                            if negation_budget <= 0:
                                active_negation = False
                    else:
                        # Non-matching token
                        if len(token) >= 4 and token not in CONTRASTIVE_CONJUNCTIONS:
                            if token not in unmapped_tokens and not any(
                                token in syn for syn in SYMPTOM_SYNONYMS
                            ):
                                unmapped_tokens.append(token)

                        i += 1
                        if active_negation:
                            negation_budget -= 1
                            if negation_budget <= 0:
                                active_negation = False

        # Positive overrides negation only if explicitly affirmed elsewhere without negation
        # If a symptom is affirmed, remove from negated set
        final_positive = set(c for c in CANONICAL_SYMPTOMS if c in positive_symptoms)
        final_negated = set(c for c in CANONICAL_SYMPTOMS if c in negated_symptoms and c not in final_positive)

        # Build 18-dim symptom vector
        symptom_vector = {c: (1.0 if c in final_positive else 0.0) for c in CANONICAL_SYMPTOMS}

        return {
            "canonical_symptoms": [c for c in CANONICAL_SYMPTOMS if c in final_positive],
            "negated_symptoms": [c for c in CANONICAL_SYMPTOMS if c in final_negated],
            "unmapped_tokens": unmapped_tokens[:10],
            "symptom_vector": symptom_vector,
        }

    def _fuzzy_match_symptom(self, word: str, min_similarity: float = 0.82) -> Optional[str]:
        """Fuzzy matches a single word against synonym catalog using SequenceMatcher."""
        best_match = None
        best_ratio = 0.0

        for synonym, canonical in self.sorted_synonyms:
            # Only compare single words against single-word synonyms
            if " " in synonym:
                continue
            if abs(len(word) - len(synonym)) > 3:
                continue

            ratio = difflib.SequenceMatcher(None, word, synonym).ratio()
            if ratio >= min_similarity and ratio > best_ratio:
                best_ratio = ratio
                best_match = canonical

        return best_match

    # -----------------------------------------------------------------------
    # Structured Vitals Parsing, Physiological Clamping, & Unit Handling
    # -----------------------------------------------------------------------

    def parse_vitals(
        self,
        vitals_data: Optional[Dict[str, Any]] = None,
        patient_profile_data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, float], Dict[str, float], List[str]]:
        """
        Parses, validates, units-normalizes, and physiologically clamps clinical vitals.
        Returns:
            - raw_vitals: dict containing numeric float values or math.nan for missing fields.
            - imputed_vitals: dict containing numeric float values with missing fields imputed to reference normals.
            - imputed_fields: list of field names that were missing and imputed.
        """
        data: Dict[str, Any] = {}
        if patient_profile_data:
            data.update(patient_profile_data)
        if vitals_data:
            data.update(vitals_data)

        raw: Dict[str, float] = {}
        imputed: Dict[str, float] = {}
        imputed_fields: List[str] = []

        # 1. Age (Years)
        age_val = self._extract_age(data)
        if age_val is not None:
            clamped_age = self._clamp("age", age_val)
            raw["age"] = clamped_age
            imputed["age"] = clamped_age
        else:
            raw["age"] = math.nan
            imputed["age"] = self.features_spec["age"]["default_imputation"]
            imputed_fields.append("age")

        # 2. Sex (Encoded: 1.0 = Male, 0.0 = Female, 0.5 = Other/Neutral)
        sex_val = self._extract_sex(data)
        if sex_val is not None:
            clamped_sex = self._clamp("sex", sex_val)
            raw["sex"] = clamped_sex
            imputed["sex"] = clamped_sex
        else:
            raw["sex"] = math.nan
            imputed["sex"] = self.features_spec["sex"]["default_imputation"]
            imputed_fields.append("sex")

        # 3. Blood Pressure: Systolic & Diastolic (mmHg)
        sys_val, dia_val = self._extract_bp(data)

        if sys_val is not None:
            clamped_sys = self._clamp("systolic_bp", sys_val)
            raw["systolic_bp"] = clamped_sys
            imputed["systolic_bp"] = clamped_sys
        else:
            raw["systolic_bp"] = math.nan
            imputed["systolic_bp"] = self.features_spec["systolic_bp"]["default_imputation"]
            imputed_fields.append("systolic_bp")

        if dia_val is not None:
            clamped_dia = self._clamp("diastolic_bp", dia_val)
            raw["diastolic_bp"] = clamped_dia
            imputed["diastolic_bp"] = clamped_dia
        else:
            raw["diastolic_bp"] = math.nan
            imputed["diastolic_bp"] = self.features_spec["diastolic_bp"]["default_imputation"]
            imputed_fields.append("diastolic_bp")

        # Ensure systolic >= diastolic if both are present in imputed/raw
        if not math.isnan(raw["systolic_bp"]) and not math.isnan(raw["diastolic_bp"]):
            if raw["systolic_bp"] < raw["diastolic_bp"]:
                raw["systolic_bp"], raw["diastolic_bp"] = raw["diastolic_bp"], raw["systolic_bp"]
        if imputed["systolic_bp"] < imputed["diastolic_bp"]:
            imputed["systolic_bp"], imputed["diastolic_bp"] = imputed["diastolic_bp"], imputed["systolic_bp"]

        # 4. Heart Rate (bpm)
        hr_val = self._extract_numeric(data, ["heart_rate", "pulse", "hr", "pulse_rate"])
        if hr_val is not None:
            clamped_hr = self._clamp("heart_rate", hr_val)
            raw["heart_rate"] = clamped_hr
            imputed["heart_rate"] = clamped_hr
        else:
            raw["heart_rate"] = math.nan
            imputed["heart_rate"] = self.features_spec["heart_rate"]["default_imputation"]
            imputed_fields.append("heart_rate")

        # 5. Glucose (mg/dL)
        glu_val = self._extract_glucose(data)
        if glu_val is not None:
            clamped_glu = self._clamp("glucose", glu_val)
            raw["glucose"] = clamped_glu
            imputed["glucose"] = clamped_glu
        else:
            raw["glucose"] = math.nan
            imputed["glucose"] = self.features_spec["glucose"]["default_imputation"]
            imputed_fields.append("glucose")

        # 6. Body Temperature (Celsius, 30.0 - 45.0)
        temp_val = self._extract_temperature(data)
        if temp_val is not None:
            clamped_temp = self._clamp("body_temperature", temp_val)
            raw["body_temperature"] = clamped_temp
            imputed["body_temperature"] = clamped_temp
        else:
            raw["body_temperature"] = math.nan
            imputed["body_temperature"] = self.features_spec["body_temperature"]["default_imputation"]
            imputed_fields.append("body_temperature")

        # 7. Oxygen Saturation / SpO2 (%, 50 - 100)
        spo2_val = self._extract_spo2(data)
        if spo2_val is not None:
            clamped_spo2 = self._clamp("oxygen_saturation", spo2_val)
            raw["oxygen_saturation"] = clamped_spo2
            imputed["oxygen_saturation"] = clamped_spo2
        else:
            raw["oxygen_saturation"] = math.nan
            imputed["oxygen_saturation"] = self.features_spec["oxygen_saturation"]["default_imputation"]
            imputed_fields.append("oxygen_saturation")

        # 8. BMI (kg/m^2, 10.0 - 70.0)
        bmi_val = self._extract_bmi(data)
        if bmi_val is not None:
            clamped_bmi = self._clamp("bmi", bmi_val)
            raw["bmi"] = clamped_bmi
            imputed["bmi"] = clamped_bmi
        else:
            raw["bmi"] = math.nan
            imputed["bmi"] = self.features_spec["bmi"]["default_imputation"]
            imputed_fields.append("bmi")

        return raw, imputed, imputed_fields

    def _clamp(self, feature_name: str, value: float) -> float:
        """Clamps a numeric feature to its physiological boundaries defined in schema."""
        spec = self.features_spec.get(feature_name, {})
        min_val = spec.get("min_val", -float("inf"))
        max_val = spec.get("max_val", float("inf"))
        return round(max(min_val, min(max_val, float(value))), 2)

    def _extract_numeric(self, data: Dict[str, Any], keys: List[str]) -> Optional[float]:
        for k in keys:
            if k in data and data[k] is not None:
                val = data[k]
                if isinstance(val, (int, float)) and not math.isnan(val):
                    return float(val)
                if isinstance(val, str):
                    m = re.search(r"[-+]?\d*\.?\d+", val)
                    if m:
                        try:
                            return float(m.group())
                        except ValueError:
                            pass
        return None

    def _extract_age(self, data: Dict[str, Any]) -> Optional[float]:
        # Direct age
        age = self._extract_numeric(data, ["age", "patient_age"])
        if age is not None:
            return age

        # From date of birth
        dob = data.get("date_of_birth") or data.get("dob")
        if dob:
            if isinstance(dob, str):
                try:
                    dob = date.fromisoformat(dob[:10])
                except Exception:
                    dob = None
            if isinstance(dob, date):
                today = date.today()
                years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                return float(years)
        return None

    def _extract_sex(self, data: Dict[str, Any]) -> Optional[float]:
        val = data.get("sex") or data.get("gender")
        if val is not None:
            if isinstance(val, (int, float)):
                return 1.0 if val == 1 else (0.0 if val == 0 else 0.5)
            s = str(val).strip().lower()
            if s in ["m", "male", "man"]:
                return 1.0
            if s in ["f", "female", "woman"]:
                return 0.0
            if s in ["other", "neutral", "non-binary", "nb"]:
                return 0.5
        return None

    def _extract_bp(self, data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
        # Combined string e.g. "120/80", "135/85 mmHg"
        bp_str = data.get("blood_pressure") or data.get("bp")
        if bp_str and isinstance(bp_str, str):
            match = re.search(r"(\d{2,3})\s*[/\\-]\s*(\d{2,3})", bp_str)
            if match:
                return float(match.group(1)), float(match.group(2))

        sys_val = self._extract_numeric(data, ["systolic_bp", "systolic", "sbp", "bp_sys"])
        dia_val = self._extract_numeric(data, ["diastolic_bp", "diastolic", "dbp", "bp_dia"])
        return sys_val, dia_val

    def _extract_temperature(self, data: Dict[str, Any]) -> Optional[float]:
        for k in ["body_temperature", "temperature", "temp"]:
            if k in data and data[k] is not None:
                val = data[k]
                is_f = False
                num_val = None

                if isinstance(val, str):
                    lower = val.lower()
                    if "f" in lower or "fahrenheit" in lower:
                        is_f = True
                    m = re.search(r"[-+]?\d*\.?\d+", val)
                    if m:
                        num_val = float(m.group())
                elif isinstance(val, (int, float)):
                    num_val = float(val)

                if num_val is not None:
                    # Auto-detect Fahrenheit if not explicit: humans rarely have core temp > 45°C
                    if is_f or num_val > 45.0:
                        num_val = (num_val - 32.0) * 5.0 / 9.0
                    return num_val
        return None

    def _extract_glucose(self, data: Dict[str, Any]) -> Optional[float]:
        for k in ["glucose", "blood_glucose", "blood_sugar", "fasting_glucose", "fbs"]:
            if k in data and data[k] is not None:
                val = data[k]
                if isinstance(val, str):
                    lower = val.lower()
                    m = re.search(r"[-+]?\d*\.?\d+", val)
                    if m:
                        num = float(m.group())
                        # If unit is mmol/L (typical range 3.0-25.0)
                        if "mmol" in lower or num < 25.0:
                            num = num * 18.0182
                        return num
                elif isinstance(val, (int, float)):
                    num = float(val)
                    if num < 25.0:  # Assumed mmol/L
                        num = num * 18.0182
                    return num
        return None

    def _extract_spo2(self, data: Dict[str, Any]) -> Optional[float]:
        val = self._extract_numeric(data, ["oxygen_saturation", "spo2", "oximeter", "o2_sat"])
        if val is not None:
            if val <= 1.0:  # Fraction e.g. 0.98 -> 98%
                val = val * 100.0
            return val
        return None

    def _extract_bmi(self, data: Dict[str, Any]) -> Optional[float]:
        # Direct BMI
        bmi = self._extract_numeric(data, ["bmi", "body_mass_index"])
        if bmi is not None:
            return bmi

        # From weight and height
        weight = self._extract_numeric(data, ["weight", "weight_kg", "wt"])
        height = self._extract_numeric(data, ["height", "height_cm", "height_m", "ht"])

        if weight and height:
            # Normalize height to meters
            h_meters = height / 100.0 if height > 3.0 else height
            if h_meters > 0.4:
                return weight / (h_meters ** 2)

        return None

    # -----------------------------------------------------------------------
    # End-to-End Dynamic Preprocessing Pipeline
    # -----------------------------------------------------------------------

    def preprocess(
        self,
        input_data: Union[Dict[str, Any], str, List[str]],
        patient_profile_data: Optional[Dict[str, Any]] = None,
        patient: Optional[Any] = None,
    ) -> PreprocessedClinicalData:
        """
        Executes full preprocessing:
        1. Extracts unstructured symptoms with bounded negation and fuzzy canonicalization.
        2. Normalizes, physiologically clamps, and imputes clinical vitals.
        3. Constructs dual deterministic feature vectors (imputed vs raw NaN) strictly aligned with schema.json.
        """
        if patient is not None:
            extracted_patient_data: Dict[str, Any] = {}
            if isinstance(patient, dict):
                extracted_patient_data.update(patient)
            else:
                for attr in ["date_of_birth", "gender", "age", "sex"]:
                    if hasattr(patient, attr):
                        extracted_patient_data[attr] = getattr(patient, attr)
                if hasattr(patient, "patient_profile"):
                    profile = getattr(patient, "patient_profile")
                    if profile:
                        if hasattr(profile, "date_of_birth") and profile.date_of_birth:
                            extracted_patient_data["date_of_birth"] = profile.date_of_birth
                        if hasattr(profile, "gender") and profile.gender:
                            extracted_patient_data["gender"] = profile.gender
            if patient_profile_data is None:
                patient_profile_data = extracted_patient_data
            else:
                merged = dict(extracted_patient_data)
                merged.update(patient_profile_data)
                patient_profile_data = merged

        # Normalize container
        if isinstance(input_data, str):
            symptoms_raw: Any = input_data
            vitals_raw: Dict[str, Any] = {}
        elif isinstance(input_data, list):
            symptoms_raw = input_data
            vitals_raw = {}
        elif isinstance(input_data, dict):
            symptoms_raw = input_data.get("symptoms") or input_data.get("text") or []
            vitals_raw = dict(input_data.get("vitals", {}))
            # Also merge top-level numeric vitals
            for k in [
                "age",
                "sex",
                "gender",
                "systolic_bp",
                "diastolic_bp",
                "blood_pressure",
                "bp",
                "heart_rate",
                "glucose",
                "body_temperature",
                "temperature",
                "temp",
                "oxygen_saturation",
                "spo2",
                "bmi",
                "height",
                "weight",
                "date_of_birth",
            ]:
                if k in input_data and k not in vitals_raw:
                    vitals_raw[k] = input_data[k]
        else:
            symptoms_raw = []
            vitals_raw = {}

        # 1. Parse symptoms
        symptom_res = self.parse_symptoms(symptoms_raw)
        canonical_symptoms = symptom_res["canonical_symptoms"]
        negated_symptoms = symptom_res["negated_symptoms"]
        unmapped_tokens = symptom_res["unmapped_tokens"]
        symptom_vector = symptom_res["symptom_vector"]

        # 2. Parse vitals
        raw_vitals, imputed_vitals, imputed_fields = self.parse_vitals(
            vitals_data=vitals_raw,
            patient_profile_data=patient_profile_data,
        )

        # 3. Construct dual representations in strict schema.json order
        imputed_vector: List[float] = []
        raw_vector: List[float] = []
        imputed_dict: Dict[str, float] = {}
        raw_dict: Dict[str, float] = {}

        for feat in self.feature_order:
            spec = self.features_spec.get(feat, {})
            category = spec.get("category", "")

            if category == "symptom":
                # Symptom value is binary 0.0 or 1.0 (both in raw and imputed)
                val = symptom_vector.get(feat, 0.0)
                imputed_vector.append(val)
                raw_vector.append(val)
                imputed_dict[feat] = val
                raw_dict[feat] = val
            else:
                # Vital / demographic
                imp_val = imputed_vitals.get(feat, spec.get("default_imputation", 0.0))
                r_val = raw_vitals.get(feat, math.nan)

                imputed_vector.append(float(imp_val))
                raw_vector.append(float(r_val))
                imputed_dict[feat] = float(imp_val)
                raw_dict[feat] = float(r_val)

        return PreprocessedClinicalData(
            feature_order=list(self.feature_order),
            imputed_vector=imputed_vector,
            raw_vector=raw_vector,
            imputed_dict=imputed_dict,
            raw_dict=raw_dict,
            canonical_symptoms=canonical_symptoms,
            negated_symptoms=negated_symptoms,
            unmapped_tokens=unmapped_tokens,
            vitals_raw=vitals_raw,
            vitals_imputed=imputed_vitals,
            imputed_fields=imputed_fields,
            schema_version=self.version,
        )


# ---------------------------------------------------------------------------
# Singleton & Backward-Compatible Service Hooks
# ---------------------------------------------------------------------------

_PREPROCESSOR_INSTANCE: Optional[ClinicalPreprocessor] = None


def get_preprocessor() -> ClinicalPreprocessor:
    """Returns singleton preprocessor instance."""
    global _PREPROCESSOR_INSTANCE
    if _PREPROCESSOR_INSTANCE is None:
        _PREPROCESSOR_INSTANCE = ClinicalPreprocessor()
    return _PREPROCESSOR_INSTANCE


def preprocess_clinical_input(
    data: Union[Dict[str, Any], str, List[str]],
    patient: Optional[Any] = None,
) -> PreprocessedClinicalData:
    """
    Convenience backward-compatible entry point.
    Resolves patient profile metadata if patient or patient_id is available.
    """
    preprocessor = get_preprocessor()
    patient_profile_data: Dict[str, Any] = {}

    # Extract patient profile if model instance or patient_id is provided
    if patient is not None and hasattr(patient, "patient_profile"):
        profile = getattr(patient, "patient_profile", None)
        if profile:
            if hasattr(profile, "date_of_birth") and profile.date_of_birth:
                patient_profile_data["date_of_birth"] = profile.date_of_birth
            if hasattr(profile, "gender") and profile.gender:
                patient_profile_data["gender"] = profile.gender
    elif isinstance(data, dict) and data.get("patient_id"):
        try:
            from apps.accounts.models import User
            target_user = User.objects.filter(id=data["patient_id"]).first()
            if target_user and hasattr(target_user, "patient_profile"):
                profile = getattr(target_user, "patient_profile", None)
                if profile:
                    if hasattr(profile, "date_of_birth") and profile.date_of_birth:
                        patient_profile_data["date_of_birth"] = profile.date_of_birth
                    if hasattr(profile, "gender") and profile.gender:
                        patient_profile_data["gender"] = profile.gender
        except Exception:
            pass  # Non-blocking if Django or DB is unavailable during unit testing

    return preprocessor.preprocess(data, patient_profile_data=patient_profile_data)
