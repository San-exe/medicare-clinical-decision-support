"""
MediCare AI Layer Package
Contains clinical preprocessor, disease risk inference, SHAP explanations, and RAG services.
"""

from .preprocessing import (
    ClinicalPreprocessor,
    PreprocessedClinicalData,
    preprocess_clinical_input,
    get_preprocessor,
    CANONICAL_SYMPTOMS,
)
from .engine import (
    DiseaseRiskEngine,
    ModelNotLoadedError,
    get_engine,
)

__all__ = [
    "ClinicalPreprocessor",
    "PreprocessedClinicalData",
    "preprocess_clinical_input",
    "get_preprocessor",
    "CANONICAL_SYMPTOMS",
    "DiseaseRiskEngine",
    "ModelNotLoadedError",
    "get_engine",
]

