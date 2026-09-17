"""
MediCare Clinical Decision Support System - Model Architecture & Training Pipeline
Trains a multi-class XGBoost classifier across 27 clinical features with native NaN missingness handling.
Serializes model artifacts, synced schema.json, and metadata.json to backend/ai/artifacts/v1.0.0/.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score, log_loss
import sys
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

# Ensure backend root is in sys.path for standalone or module execution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from ai.preprocessing import get_preprocessor
except ImportError:
    from backend.ai.preprocessing import get_preprocessor

# ---------------------------------------------------------------------------
# Default Constants & Disease Target Classes
# ---------------------------------------------------------------------------

DEFAULT_DISEASE_CLASSES: List[str] = [
    "Influenza",
    "Common Cold",
    "Pneumonia",
    "Type 2 Diabetes",
    "Hypertension",
    "Migraine",
    "Acute Gastroenteritis",
    "Bronchial Asthma",
]

DEFAULT_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DEFAULT_DATA_PATH = os.path.join(DEFAULT_DATA_DIR, "dev_dataset.csv")
DEFAULT_ARTIFACT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "ai", "artifacts", "v1.0.0"
)
SCHEMA_SOURCE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "ai", "schema.json"
)


# ---------------------------------------------------------------------------
# Clinically Realistic Synthetic Development Generator
# ---------------------------------------------------------------------------

def generate_synthetic_dev_data(
    n_samples_per_class: int = 350,
    random_state: int = 42,
    output_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    Generates clinically realistic development dataset for the 8 target conditions.
    Features: 18 canonical symptoms + 9 vitals/demographics.
    Injects realistic missingness (40-70% in unmeasured vitals) represented as np.nan.
    """
    rng = np.random.default_rng(random_state)
    preprocessor = get_preprocessor()
    feature_order = preprocessor.feature_order

    records: List[Dict[str, Any]] = []

    for disease in DEFAULT_DISEASE_CLASSES:
        for _ in range(n_samples_per_class):
            row: Dict[str, Any] = {feat: 0.0 for feat in feature_order[:18]}

            # Default demographic / vitals baseline
            age = float(rng.integers(18, 85))
            sex = float(rng.choice([1.0, 0.0], p=[0.48, 0.52]))
            systolic_bp = float(rng.normal(122, 10))
            diastolic_bp = float(rng.normal(80, 7))
            heart_rate = float(rng.normal(74, 9))
            glucose = float(rng.normal(95, 12))
            body_temperature = float(rng.normal(36.8, 0.4))
            oxygen_saturation = float(rng.normal(98.2, 1.0))
            bmi = float(rng.normal(25.0, 3.5))

            # Apply clinical disease profiles
            if disease == "Influenza":
                row["fever"] = 1.0 if rng.random() < 0.94 else 0.0
                row["body_aches"] = 1.0 if rng.random() < 0.90 else 0.0
                row["chills"] = 1.0 if rng.random() < 0.88 else 0.0
                row["fatigue"] = 1.0 if rng.random() < 0.92 else 0.0
                row["headache"] = 1.0 if rng.random() < 0.78 else 0.0
                row["cough"] = 1.0 if rng.random() < 0.72 else 0.0
                row["sore_throat"] = 1.0 if rng.random() < 0.55 else 0.0
                row["rhinorrhea"] = 1.0 if rng.random() < 0.40 else 0.0
                body_temperature = float(rng.normal(38.9, 0.5))
                heart_rate = float(rng.normal(92, 10))

            elif disease == "Common Cold":
                row["rhinorrhea"] = 1.0 if rng.random() < 0.96 else 0.0
                row["sore_throat"] = 1.0 if rng.random() < 0.90 else 0.0
                row["cough"] = 1.0 if rng.random() < 0.75 else 0.0
                row["fatigue"] = 1.0 if rng.random() < 0.50 else 0.0
                row["headache"] = 1.0 if rng.random() < 0.35 else 0.0
                row["fever"] = 1.0 if rng.random() < 0.15 else 0.0
                body_temperature = float(rng.normal(37.1, 0.3))

            elif disease == "Pneumonia":
                row["dyspnea"] = 1.0 if rng.random() < 0.94 else 0.0
                row["cough"] = 1.0 if rng.random() < 0.95 else 0.0
                row["fever"] = 1.0 if rng.random() < 0.90 else 0.0
                row["chest_pain"] = 1.0 if rng.random() < 0.82 else 0.0
                row["chills"] = 1.0 if rng.random() < 0.75 else 0.0
                row["fatigue"] = 1.0 if rng.random() < 0.70 else 0.0
                body_temperature = float(rng.normal(39.1, 0.6))
                oxygen_saturation = float(rng.normal(88.5, 3.2))  # Hypoxemia
                heart_rate = float(rng.normal(106, 12))           # Tachycardia

            elif disease == "Type 2 Diabetes":
                row["polyuria"] = 1.0 if rng.random() < 0.94 else 0.0
                row["polydipsia"] = 1.0 if rng.random() < 0.92 else 0.0
                row["fatigue"] = 1.0 if rng.random() < 0.76 else 0.0
                row["blurred_vision"] = 1.0 if rng.random() < 0.65 else 0.0
                row["weight_loss"] = 1.0 if rng.random() < 0.48 else 0.0
                glucose = float(rng.normal(185, 38))              # Hyperglycemia
                age = float(rng.integers(42, 80))
                bmi = float(rng.normal(31.8, 4.8))                # Elevated BMI

            elif disease == "Hypertension":
                row["headache"] = 1.0 if rng.random() < 0.78 else 0.0
                row["dizziness"] = 1.0 if rng.random() < 0.70 else 0.0
                row["blurred_vision"] = 1.0 if rng.random() < 0.50 else 0.0
                row["chest_pain"] = 1.0 if rng.random() < 0.38 else 0.0
                systolic_bp = float(rng.normal(162, 14))          # Hypertension Stage 2
                diastolic_bp = float(rng.normal(101, 8))
                age = float(rng.integers(45, 82))

            elif disease == "Migraine":
                row["headache"] = 1.0 if rng.random() < 0.98 else 0.0
                row["photophobia"] = 1.0 if rng.random() < 0.94 else 0.0
                row["nausea"] = 1.0 if rng.random() < 0.82 else 0.0
                row["dizziness"] = 1.0 if rng.random() < 0.58 else 0.0
                row["fatigue"] = 1.0 if rng.random() < 0.45 else 0.0

            elif disease == "Acute Gastroenteritis":
                row["diarrhea"] = 1.0 if rng.random() < 0.98 else 0.0
                row["nausea"] = 1.0 if rng.random() < 0.90 else 0.0
                row["body_aches"] = 1.0 if rng.random() < 0.45 else 0.0
                row["fatigue"] = 1.0 if rng.random() < 0.65 else 0.0
                row["fever"] = 1.0 if rng.random() < 0.35 else 0.0
                heart_rate = float(rng.normal(88, 11))

            elif disease == "Bronchial Asthma":
                row["dyspnea"] = 1.0 if rng.random() < 0.96 else 0.0
                row["cough"] = 1.0 if rng.random() < 0.84 else 0.0
                row["chest_pain"] = 1.0 if rng.random() < 0.65 else 0.0
                row["fatigue"] = 1.0 if rng.random() < 0.50 else 0.0
                oxygen_saturation = float(rng.normal(93.2, 2.5))

            # Add minor random background noise across unrelated symptoms (2-6% chance)
            for sym in feature_order[:18]:
                if row[sym] == 0.0 and rng.random() < 0.035:
                    row[sym] = 1.0

            # Realistic Outpatient Missingness Patterns (inject np.nan)
            vital_missing_prob = rng.random()

            # 1. Glucose: ~60% missing unless diabetic
            if (disease != "Type 2 Diabetes" and rng.random() < 0.65) or rng.random() < 0.25:
                glucose = np.nan

            # 2. SpO2: ~45% missing unless respiratory, but ~25% unmeasured in initial outpatient intake
            if disease not in ["Pneumonia", "Bronchial Asthma"]:
                if rng.random() < 0.50:
                    oxygen_saturation = np.nan
            else:
                if rng.random() < 0.25:
                    oxygen_saturation = np.nan

            # 3. BMI: ~40% missing across clinics
            if rng.random() < 0.42:
                bmi = np.nan

            # 4. Temperature: ~30% missing in non-febrile cases, ~20% unmeasured in initial self-triage
            if disease not in ["Influenza", "Pneumonia"]:
                if rng.random() < 0.35:
                    body_temperature = np.nan
            else:
                if rng.random() < 0.20:
                    body_temperature = np.nan

            # 5. Blood Pressure: ~25% missing in quick triage
            if disease != "Hypertension":
                if rng.random() < 0.28:
                    systolic_bp = np.nan
                    diastolic_bp = np.nan
            else:
                if rng.random() < 0.15:
                    systolic_bp = np.nan
                    diastolic_bp = np.nan

            # 6. Heart rate: ~20% missing
            if rng.random() < 0.20:
                heart_rate = np.nan

            # Pure symptom self-report without any clinic vitals (~18% of all presentations)
            if vital_missing_prob < 0.18:
                systolic_bp = np.nan
                diastolic_bp = np.nan
                heart_rate = np.nan
                glucose = np.nan
                body_temperature = np.nan
                oxygen_saturation = np.nan
                bmi = np.nan

            # Populate vitals
            row["age"] = round(age, 1)
            row["sex"] = sex
            row["systolic_bp"] = round(systolic_bp, 1) if not np.isnan(systolic_bp) else np.nan
            row["diastolic_bp"] = round(diastolic_bp, 1) if not np.isnan(diastolic_bp) else np.nan
            row["heart_rate"] = round(heart_rate, 1) if not np.isnan(heart_rate) else np.nan
            row["glucose"] = round(glucose, 1) if not np.isnan(glucose) else np.nan
            row["body_temperature"] = round(body_temperature, 2) if not np.isnan(body_temperature) else np.nan
            row["oxygen_saturation"] = round(oxygen_saturation, 1) if not np.isnan(oxygen_saturation) else np.nan
            row["bmi"] = round(bmi, 1) if not np.isnan(bmi) else np.nan

            row["target_disease"] = disease
            records.append(row)

    df = pd.DataFrame(records)
    # Shuffle
    df = df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"[*] Synthetic development dataset saved to: {output_path} ({len(df)} records)")

    return df


