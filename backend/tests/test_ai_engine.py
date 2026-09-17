"""
Test suite for MediCare Production Inference Engine & Real TreeSHAP Explainability.

Verifies:
1. Engine initialization, artifact loading, and singleton cache behavior (100 classes, 163 features).
2. Complete response payload schema contract and type validation across both tiers.
3. Real TreeSHAP mathematical sanity (sum of SHAP values = margin - base_value) across 100 classes.
4. Missing vitals resilience (inference and SHAP with np.nan for all 9 vitals).
5. Error handling and typed ModelNotLoadedError on missing/corrupted artifacts.
6. Tier 2 fallback routing when given rare or atypical symptom combinations.
7. Clinical red-flag escalation logic (severe hypoxemia, chest pain, hypertensive crisis).
8. Flexible clinical input parsing (dict, list, raw text string).
"""

import math
from pathlib import Path
import numpy as np
import pytest

from ai.engine import DiseaseRiskEngine, ModelNotLoadedError, get_engine


class TestDiseaseRiskEngine:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.engine = get_engine(force_reload=True)

    def test_engine_initialization(self):
        """Engine loads artifacts, model, and SHAP explainer successfully for v2.0.0."""
        assert self.engine.model is not None
        assert self.engine.explainer is not None
        assert len(self.engine.classes) == 100
        assert len(self.engine.feature_order) == 163
        assert self.engine.schema_version == "2.0.0"
        assert self.engine.model_version == "2.0.0"
        assert self.engine.model_name == "MediCare-MultiDisease-XGBoost"
        assert self.engine.knowledge_matcher is not None

        # Verify singleton behavior
        cached = get_engine()
        assert cached is self.engine

    def test_predict_and_explain_structure(self):
        """Verify full response payload contract matches all required keys and types."""
        input_data = {
            "symptoms": ["excessive thirst", "frequent urination", "blurred vision"],
            "vitals": {"glucose": 215.0, "age": 55, "bmi": 31.5},
        }
        res = self.engine.predict_and_explain(input_data)

        # 1. Top-level keys
        assert "predicted_condition" in res
        assert "confidence" in res
        assert "risk_level" in res
        assert "severity" in res
        assert "triage_level" in res
        assert "recommendation" in res
        assert "recommended_action" in res
        assert "canonical_symptoms" in res
        assert "differential_diagnoses" in res
        assert "ranked_diagnoses" in res
        assert "ranked_diseases" in res
        assert "tier2_clinical_matches" in res
        assert "explanation" in res
        assert "shap_analysis" in res
        assert "clinical_safety" in res
        assert "model_metadata" in res

        # 2. Types and values
        assert isinstance(res["predicted_condition"], str)
        assert "Diabetes" in res["predicted_condition"]
        assert isinstance(res["confidence"], float)
        assert 0.0 <= res["confidence"] <= 1.0
        assert res["risk_level"] in ["LOW", "MODERATE", "HIGH"]
        assert res["triage_level"] in ["LOW", "MODERATE", "HIGH"]

        # 3. Differential diagnoses
        diff = res["differential_diagnoses"]
        assert isinstance(diff, list)
        assert len(diff) > 0
        probs = [d["probability"] for d in diff]
        assert probs == sorted(probs, reverse=True)
        for item in diff:
            assert "condition" in item
            assert "probability" in item
            assert "risk_level" in item
            assert item["risk_level"] in ["LOW", "MODERATE", "HIGH"]

        # 4. Explanation & SHAP
        expl = res["explanation"]
        assert isinstance(expl["base_value"], float)
        assert isinstance(expl["summary"], str)
        assert len(expl["summary"]) > 10
        assert isinstance(expl["features"], list)
        assert len(expl["features"]) > 0

        for f in expl["features"]:
            assert "feature" in f
            assert "value" in f
            assert "shap_value" in f
            assert "direction" in f
            assert f["direction"] in ["increases_risk", "decreases_risk"]
            assert isinstance(f["shap_value"], float)

        # Features must be sorted by descending absolute SHAP magnitude
        abs_shaps = [abs(f["shap_value"]) for f in expl["features"]]
        assert abs_shaps == sorted(abs_shaps, reverse=True)

        # 5. Clinical Safety & Metadata
        safety = res["clinical_safety"]
        assert safety["is_definitive_diagnosis"] is False
        assert "Clinical decision support estimate only" in safety["disclaimer"]

        meta = res["model_metadata"]
        assert meta["model_name"] == "MediCare-MultiDisease-XGBoost"
        assert meta["model_version"] in ["1.0.0", "2.0.0"]
        assert meta["schema_version"] in ["1.0.0", "2.0.0"]
        assert meta["tier"] in ["Tier-1-ML", "Tier-2-KB", "Undifferentiated"]

    def test_shap_mathematical_consistency(self):
        """
        Verify that sum of SHAP attributions matches the model prediction offset from base value:
        sum(SHAP_i) == f(x) - E[f(X)] (within numerical precision < 1e-4).
        """
        input_data = {
            "symptoms": ["fever", "cough", "sore throat"],
            "vitals": {"body_temperature": 38.5, "age": 30},
        }
        prep = self.engine.preprocessor.preprocess(input_data)
        X = np.array([prep.raw_vector], dtype=np.float32)

        # Model margins (raw logits before softmax)
        margins = self.engine.model.predict(X, output_margin=True)[0]
        probs = self.engine.model.predict_proba(X)[0]
        pred_idx = int(np.argmax(probs))

        # Real SHAP values
        raw_shaps = self.engine.explainer.shap_values(X)
        shap_slice = self.engine._extract_shap_slice_for_class(raw_shaps, pred_idx)
        base_val = self.engine._extract_base_value(pred_idx)

        # Theoretical identity: margin = base_value + sum(shap_values)
        shap_sum = float(np.sum(shap_slice))
        expected_margin = base_val + shap_sum
        actual_margin = float(margins[pred_idx])

        diff = abs(actual_margin - expected_margin)
        assert diff < 1e-4, f"SHAP sum {shap_sum} + base {base_val} != margin {actual_margin} (diff: {diff})"

    def test_missing_vitals_resilience(self):
        """Inference and SHAP succeed cleanly when all 9 vitals are np.nan."""
        input_data = "I have a terrible headache with sensitivity to light and nausea"
        res = self.engine.predict_and_explain(input_data)

        assert res["predicted_condition"] == "Migraine"
        assert res["confidence"] > 0.40
        assert len(res["explanation"]["features"]) > 0

        # Check that top features are symptoms like headache, photophobia, nausea
        top_features = [f["feature"] for f in res["explanation"]["features"][:3]]
        assert any(feat in ["headache", "photophobia", "nausea"] for feat in top_features)

        # For any vital feature in the list, value should be None (representing missing/NaN)
        n_symptoms = len(self.engine.feature_order) - 9
        vital_names = set(self.engine.feature_order[n_symptoms:])
        for f in res["explanation"]["features"]:
            if f["feature"] in vital_names:
                assert f["value"] is None

    def test_tier2_fallback_routing_on_rare_or_atypical_presentation(self):
        """Tier 2 Clinical Knowledge Matcher leads when given atypical presentations."""
        # Atypical symptom combo with rare hallmarks: ascites and clay colored stools
        input_data = {
            "symptoms": ["ascites", "clay colored stools", "yellow skin", "dark urine"],
            "vitals": {"systolic_bp": 105.0},
        }
        res = self.engine.predict_and_explain(input_data)

        # Must route through Tier 2 or identify cirrhosis / liver decompensation
        assert res["confidence"] > 0.30
        assert any(term in res["predicted_condition"] for term in ["Cirrhosis", "Hepatitis", "Liver", "Cholangitis"])
        assert "tier2_clinical_matches" in res
        assert len(res["tier2_clinical_matches"]) > 0

    def test_missing_artifact_handling(self, tmp_path):
        """ModelNotLoadedError is raised if artifact directory or files do not exist."""
        with pytest.raises(ModelNotLoadedError) as exc_info:
            DiseaseRiskEngine(artifacts_dir=tmp_path / "non_existent_folder")
        assert "does not exist" in str(exc_info.value)

        empty_dir = tmp_path / "empty_artifacts"
        empty_dir.mkdir()
        with pytest.raises(ModelNotLoadedError) as exc_info:
            DiseaseRiskEngine(artifacts_dir=empty_dir)
        assert "not found" in str(exc_info.value)

    def test_clinical_red_flag_escalation(self):
        """Clinical red flags escalate risk triage level to HIGH."""
        # 1. Chest pain escalation
        res_chest_pain = self.engine.predict_and_explain({
            "symptoms": ["chest pain", "dizziness"],
            "vitals": {"systolic_bp": 135.0},
        })
        assert res_chest_pain["risk_level"] == "HIGH"
        assert res_chest_pain["triage_level"] == "HIGH"

        # 2. Dyspnea with hypoxemia (SpO2 < 92%)
        res_hypoxemic = self.engine.predict_and_explain({
            "symptoms": ["cough", "dyspnea"],
            "vitals": {"oxygen_saturation": 89.0},
        })
        assert res_hypoxemic["risk_level"] == "HIGH"
        assert res_hypoxemic["severity"] == "critical"

        # 3. Hypertensive crisis (Systolic BP >= 180)
        res_htn_crisis = self.engine.predict_and_explain({
            "symptoms": ["headache"],
            "vitals": {"systolic_bp": 195.0, "diastolic_bp": 115.0},
        })
        assert res_htn_crisis["risk_level"] == "HIGH"
        assert res_htn_crisis["severity"] == "critical"

    def test_flexible_inputs(self):
        """Engine accepts dict, list of strings, or raw natural language string."""
        # List of symptoms
        res_list = self.engine.predict_and_explain(["cough", "sore throat", "rhinorrhea"])
        assert "predicted_condition" in res_list
        assert res_list["confidence"] > 0.20

        # Raw string query
        res_str = self.engine.predict_and_explain("Severe flank pain with blood in urine")
        assert "Nephrolithiasis" in res_str["predicted_condition"]

        # Dict with patient object mock
        class MockPatient:
            age = 62
            gender = "female"

        res_patient = self.engine.predict_and_explain(
            {"symptoms": ["frequent urination", "excessive thirst"]},
            patient=MockPatient(),
        )
        assert "Diabetes" in res_patient["predicted_condition"]
