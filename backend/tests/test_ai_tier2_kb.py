"""
Unit tests for Tier 2 Clinical Knowledge Base, 140+ Feature Schema, and Diagnostic Matcher.
"""
import pytest
from ai.preprocessing import (
    get_preprocessor_v2,
    ClinicalPreprocessor,
    SCHEMA_V2_PATH,
)
from ai.clinical_kb import (
    ClinicalKnowledgeMatcher,
    get_knowledge_matcher,
    DifferentialDiagnosisCandidate,
)


import unittest


class TestAITier2KnowledgeBase(unittest.TestCase):
    """Test suite for schema expansion to 140+ symptoms and Tier 2 matching engine."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.preprocessor_v2 = get_preprocessor_v2()
        cls.matcher = get_knowledge_matcher()

    @classmethod
    def setup_class(cls):
        cls.preprocessor_v2 = get_preprocessor_v2()
        cls.matcher = get_knowledge_matcher()

    def test_v2_schema_contains_over_140_symptoms_and_9_vitals(self):
        """Verifies schema.json v2.0.0 contains >= 140 clinical symptoms and 9 structured vitals."""
        schema = self.preprocessor_v2.schema
        assert schema["version"] == "2.0.0"

        feature_order = self.preprocessor_v2.feature_order
        features = self.preprocessor_v2.features_spec

        symptoms = [f for f in feature_order if features[f]["category"] == "symptom"]
        vitals = [f for f in feature_order if features[f]["category"] != "symptom"]

        # Must have at least 140 clinical symptoms (we have 154)
        assert len(symptoms) >= 140, f"Expected >= 140 symptoms, got {len(symptoms)}"
        assert len(symptoms) == 154
        assert len(vitals) == 9
        assert len(feature_order) == 163

        # Specialty hallmark checks
        # GI/Hepatic
        for sym in ["abdominal_pain", "jaundice", "dark_urine", "clay_colored_stools", "ascites", "hematemesis", "heartburn"]:
            assert sym in symptoms, f"Missing GI/Hepatic symptom: {sym}"

        # Cardio/Resp
        for sym in ["chest_pain", "dyspnea", "palpitations", "leg_swelling", "orthopnea", "hemoptysis", "wheezing"]:
            assert sym in symptoms, f"Missing Cardio/Resp symptom: {sym}"

        # Neuro
        for sym in ["tremor", "numbness", "tingling", "seizures", "confusion", "ataxia", "photophobia", "stiff_neck", "facial_droop"]:
            assert sym in symptoms, f"Missing Neuro symptom: {sym}"

        # Renal/Uro
        for sym in ["flank_pain", "hematuria", "dysuria", "oliguria", "urinary_urgency"]:
            assert sym in symptoms, f"Missing Renal/Uro symptom: {sym}"

        # Derm/Immune
        for sym in ["skin_rash", "itching", "butterfly_rash", "hives", "joint_swelling", "hair_loss", "purpura"]:
            assert sym in symptoms, f"Missing Derm/Immune symptom: {sym}"

        # General/Infectious
        for sym in ["fever", "chills", "rigors", "night_sweats", "lymphadenopathy", "malaise", "weight_loss"]:
            assert sym in symptoms, f"Missing General/Infectious symptom: {sym}"

        # Vitals and baseline normals preserved
        expected_vitals = [
            "age", "sex", "systolic_bp", "diastolic_bp", "heart_rate",
            "glucose", "body_temperature", "oxygen_saturation", "bmi"
        ]
        for v in expected_vitals:
            assert v in vitals
            assert "default_imputation" in features[v]

    def test_dynamic_preprocessor_extracts_new_clinical_symptoms(self):
        """Verifies preprocessor correctly canonicalizes new specialty symptoms."""
        # Yellow skin and dark urine -> jaundice, dark_urine
        res1 = self.preprocessor_v2.preprocess("Patient has marked yellow skin and dark urine for two days.")
        assert "jaundice" in res1.canonical_symptoms
        assert "dark_urine" in res1.canonical_symptoms

        # Flank pain and hematuria
        res2 = self.preprocessor_v2.preprocess(["severe flank pain", "blood when peeing"])
        assert "flank_pain" in res2.canonical_symptoms
        assert "hematuria" in res2.canonical_symptoms

        # Lupus hallmarks
        res3 = self.preprocessor_v2.preprocess("Presents with butterfly rash across nose and painful swollen joints")
        assert "butterfly_rash" in res3.canonical_symptoms
        assert "joint_swelling" in res3.canonical_symptoms

        # Negation boundary resolution on new symptoms
        res4 = self.preprocessor_v2.preprocess("Patient has severe flank pain but denies hematuria and has no fever")
        assert "flank_pain" in res4.canonical_symptoms
        assert "hematuria" in res4.negated_symptoms
        assert "fever" in res4.negated_symptoms

    def test_tier2_knowledge_catalog_contains_over_500_conditions(self):
        """Verifies Tier 2 clinical knowledge catalog contains >= 500 conditions."""
        assert self.matcher.condition_count >= 500, f"Expected >= 500 conditions, got {self.matcher.condition_count}"
        
        # Verify structure of loaded conditions
        sample = self.matcher.conditions[0]
        assert "id" in sample
        assert "name" in sample
        assert "category" in sample
        assert "icd10" in sample
        assert "pathognomonic_symptoms" in sample
        assert "secondary_symptoms" in sample
        assert "urgency" in sample
        assert "description" in sample

    def test_tier2_matcher_identifies_nephrolithiasis(self):
        """Verifies Tier 2 matcher accurately identifies Nephrolithiasis from flank_pain and hematuria."""
        diffs = self.matcher.match(
            symptoms=["flank_pain", "hematuria"],
            top_k=5,
        )
        assert len(diffs) > 0
        top = diffs[0]

        assert top.condition_id == "nephrolithiasis"
        assert "Nephrolithiasis" in top.name
        assert top.icd10 == "N20.0"
        assert top.category == "Nephrology/Urology"
        assert "flank_pain" in top.matched_hallmarks
        assert "hematuria" in top.matched_hallmarks
        assert len(top.missing_hallmarks) == 0  # Both hallmarks matched
        assert top.score >= 0.85
        assert top.confidence_pct >= 85.0

    def test_tier2_matcher_identifies_systemic_lupus_with_attribution(self):
        """Verifies Tier 2 matcher accurately identifies Systemic Lupus with hallmark attribution."""
        diffs = self.matcher.match(
            symptoms=["butterfly_rash", "joint_swelling"],
            top_k=5,
        )
        assert len(diffs) > 0
        top = diffs[0]

        assert top.condition_id == "systemic_lupus_erythematosus"
        assert "Systemic Lupus" in top.name
        assert top.icd10 == "M32.9"
        assert top.category == "Rheumatology/Immunology"
        assert "butterfly_rash" in top.matched_hallmarks
        assert "joint_swelling" in top.matched_hallmarks
        assert "photosensitivity" in top.missing_hallmarks
        assert top.score >= 0.60
        assert top.confidence_pct >= 60.0

    def test_tfidf_weighting_favors_rare_symptoms_over_generic(self):
        """Verifies rare pathognomonic symptoms have higher IDF weight than generic constitutional symptoms."""
        # Generic common symptoms
        idf_fatigue = self.matcher.idf_weights.get("fatigue", 1.0)
        idf_headache = self.matcher.idf_weights.get("headache", 1.0)

        # Specific hallmarks
        idf_jaundice = self.matcher.idf_weights.get("jaundice", 1.0)
        idf_butterfly_rash = self.matcher.idf_weights.get("butterfly_rash", 1.0)
        idf_flank_pain = self.matcher.idf_weights.get("flank_pain", 1.0)
        idf_hematuria = self.matcher.idf_weights.get("hematuria", 1.0)

        assert idf_butterfly_rash > idf_fatigue
        assert idf_jaundice > idf_fatigue
        assert idf_flank_pain > idf_headache
        assert idf_hematuria > idf_headache

    def test_direct_attribution_output_schema(self):
        """Verifies differential candidates adhere to the clinical attribution schema."""
        diffs = self.matcher.match(["jaundice", "dark_urine", "ascites"], top_k=3)
        assert len(diffs) > 0

        for candidate in diffs:
            d = candidate.to_dict()
            assert isinstance(d["condition_id"], str)
            assert isinstance(d["name"], str)
            assert isinstance(d["category"], str)
            assert isinstance(d["icd10"], str)
            assert isinstance(d["urgency"], str)
            assert 0.0 <= d["score"] <= 1.0
            assert 0.0 <= d["confidence_pct"] <= 100.0
            assert isinstance(d["matched_features"], list)
            assert isinstance(d["matched_hallmarks"], list)
            assert isinstance(d["missing_hallmarks"], list)
            assert len(d["description"]) > 0