# ---------------------------------------------------------------------------
# Training Pipeline
# ---------------------------------------------------------------------------

def train_model(
    data_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    test_size: float = 0.2,
    random_state: int = 42,
    generate_dev: bool = False,
    n_samples_per_class: int = 350,
) -> Dict[str, Any]:
    """
    Executes production ML training pipeline:
    1. Ingests data (or generates realistic clinical dev data).
    2. Validates schema alignment across all 27 features.
    3. Trains multi-class XGBoost with native NaN split routing.
    4. Evaluates classification metrics (macro-F1, log-loss).
    5. Serializes artifacts: xgboost_model.joblib, schema.json, metadata.json.
    """
    output_dir = output_dir or DEFAULT_ARTIFACT_DIR
    data_path = data_path or DEFAULT_DATA_PATH
    os.makedirs(output_dir, exist_ok=True)

    preprocessor = get_preprocessor()
    feature_order = preprocessor.feature_order
    schema_version = preprocessor.version

    # 1. Dataset Resolution
    dataset_provenance = "clinical-curated"
    if generate_dev or not os.path.exists(data_path):
        print(f"[*] Generating synthetic clinical development data...")
        df = generate_synthetic_dev_data(
            n_samples_per_class=n_samples_per_class,
            random_state=random_state,
            output_path=data_path,
        )
        dataset_provenance = "synthetic-dev-fallback"
    else:
        print(f"[*] Loading training data from: {data_path}")
        df = pd.read_csv(data_path)

    # Validate target column
    if "target_disease" not in df.columns:
        raise ValueError("Dataset missing required target column 'target_disease'.")

    # Validate all 27 schema features exist
    missing_cols = [f for f in feature_order if f not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset missing required schema features: {missing_cols}")

    X = df[feature_order].copy()
    y_raw = df["target_disease"].copy()

    # 2. Label Encoding
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y_raw)
    classes = list(label_encoder.classes_)

    # 3. Stratified Train / Validation Split
    X_train, X_val, y_train, y_val = train_test_split(
        X,
        y,
        test_size=test_size,
        stratify=y,
        random_state=random_state,
    )

    # 4. Balanced Sample Weighting
    sample_weights = compute_sample_weight("balanced", y_train)

    # 5. XGBoost Classifier Configuration (Native NaN support)
    print(f"[*] Training multi-class XGBoost model on {len(X_train)} samples across {len(classes)} classes...")
    model = XGBClassifier(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        missing=np.nan,  # Native directional split routing for unmeasured vitals
        objective="multi:softprob",
        eval_metric="mlogloss",
        random_state=random_state,
        n_jobs=-1,
    )

    model.fit(
        X_train,
        y_train,
        sample_weight=sample_weights,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    # 6. Evaluation
    y_pred = model.predict(X_val)
    y_prob = model.predict_proba(X_val)

    macro_f1 = float(f1_score(y_val, y_pred, average="macro"))
    weighted_f1 = float(f1_score(y_val, y_pred, average="weighted"))
    acc = float(accuracy_score(y_val, y_pred))
    loss = float(log_loss(y_val, y_prob))
    report = classification_report(y_val, y_pred, target_names=classes, output_dict=True)

    print(f"[*] Training complete. Validation Metrics:")
    print(f"    - Macro F1-Score: {macro_f1:.4f}")
    print(f"    - Weighted F1:    {weighted_f1:.4f}")
    print(f"    - Accuracy:       {acc:.4f}")
    print(f"    - Log-Loss:       {loss:.4f}")

    # 7. Artifact Serialization
    # A. xgboost_model.joblib
    model_artifact_path = os.path.join(output_dir, "xgboost_model.joblib")
    artifact_payload = {
        "model": model,
        "label_encoder": label_encoder,
        "classes": classes,
        "feature_order": feature_order,
        "schema_version": schema_version,
    }
    joblib.dump(artifact_payload, model_artifact_path)
    print(f"[+] Serialized model artifact to: {model_artifact_path}")

    # B. schema.json (Synced contract copy)
    artifact_schema_path = os.path.join(output_dir, "schema.json")
    if os.path.exists(SCHEMA_SOURCE_PATH):
        shutil.copy2(SCHEMA_SOURCE_PATH, artifact_schema_path)
        print(f"[+] Synced schema contract to: {artifact_schema_path}")

    # C. metadata.json
    metadata_payload = {
        "model_name": "MediCare-MultiDisease-XGBoost",
        "version": schema_version,
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_provenance": dataset_provenance,
        "target_classes": classes,
        "total_classes": len(classes),
        "total_features": len(feature_order),
        "feature_order": feature_order,
        "metrics": {
            "macro_f1": round(macro_f1, 4),
            "weighted_f1": round(weighted_f1, 4),
            "accuracy": round(acc, 4),
            "log_loss": round(loss, 4),
            "per_class_metrics": {
                c: {
                    "precision": round(report[c]["precision"], 4),
                    "recall": round(report[c]["recall"], 4),
                    "f1_score": round(report[c]["f1-score"], 4),
                    "support": int(report[c]["support"]),
                }
                for c in classes
                if c in report
            },
        },
        "training_config": {
            "n_estimators": 120,
            "max_depth": 5,
            "learning_rate": 0.08,
            "missing_value_handling": "native_directional_split_np_nan",
            "objective": "multi:softprob",
        },
    }

    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata_payload, f, indent=2)
    print(f"[+] Serialized metadata manifest to: {metadata_path}")

    return {
        "model_path": model_artifact_path,
        "schema_path": artifact_schema_path,
        "metadata_path": metadata_path,
        "metrics": metadata_payload["metrics"],
        "classes": classes,
        "dataset_provenance": dataset_provenance,
    }


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="MediCare Multi-Disease Model Training & Artifact Serialization"
    )
    parser.add_argument(
        "--generate-dev-data",
        action="store_true",
        help="Generate synthetic clinical development dataset in backend/ml/data/",
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=DEFAULT_DATA_PATH,
        help="Path to training data CSV",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_ARTIFACT_DIR,
        help="Path to output artifacts directory",
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=350,
        help="Samples per class for development generator (default: 350 -> 2800 total)",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Hold-out validation split ratio (default: 0.2)",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )

    args = parser.parse_args()

    train_model(
        data_path=args.data_path,
        output_dir=args.output_dir,
        test_size=args.test_size,
        random_state=args.random_state,
        generate_dev=args.generate_dev_data,
        n_samples_per_class=args.n_samples,
    )


if __name__ == "__main__":
    main()
