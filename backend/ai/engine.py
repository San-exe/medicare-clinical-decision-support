"""
MediCare Production Inference Engine & Real TreeSHAP Explainability.

Unites:
- Tier 1: 100-disease multi-class XGBoost classifier with sample-level TreeSHAP feature attributions.
- Tier 2: 530-disease Clinical Knowledge Matcher with TF-IDF weighted Cosine/Jaccard retrieval.
- Intelligent Hybrid Routing with clinical red-flag triage escalation and 100% backward compatibility.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import joblib
import numpy as np
import shap

from .preprocessing import ClinicalPreprocessor, PreprocessedClinicalData, get_preprocessor_v2
from .clinical_kb import ClinicalKnowledgeMatcher, get_knowledge_matcher, DifferentialDiagnosisCandidate

logger = logging.getLogger(__name__)


class ModelNotLoadedError(RuntimeError):
    """Raised when AI model artifacts cannot be loaded, are missing, or are corrupted."""
    pass


class DiseaseRiskEngine:
    """
    Production dual-tier prediction and explainability engine for clinical decision support.
    """

    _instance: Optional["DiseaseRiskEngine"] = None

    def __init__(self, artifacts_dir: Optional[Union[str, Path]] = None) -> None:
        """
        Initialize engine from serialized artifacts.
        Defaults to v2.0.0 (100 diseases, 163 features), with fallback to v1.0.0 if v2.0.0 is missing.
        """
        base_dir = Path(__file__).resolve().parent / "artifacts"
        if artifacts_dir is None:
            v2_dir = base_dir / "v2.0.0"
            v1_dir = base_dir / "v1.0.0"
            if v2_dir.exists() and (v2_dir / "xgboost_model.joblib").exists():
                self.artifacts_dir = v2_dir
            elif v1_dir.exists() and (v1_dir / "xgboost_model.joblib").exists():
                self.artifacts_dir = v1_dir
            else:
                self.artifacts_dir = v2_dir
        else:
            self.artifacts_dir = Path(artifacts_dir)

        self._load_artifacts()
        self._init_knowledge_matcher()

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
            self.schema_version = str(artifact_data.get("schema_version", "2.0.0"))

            with open(schema_path, "r", encoding="utf-8") as f:
                self.schema = json.load(f)

            with open(metadata_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

            self.model_name = self.metadata.get("model_name", "MediCare-MultiDisease-XGBoost")
            self.model_version = str(self.metadata.get("version", self.schema_version))

            # Initialize preprocessor using loaded schema
            self.preprocessor = ClinicalPreprocessor(schema=self.schema)

            # Initialize and cache TreeExplainer
            self.explainer = shap.TreeExplainer(self.model)
            logger.info(
                f"DiseaseRiskEngine initialized with {len(self.classes)} classes and "
                f"{len(self.feature_order)} features (version {self.model_version})."
            )
        except Exception as e:
            if isinstance(e, ModelNotLoadedError):
                raise
            raise ModelNotLoadedError(
                f"Failed to initialize DiseaseRiskEngine from {self.artifacts_dir}: {str(e)}"
            ) from e

    def _init_knowledge_matcher(self) -> None:
        """Initializes Tier 2 Clinical Knowledge Matcher."""
        try:
            self.knowledge_matcher = get_knowledge_matcher()
        except Exception as exc:
            logger.warning(f"Could not load Tier 2 Knowledge Matcher: {exc}")
            self.knowledge_matcher = None

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
        tier: str = "Tier-1-ML",
        tier2_attribution: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generates a concise, clinical, plain-English summary of top factors driving risk.
        """
        if tier == "Tier-2-KB" and tier2_attribution:
            hallmarks = tier2_attribution.get("matched_hallmarks", [])
            features = tier2_attribution.get("matched_features", [])
            key_pts = hallmarks or features
            if key_pts:
                pts_str = ", ".join(f.replace("_", " ") for f in key_pts[:4])
                return (
                    f"Tier 2 Clinical Knowledge Base identified {predicted_condition} as the leading diagnostic match "
                    f"based on hallmark presentation: {pts_str}."
                )

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
        Executes dual-tier prediction and TreeSHAP explainability pipeline.

        Evaluates:
        - Tier 1: 100-disease multi-class XGBoost classifier.
        - Tier 2: 530-disease open-world clinical knowledge matcher.
        - Intelligent Hybrid Routing: Tier 1 leads when confidence >= 0.40; escalates to Tier 2 for atypical/rare presentations.
        - Red-flag triage escalation for hypoxemia, chest pain, and hypertensive crisis.
        """
        # 1. Dynamic Preprocessing (preserving native np.nan for unmeasured vitals)
        preprocessed: PreprocessedClinicalData = self.preprocessor.preprocess(
            input_data=input_data,
            patient=patient,
        )
        raw_vector = preprocessed.raw_vector
        X = np.array([raw_vector], dtype=np.float32)
        canonical_symptoms = list(preprocessed.canonical_symptoms)
        vitals_raw = preprocessed.vitals_raw

        # 2. Evaluate Tier 1 (XGBoost ML)
        probs = self.model.predict_proba(X)[0]
        t1_pred_idx = int(np.argmax(probs))
        t1_condition = str(self.classes[t1_pred_idx])
        t1_confidence = round(float(probs[t1_pred_idx]), 4)

        # 3. Evaluate Tier 2 (Clinical Knowledge Matcher across 530+ conditions)
        tier2_candidates: List[DifferentialDiagnosisCandidate] = []
        if self.knowledge_matcher and canonical_symptoms:
            tier2_candidates = self.knowledge_matcher.match(
                symptoms=canonical_symptoms,
                vitals=vitals_raw,
                top_k=top_n,
            )
        top_t2 = tier2_candidates[0] if tier2_candidates else None

        # 4. Intelligent Hybrid Routing
        # Tier 1 threshold = 0.40 (40x baseline random prior in 100 classes)
        if t1_confidence >= 0.40:
            active_tier = "Tier-1-ML"
            predicted_condition = t1_condition
            confidence = t1_confidence
            explanation_class_idx = t1_pred_idx
            tier2_attr = None
        else:
            # Low Tier 1 confidence: Atypical, rare, or open-world presentation
            if top_t2 and top_t2.score >= 0.25:
                active_tier = "Tier-2-KB"
                predicted_condition = top_t2.name
                confidence = round(top_t2.score, 4)
                explanation_class_idx = t1_pred_idx
                tier2_attr = top_t2.to_dict()
            else:
                # Both tiers have low confidence
                active_tier = "Undifferentiated"
                predicted_condition = t1_condition if t1_confidence > 0.15 else "Undifferentiated / Atypical Presentation"
                confidence = t1_confidence
                explanation_class_idx = t1_pred_idx
                tier2_attr = None

        # 5. Differential Diagnoses Ranking
        sorted_indices = np.argsort(probs)[::-1]
        t1_differentials = []
        for idx in sorted_indices[:top_n]:
            p = round(float(probs[idx]), 4)
            r_cat = "HIGH" if p > 0.70 else ("MODERATE" if p >= 0.30 else "LOW")
            t1_differentials.append({
                "condition": str(self.classes[idx]),
                "probability": p,
                "risk_level": r_cat,
                "tier": "Tier-1-ML",
            })

        tier2_matches_payload = [c.to_dict() for c in tier2_candidates]

        if active_tier == "Tier-2-KB" and tier2_candidates:
            # When Tier 2 leads, prioritize knowledge base differentials
            primary_differentials = []
            for c in tier2_candidates[:top_n]:
                r_cat = "HIGH" if c.score > 0.70 else ("MODERATE" if c.score >= 0.30 else "LOW")
                primary_differentials.append({
                    "condition": c.name,
                    "probability": c.score,
                    "risk_level": r_cat,
                    "tier": "Tier-2-KB",
                    "icd10": c.icd10,
                    "category": c.category,
                    "matched_hallmarks": c.matched_hallmarks,
                })
        else:
            primary_differentials = t1_differentials

        # Base Risk Level Assessment
        if confidence < 0.30:
            assigned_risk = "LOW"
            severity = "low"
        elif confidence <= 0.70:
            assigned_risk = "MODERATE"
            severity = "moderate"
        else:
            assigned_risk = "HIGH"
            severity = "high"

        # 6. Clinical Red-Flag Escalation Triage (Applies universally across both tiers)
        canonical_sym_set = set(canonical_symptoms)
        has_chest_pain = "chest_pain" in canonical_sym_set or preprocessed.raw_dict.get("chest_pain", 0.0) == 1.0
        has_dyspnea = "dyspnea" in canonical_sym_set or preprocessed.raw_dict.get("dyspnea", 0.0) == 1.0
        spo2 = vitals_raw.get("oxygen_saturation")
        systolic_bp = vitals_raw.get("systolic_bp")

        is_hypoxemic = spo2 is not None and spo2 < 92.0
        is_severe_hypoxemic = spo2 is not None and spo2 < 90.0
        is_hypertensive_crisis = systolic_bp is not None and systolic_bp >= 180.0

        escalate_red_flag = (
            has_chest_pain
            or (has_dyspnea and is_hypoxemic)
            or is_severe_hypoxemic
            or is_hypertensive_crisis
        )

        if escalate_red_flag:
            assigned_risk = "HIGH"
            if is_severe_hypoxemic or is_hypertensive_crisis or (has_chest_pain and (has_dyspnea or is_hypoxemic)):
                severity = "critical"
            else:
                severity = "high"

        # 7. Real TreeSHAP Explainability Calculation
        raw_shap_values = self.explainer.shap_values(X)
        class_shap_slice = self._extract_shap_slice_for_class(raw_shap_values, explanation_class_idx)
        base_value = self._extract_base_value(explanation_class_idx)

        # Feature Attributions (|s_i| > 1e-4)
        n_symptoms = len(self.feature_order) - 9
        feature_attributions: List[Dict[str, Any]] = []
        for i, feat_name in enumerate(self.feature_order):
            s_val = float(class_shap_slice[i])
            if abs(s_val) > 1e-4:
                raw_val = raw_vector[i]
                if np.isnan(raw_val):
                    val_json: Any = None
                elif i < n_symptoms:
                    val_json = int(raw_val)
                else:
                    val_json = round(float(raw_val), 2)

                feature_attributions.append({
                    "feature": feat_name,
                    "value": val_json,
                    "shap_value": round(s_val, 4),
                    "contribution": round(abs(s_val), 4),
                    "baseline": round(base_value, 4),
                    "direction": "increases_risk" if s_val > 0 else "decreases_risk",
                })

        # Sort features by descending absolute SHAP magnitude
        feature_attributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

        summary_text = self._generate_explanation_summary(
            predicted_condition=predicted_condition,
            feature_attributions=feature_attributions,
            tier=active_tier,
            tier2_attribution=tier2_attr,
        )

        # Clinical Recommendations
        if escalate_red_flag:
            recommendation = (
                "EMERGENCY CLINICAL TRIAGE: Red-flag features detected (acute chest pain, critical hypoxemia, or "
                "hypertensive emergency). Immediate emergency department evaluation recommended."
            )
        elif active_tier == "Undifferentiated":
            recommendation = (
                "Atypical or undifferentiated presentation. Observed symptoms do not form a classic single-disease pattern. "
                "Specialist clinical referral and comprehensive lab workup recommended."
            )
        elif assigned_risk == "HIGH":
            recommendation = "Urgent clinical medical evaluation and targeted diagnostic workup recommended."
        elif assigned_risk == "MODERATE":
            recommendation = "Clinical consultation recommended for confirmation, symptomatic relief, and follow-up monitoring."
        else:
            recommendation = "Routine medical consultation and supportive care. Return if symptoms worsen or new red flags develop."

        ranked_diagnoses = [
            {
                "disease": d["condition"],
                "condition": d["condition"],
                "probability": d["probability"],
                "risk_level": d["risk_level"],
                "severity": severity,
                "tier": d.get("tier", active_tier),
            }
            for d in primary_differentials
        ]

        explanation_payload = {
            "base_value": round(base_value, 4),
            "features": feature_attributions,
            "summary": summary_text,
        }

        # 8. Clinical Safety & Comprehensive Backward-Compatible Payload Contract
        return {
            "predicted_condition": predicted_condition,
            "confidence": confidence,
            "risk_level": assigned_risk,
            "severity": severity,
            "triage_level": assigned_risk,
            "recommendation": recommendation,
            "recommended_action": recommendation,
            "canonical_symptoms": canonical_symptoms,
            "differential_diagnoses": primary_differentials,
            "ranked_diagnoses": ranked_diagnoses,
            "ranked_diseases": ranked_diagnoses,
            "tier2_clinical_matches": tier2_matches_payload,
            "explanation": explanation_payload,
            "shap_analysis": explanation_payload,
            "shap_explanations": explanation_payload,
            "clinical_safety": {
                "is_definitive_diagnosis": False,
                "disclaimer": (
                    "Clinical decision support estimate only by automated clinical decision support system. "
                    "Not a definitive medical diagnosis. Requires clinical clinician evaluation."
                ),
            },
            "disclaimer": (
                "Clinical decision support estimate only by automated clinical decision support system. "
                "Not a definitive medical diagnosis. Requires clinical clinician evaluation."
            ),
            "model_metadata": {
                "model_name": self.model_name,
                "model_version": self.model_version,
                "schema_version": self.schema_version,
                "tier": active_tier,
                "total_classes": len(self.classes),
                "total_features": len(self.feature_order),
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
