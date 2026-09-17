"""
Test suite for MediCare multi-disease model training pipeline and artifact serialization.
Verifies:
1. Model training pipeline execution, convergence, and dataset generation.
2. Serialization and integrity of xgboost_model.joblib, schema.json, and metadata.json.
3. Proper artifact loading and execution of model inference.
4. Valid probability distributions summing to 1.0.
5. Graceful handling of full clinical vitals missingness (np.nan across all 9 vitals).
6. High precision on classic condition presentations.
"""

import json
import math
import os
import joblib
import numpy as np
import pytest

from ml.train import (
    DEFAULT_ARTIFACT_DIR,
    DEFAULT_DISEASE_CLASSES,
    generate_synthetic_dev_data,
    train_model,
)
from ai.preprocessing import get_preprocessor


class TestAITrainingPipeline:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.tmp_output_dir = str(tmp_path / "artifacts_test")
        self.tmp_data_path = str(tmp_path / "dev_data.csv")
        self.preprocessor = get_preprocessor()

    def test_synthetic_dev_data_generator(self):
        df = generate_synthetic_dev_data(
            n_samples_per_class=50,
            random_state=42,
            output_path=self.tmp_data_path,
        )
        assert len(df) == 50 * len(DEFAULT_DISEASE_CLASSES)
        assert os.path.exists(self.tmp_data_path)

        # Check all 27 schema features exist
        for feat in self.preprocessor.feature_order:
            assert feat in df.columns

        # Verify missingness exists in vitals (np.nan present)
        vital_cols = self.preprocessor.feature_order[18:]
        has_nans = any(df[col].isna().any() for col in vital_cols)
        assert has_nans, "Synthetic generator must inject realistic missingness (np.nan) in vitals"

        # Verify target column
        assert set(df["target_disease"].unique()) == set(DEFAULT_DISEASE_CLASSES)

    def test_model_training_and_artifact_serialization(self):
        result = train_model(
            data_path=self.tmp_data_path,
            output_dir=self.tmp_output_dir,
            test_size=0.25,
            random_state=42,
            generate_dev=True,
            n_samples_per_class=50,
        )

        # Verify returned paths
        assert os.path.exists(result["model_path"])
        assert os.path.exists(result["schema_path"])
        assert os.path.exists(result["metadata_path"])

        # Check validation metrics
        metrics = result["metrics"]
        assert metrics["macro_f1"] > 0.85
        assert metrics["accuracy"] > 0.85
        assert metrics["log_loss"] < 0.50

        # Verify metadata.json
        with open(result["metadata_path"], "r", encoding="utf-8") as f:
            meta = json.load(f)

        assert meta["model_name"] == "MediCare-MultiDisease-XGBoost"
        assert meta["version"] == "1.0.0"
        assert meta["dataset_provenance"] == "synthetic-dev-fallback"
        assert len(meta["target_classes"]) == 8
        assert len(meta["feature_order"]) == 27
        assert "per_class_metrics" in meta["metrics"]

    def test_loaded_artifact_inference_and_probability_calibration(self):
        # Load the serialized production artifact from backend/ai/artifacts/v1.0.0/
        model_path = os.path.join(DEFAULT_ARTIFACT_DIR, "xgboost_model.joblib")
        assert os.path.exists(model_path), f"Artifact {model_path} must exist"

        artifact = joblib.load(model_path)
        assert "model" in artifact
        assert "label_encoder" in artifact
        assert "classes" in artifact
        assert "feature_order" in artifact

        model = artifact["model"]
        label_encoder = artifact["label_encoder"]
        classes = artifact["classes"]

        # 1. Test Diabetes-like profile
        prep_diabetes = self.preprocessor.preprocess({
            "symptoms": ["excessive thirst", "frequent urination", "blurred vision"],
            "vitals": {"glucose": 210.0, "age": 58, "bmi": 32.0},
        })
        x_diab = np.array([prep_diabetes.raw_vector])  # With raw NaNs for missing vitals

        probs = model.predict_proba(x_diab)[0]
        # Assert probability distribution sums strictly to 1.0
        assert math.isclose(float(np.sum(probs)), 1.0, abs_tol=1e-4)

        pred_idx = np.argmax(probs)
        pred_disease = classes[pred_idx]
        assert pred_disease == "Type 2 Diabetes"
        assert probs[pred_idx] > 0.70

    def test_model_handles_full_vitals_missingness(self):
        """Verify model handles extreme input where all 9 vitals are unmeasured (np.nan)."""
        model_path = os.path.join(DEFAULT_ARTIFACT_DIR, "xgboost_model.joblib")
        artifact = joblib.load(model_path)
        model = artifact["model"]
        classes = artifact["classes"]

        # Only symptoms, no vitals at all
        prep_flu = self.preprocessor.preprocess("Patient has high fever, severe body aches, chills, and fatigue")
        x_flu = np.array([prep_flu.raw_vector])

        # Confirm all 9 vitals are indeed np.nan in input
        assert np.isnan(x_flu[0, 18:]).all()

        # Inference must execute without exception
        probs = model.predict_proba(x_flu)[0]
        assert math.isclose(float(np.sum(probs)), 1.0, abs_tol=1e-4)

        pred_idx = np.argmax(probs)
        assert classes[pred_idx] == "Influenza"
        assert probs[pred_idx] > 0.30  # Confident top prediction significantly above 0.125 baseline prior
