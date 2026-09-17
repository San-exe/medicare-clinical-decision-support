"""
MediCare Production Inference Engine & Real TreeSHAP Explainability.

Provides cached model artifact loading, multi-class XGBoost disease risk prediction,
and sample-level TreeSHAP feature attributions adhering to clinical safety standards.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import joblib
import numpy as np
import shap

from .preprocessing import ClinicalPreprocessor, PreprocessedClinicalData, get_preprocessor

logger = logging.getLogger(__name__)


class ModelNotLoadedError(RuntimeError):
    """Raised when AI model artifacts cannot be loaded, are missing, or are corrupted."""
    pass


class DiseaseRiskEngine:
    """
    Production-grade inference and TreeSHAP explainability engine for multi-disease risk triage.
    """

    _instance: Optional["DiseaseRiskEngine"] = None

    def __init__(self, artifacts_dir: Optional[Union[str, Path]] = None) -> None:
        """
        Initialize engine from serialized artifacts.
        """
        if artifacts_dir is None:
            self.artifacts_dir = Path(__file__).resolve().parent / "artifacts" / "v1.0.0"
        else:
            self.artifacts_dir = Path(artifacts_dir)

        self._load_artifacts()

    def _load_artifacts(self) -> None:
        """Loads serialized XGBoost model, label encoder, schema, metadata, and SHAP explainer."""
        if not self.artifacts_dir.exists() or not self.artifacts_dir.is_dir():
            raise ModelNotLoadedError(
                f"Model artifact directory does not exist: {self.artifacts_dir}"
            )

        model_path = self.artifacts_dir / "xgboost_model.joblib"
        schema_path = self.artifacts_dir / "schema.json"
        metadata_path = self.artifacts_dir / "metadata.json"

        if not model_path.exists():
            raise ModelNotLoadedError(f"Model artifact not found at: {model_path}")
        if not schema_path.exists():
            raise ModelNotLoadedError(f"Schema artifact not found at: {schema_path}")
        if not metadata_path.exists():
            raise ModelNotLoadedError(f"Metadata artifact not found at: {metadata_path}")

        try:
            artifact_data = joblib.load(model_path)
            if not isinstance(artifact_data, dict) or "model" not in artifact_data:
                raise ModelNotLoadedError("Invalid model artifact dictionary structure.")

            self.model = artifact_data["model"]
            self.label_encoder = artifact_data["label_encoder"]
            self.classes = list(artifact_data["classes"])
            self.feature_order = list(artifact_data["feature_order"])
            self.schema_version = artifact_data.get("schema_version", "1.0.0")

            with open(schema_path, "r", encoding="utf-8") as f:
                self.schema = json.load(f)

            with open(metadata_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

            self.model_name = self.metadata.get("model_name", "MediCare-MultiDisease-XGBoost")
            self.model_version = self.metadata.get("version", "1.0.0")

            # Initialize preprocessor using loaded schema
            self.preprocessor = ClinicalPreprocessor(schema=self.schema)

            # Initialize and cache TreeExplainer
            self.explainer = shap.TreeExplainer(self.model)
            logger.info("DiseaseRiskEngine successfully initialized with TreeExplainer.")
        except Exception as e:
            if isinstance(e, ModelNotLoadedError):
                raise
            raise ModelNotLoadedError(
                f"Failed to initialize DiseaseRiskEngine from {self.artifacts_dir}: {str(e)}"
            ) from e

    def _extract_shap_slice_for_class(
        self,
        shap_values: Union[List[np.ndarray], np.ndarray],
        class_idx: int,
    ) -> np.ndarray:
        """
        Robustly extracts the 1D SHAP attribution slice for the predicted target class across
        different shap/xgboost multi-class return shapes.
        """
        if isinstance(shap_values, list):
            # List of [1, n_features] arrays per class
            return np.asarray(shap_values[class_idx][0], dtype=np.float32)

        if isinstance(shap_values, np.ndarray):
            if shap_values.ndim == 3:
                # Shape (1, n_features, n_classes) or (1, n_classes, n_features)
                n_features = len(self.feature_order)
                if shap_values.shape[1] == n_features:
                    return np.asarray(shap_values[0, :, class_idx], dtype=np.float32)
                elif shap_values.shape[2] == n_features:
                    return np.asarray(shap_values[0, class_idx, :], dtype=np.float32)
                else:
                    raise ValueError(f"Incompatible 3D SHAP shape: {shap_values.shape}")
            elif shap_values.ndim == 2:
                return np.asarray(shap_values[0], dtype=np.float32)

        raise ValueError(f"Unsupported SHAP values type/shape: {type(shap_values)}")

    def _extract_base_value(self, class_idx: int) -> float:
        """Extracts the model's base expected margin value for the given class."""
        ev = self.explainer.expected_value
        if isinstance(ev, (list, np.ndarray)):
            return float(ev[class_idx])
        return float(ev)

    def _generate_explanation_summary(
        self,
        predicted_condition: str,
        feature_attributions: List[Dict[str, Any]],
    ) -> str:
        """
        Generates a concise, clinical, plain-English summary of top factors driving risk.
        """
        top_increasing = [f for f in feature_attributions if f["direction"] == "increases_risk"][:3]
        top_decreasing = [f for f in feature_attributions if f["direction"] == "decreases_risk"][:2]

        summary_parts = []
        if top_increasing:
            inc_items = []
            for item in top_increasing:
                feat = item["feature"].replace("_", " ")
                val = item["value"]
                if val is not None and val != 1:
                    inc_items.append(f"{feat} ({val})")
                else:
                    inc_items.append(feat)
            summary_parts.append(
                f"Primary factors elevating risk for {predicted_condition} include {', '.join(inc_items)}."
            )

        if top_decreasing:
            dec_items = []
            for item in top_decreasing:
                feat = item["feature"].replace("_", " ")
                val = item["value"]
                if val is not None and val != 0:
                    dec_items.append(f"{feat} ({val})")
                else:
                    dec_items.append(f"absence of {feat}")
            summary_parts.append(
                f"Conversely, {', '.join(dec_items)} moderated overall suspicion."
            )

        if not summary_parts:
            return f"Feature baseline consistent with general population; model identified {predicted_condition} as most consistent match."

        return " ".join(summary_parts)

    def predict_and_explain(
        self,
        input_data: Union[Dict[str, Any], List[str], str],
        patient: Optional[Any] = None,
        top_n: int = 5,
    ) -> Dict[str, Any]:
        """
        Execute deterministic prediction and TreeSHAP explainability pipeline.

        Args:
            input_data: Flexible clinical input (dict, list of symptoms, or raw text query).
            patient: Optional baseline patient profile model instance or dict.
            top_n: Number of differential diagnoses to include in output.

        Returns:
            Standardized CDS response payload matching clinical safety specifications.
        """
        # 1. Dynamic Preprocessing (preserving native np.nan for vitals)
        preprocessed: PreprocessedClinicalData = self.preprocessor.preprocess(
            input_data=input_data,
            patient=patient,
        )
        raw_vector = preprocessed.raw_vector
        X = np.array([raw_vector], dtype=np.float32)

        # 2. Deterministic Multi-Class Prediction
        probs = self.model.predict_proba(X)[0]
        pred_class_idx = int(np.argmax(probs))
        predicted_condition = str(self.classes[pred_class_idx])
        confidence = round(float(probs[pred_class_idx]), 4)

        # Differential Diagnoses
        sorted_indices = np.argsort(probs)[::-1]
        differential_diagnoses = []
        for idx in sorted_indices[:top_n]:
            p = round(float(probs[idx]), 4)
            if p < 0.30:
                risk_cat = "LOW"
            elif p <= 0.70:
                risk_cat = "MODERATE"
            else:
                risk_cat = "HIGH"
            differential_diagnoses.append({
                "condition": str(self.classes[idx]),
                "probability": p,
                "risk_level": risk_cat,
            })

        # Base Risk Level Assessment
        if confidence < 0.30:
            assigned_risk = "LOW"
        elif confidence <= 0.70:
            assigned_risk = "MODERATE"
        else:
            assigned_risk = "HIGH"

        # 3. Clinical Red-Flag Escalation Triage
        canonical_symptoms = set(preprocessed.canonical_symptoms)
        vitals = preprocessed.vitals_raw

        has_chest_pain = "chest_pain" in canonical_symptoms or preprocessed.raw_dict.get("chest_pain", 0.0) == 1.0
        has_dyspnea = "dyspnea" in canonical_symptoms or preprocessed.raw_dict.get("dyspnea", 0.0) == 1.0
        spo2 = vitals.get("oxygen_saturation")
        systolic_bp = vitals.get("systolic_bp")

        is_hypoxemic = spo2 is not None and spo2 < 92.0
        is_severe_hypoxemic = spo2 is not None and spo2 < 90.0
        is_hypertensive_crisis = systolic_bp is not None and systolic_bp >= 180.0

        escalate_red_flag = (
            has_chest_pain
            or (has_dyspnea and is_hypoxemic)
            or is_severe_hypoxemic
            or is_hypertensive_crisis
        )

        if escalate_red_flag and assigned_risk != "HIGH":
            assigned_risk = "HIGH"

        # 4. Real TreeSHAP Explainability Calculation
        raw_shap_values = self.explainer.shap_values(X)
        class_shap_slice = self._extract_shap_slice_for_class(raw_shap_values, pred_class_idx)
        base_value = self._extract_base_value(pred_class_idx)

        # Feature Attributions (|s_i| > 1e-4)
        feature_attributions: List[Dict[str, Any]] = []
        for i, feat_name in enumerate(self.feature_order):
            s_val = float(class_shap_slice[i])
            if abs(s_val) > 1e-4:
                raw_val = raw_vector[i]
                if np.isnan(raw_val):
                    val_json: Any = None
                elif i < 18:
                    val_json = int(raw_val)
                else:
                    val_json = round(float(raw_val), 2)

                feature_attributions.append({
                    "feature": feat_name,
                    "value": val_json,
                    "shap_value": round(s_val, 4),
                    "direction": "increases_risk" if s_val > 0 else "decreases_risk",
                })

        # Sort features by descending absolute SHAP magnitude
        feature_attributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

        summary_text = self._generate_explanation_summary(
            predicted_condition, feature_attributions
        )

        # 5. Clinical Safety & Response Payload Contract
        return {
            "predicted_condition": predicted_condition,
            "confidence": confidence,
            "risk_level": assigned_risk,
            "differential_diagnoses": differential_diagnoses,
            "explanation": {
                "base_value": round(base_value, 4),
                "features": feature_attributions,
                "summary": summary_text,
            },
            "clinical_safety": {
                "is_definitive_diagnosis": False,
                "disclaimer": (
                    "Clinical decision support estimate only by automated clinical decision support system. "
                    "Not a definitive medical diagnosis. Requires clinical clinician evaluation."
                ),
            },
            "model_metadata": {
                "model_name": self.model_name,
                "model_version": self.model_version,
                "schema_version": self.schema_version,
            },
        }


def get_engine(
    artifacts_dir: Optional[Union[str, Path]] = None,
    force_reload: bool = False,
) -> DiseaseRiskEngine:
    """
    Retrieve or create the singleton instance of DiseaseRiskEngine.
    """
    if DiseaseRiskEngine._instance is None or force_reload:
        DiseaseRiskEngine._instance = DiseaseRiskEngine(artifacts_dir=artifacts_dir)
    return DiseaseRiskEngine._instance
