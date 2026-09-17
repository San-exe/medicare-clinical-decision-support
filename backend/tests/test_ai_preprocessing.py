"""
Unit and integration test suite for MediCare AI Preprocessing layer (backend/ai/preprocessing.py).
Verifies:
1. Deterministic feature vector ordering against schema.json.
2. Flexible symptom input parsing (free text, lists, slugs, comma-delimited).
3. Clinical synonym mapping and fuzzy matching for typos.
4. Bounded negation scope with contrastive conjunction boundary breaking.
5. Physiological clamping and unit normalization (Fahrenheit, mmol/L, SpO2, BP strings).
6. Dual representation (imputed vectors vs native math.nan).
7. Backward-compatible hook with PatientProfile integration.
"""

import math
from datetime import date
import pytest
from ai.preprocessing import (
    ClinicalPreprocessor,
    PreprocessedClinicalData,
    preprocess_clinical_input,
    get_preprocessor,
    CANONICAL_SYMPTOMS,
)
from apps.accounts.models import User
from apps.patients.models import PatientProfile


class TestAIClinicalPreprocessing:
    @pytest.fixture(autouse=True)
    def setup_preprocessor(self):
        self.preprocessor = get_preprocessor()
        self.schema = self.preprocessor.schema

    # -----------------------------------------------------------------------
    # 1. Deterministic Feature Vector Ordering & Schema Alignment
    # -----------------------------------------------------------------------

    def test_schema_feature_order_integrity(self):
        assert self.schema["version"] == "1.0.0"
        order = self.preprocessor.feature_order
        assert len(order) == 27
        # First 18 must be canonical symptoms
        assert order[:18] == CANONICAL_SYMPTOMS
        # Last 9 must be vitals / demographics
        expected_vitals = [
            "age",
            "sex",
            "systolic_bp",
            "diastolic_bp",
            "heart_rate",
            "glucose",
            "body_temperature",
            "oxygen_saturation",
            "bmi",
        ]
        assert order[18:] == expected_vitals

    def test_deterministic_vector_lengths_and_keys(self):
        result = self.preprocessor.preprocess("fever, cough")
        assert isinstance(result, PreprocessedClinicalData)
        assert len(result.imputed_vector) == 27
        assert len(result.raw_vector) == 27
        assert list(result.imputed_dict.keys()) == self.preprocessor.feature_order
        assert list(result.raw_dict.keys()) == self.preprocessor.feature_order

    # -----------------------------------------------------------------------
    # 2. Flexible Symptom Inputs
    # -----------------------------------------------------------------------

    def test_flexible_symptom_inputs_equivalence(self):
        # Different input representations of same symptoms
        res_list = self.preprocessor.preprocess(["fever", "cough", "headache"])
        res_csv = self.preprocessor.preprocess("fever, cough, headache")
        res_text = self.preprocessor.preprocess("Patient suffers from fever, cough, and severe headache.")
        res_slug = self.preprocessor.preprocess(["fever", "cough", "headache"])

        assert set(res_list.canonical_symptoms) == {"fever", "cough", "headache"}
        assert set(res_csv.canonical_symptoms) == {"fever", "cough", "headache"}
        assert set(res_text.canonical_symptoms) == {"fever", "cough", "headache"}
        assert set(res_slug.canonical_symptoms) == {"fever", "cough", "headache"}

    # -----------------------------------------------------------------------
    # 3. Clinical Synonyms & Fuzzy Typo Matching
    # -----------------------------------------------------------------------

    def test_clinical_synonyms_canonicalization(self):
        res = self.preprocessor.preprocess([
            "pyrexia",             # -> fever
            "productive sputum",   # -> cough
            "lethargy",            # -> fatigue
            "cephalalgia",         # -> headache
            "dyspnoea",            # -> dyspnea
            "angina pectoris",     # -> chest_pain
            "pharyngitis",         # -> sore_throat
            "emesis",              # -> nausea
            "myalgia",             # -> body_aches
        ])
        expected = {
            "fever",
            "cough",
            "fatigue",
            "headache",
            "dyspnea",
            "chest_pain",
            "sore_throat",
            "nausea",
            "body_aches",
        }
        assert expected.issubset(set(res.canonical_symptoms))

    def test_fuzzy_matching_for_misspelled_symptoms(self):
        res = self.preprocessor.preprocess([
            "fevr",          # typo for fever
            "hedache",       # typo for headache
            "nausia",        # typo for nausea
            "dizzyness",     # typo for dizziness
            "shiverring",    # typo for chills
            "diarhea",       # typo for diarrhea
        ])
        expected = {"fever", "headache", "nausea", "dizziness", "chills", "diarrhea"}
        assert expected.issubset(set(res.canonical_symptoms))

    # -----------------------------------------------------------------------
    # 4. Bounded Negation Scope & Contrastive Conjunction Breaking
    # -----------------------------------------------------------------------

    def test_bounded_negation_basic(self):
        res = self.preprocessor.preprocess("Patient has no fever and denies cough.")
        assert "fever" in res.negated_symptoms
        assert "cough" in res.negated_symptoms
        assert "fever" not in res.canonical_symptoms
        assert "cough" not in res.canonical_symptoms
        assert res.imputed_dict["fever"] == 0.0
        assert res.imputed_dict["cough"] == 0.0

    def test_contrastive_conjunction_breaks_negation_scope(self):
        # 'but' must break negation immediately: cough is negated, fever & chest_pain are POSITIVE
        text = "Patient has no cough, but reports severe fever and chest pain."
        res = self.preprocessor.preprocess(text)

        assert "cough" in res.negated_symptoms
        assert "fever" in res.canonical_symptoms
        assert "chest_pain" in res.canonical_symptoms

        assert res.imputed_dict["cough"] == 0.0
        assert res.imputed_dict["fever"] == 1.0
        assert res.imputed_dict["chest_pain"] == 1.0

    def test_however_conjunction_breaks_negation(self):
        text = "Denies headache and dizziness; however, experiences extreme nausea and chills."
        res = self.preprocessor.preprocess(text)

        assert "headache" in res.negated_symptoms
        assert "dizziness" in res.negated_symptoms
        assert "nausea" in res.canonical_symptoms
        assert "chills" in res.canonical_symptoms

        assert res.imputed_dict["nausea"] == 1.0
        assert res.imputed_dict["chills"] == 1.0
        assert res.imputed_dict["headache"] == 0.0

    def test_negation_window_budget_expiry(self):
        # Window of 4 words: "no" at start should NOT negate symptoms 6 words later
        text = "No fever observed during early morning rounds. Patient reports severe fatigue and headache."
        res = self.preprocessor.preprocess(text)

        assert "fever" in res.negated_symptoms
        assert "fatigue" in res.canonical_symptoms
        assert "headache" in res.canonical_symptoms

    # -----------------------------------------------------------------------
    # 5. Physiological Clamping & Unit Handling
    # -----------------------------------------------------------------------

    def test_temperature_fahrenheit_conversion_and_clamping(self):
        # 102.2°F -> 39.0°C
        res = self.preprocessor.preprocess({
            "symptoms": ["fever"],
            "vitals": {"temperature": "102.2 F"},
        })
        assert math.isclose(res.imputed_dict["body_temperature"], 39.0, abs_tol=0.15)

        # Extreme high clamping: 115°F -> 46.1°C -> clamped to 45.0°C
        res_high = self.preprocessor.preprocess({
            "vitals": {"temperature": "115 F"},
        })
        assert res_high.imputed_dict["body_temperature"] == 45.0

        # Sub-physiological clamping: 25°C -> clamped to 30.0°C
        res_low = self.preprocessor.preprocess({
            "vitals": {"temperature": 25.0},
        })
        assert res_low.imputed_dict["body_temperature"] == 30.0

    def test_blood_pressure_combined_string_and_clamping(self):
        res = self.preprocessor.preprocess({
            "vitals": {"bp": "135/85 mmHg"},
        })
        assert res.imputed_dict["systolic_bp"] == 135.0
        assert res.imputed_dict["diastolic_bp"] == 85.0

        # Extreme clamping
        res_clamp = self.preprocessor.preprocess({
            "vitals": {"systolic_bp": 320, "diastolic_bp": 15},
        })
        assert res_clamp.imputed_dict["systolic_bp"] == 260.0  # max clamped
        assert res_clamp.imputed_dict["diastolic_bp"] == 30.0   # min clamped

    def test_glucose_unit_conversion_and_clamping(self):
        # mmol/L -> mg/dL: 5.5 mmol/L * 18.0182 = 99.1 mg/dL
        res = self.preprocessor.preprocess({
            "vitals": {"glucose": "5.5 mmol/L"},
        })
        assert math.isclose(res.imputed_dict["glucose"], 99.1, abs_tol=0.5)

    def test_spo2_normalization(self):
        # Fraction 0.96 -> 96%
        res = self.preprocessor.preprocess({
            "vitals": {"spo2": 0.96},
        })
        assert res.imputed_dict["oxygen_saturation"] == 96.0

    def test_bmi_computation_from_height_and_weight(self):
        # Height 180cm, Weight 81kg -> BMI = 81 / (1.80^2) = 25.0
        res = self.preprocessor.preprocess({
            "vitals": {"height_cm": 180, "weight_kg": 81},
        })
        assert math.isclose(res.imputed_dict["bmi"], 25.0, abs_tol=0.2)

    # -----------------------------------------------------------------------
    # 6. Dual Representation: Imputed vs Native NaN
    # -----------------------------------------------------------------------

    def test_dual_representation_missing_vitals(self):
        # Symptoms only -> all 9 vitals should be NaN in raw_vector, and imputed in imputed_vector
        res = self.preprocessor.preprocess(["cough", "fever"])

        assert len(res.imputed_fields) == 9
        for vital in [
            "age",
            "sex",
            "systolic_bp",
            "diastolic_bp",
            "heart_rate",
            "glucose",
            "body_temperature",
            "oxygen_saturation",
            "bmi",
        ]:
            assert math.isnan(res.raw_dict[vital])
            assert not math.isnan(res.imputed_dict[vital])

        # Verify reference physiological defaults
        assert res.imputed_dict["systolic_bp"] == 120.0
        assert res.imputed_dict["diastolic_bp"] == 80.0
        assert res.imputed_dict["heart_rate"] == 72.0
        assert res.imputed_dict["glucose"] == 95.0
        assert res.imputed_dict["body_temperature"] == 37.0
        assert res.imputed_dict["oxygen_saturation"] == 98.0
        assert res.imputed_dict["bmi"] == 24.5

        # Check raw_vector maintains float("nan") for downstream XGBoost
        nan_indices = [i for i, v in enumerate(res.raw_vector) if math.isnan(v)]
        assert len(nan_indices) == 9
        assert nan_indices == list(range(18, 27))

    # -----------------------------------------------------------------------
    # 7. Backward-Compatible Service Hook & Patient Profile Integration
    # -----------------------------------------------------------------------

    @pytest.mark.django_db
    def test_backward_compatible_hook_with_patient_model(self):
        user = User.objects.create_user(
            email="preproc.test.patient@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
        )
        PatientProfile.objects.create(
            user=user,
            date_of_birth=date(1990, 5, 15),
            gender="Female",
        )

        payload = {
            "symptoms": ["chest pain", "shortness of breath"],
            "vitals": {"bp": "130/80"},
            "patient_id": user.id,
        }

        res = preprocess_clinical_input(payload, patient=user)

        # Symptoms
        assert "chest_pain" in res.canonical_symptoms
        assert "dyspnea" in res.canonical_symptoms

        # Demographics auto-resolved from profile
        assert res.imputed_dict["sex"] == 0.0  # Female
        assert res.raw_dict["sex"] == 0.0
        assert not math.isnan(res.raw_dict["age"])
        assert res.imputed_dict["age"] >= 30.0  # Born 1990

        # BP
        assert res.imputed_dict["systolic_bp"] == 130.0
        assert res.imputed_dict["diastolic_bp"] == 80.0
