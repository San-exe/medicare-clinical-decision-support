"""
MediCare AI Layer Package
Contains clinical preprocessor, disease risk inference, SHAP explanations, and Tier 2 Knowledge Matcher.
"""

from .preprocessing import (
    ClinicalPreprocessor,
    PreprocessedClinicalData,
    preprocess_clinical_input,
    get_preprocessor,
    get_preprocessor_v2,
    CANONICAL_SYMPTOMS,
)
from .engine import (
    DiseaseRiskEngine,
    ModelNotLoadedError,
    get_engine,
)
from .clinical_kb import (
    ClinicalKnowledgeMatcher,
    DifferentialDiagnosisCandidate,
    get_knowledge_matcher,
)

__all__ = [
    "ClinicalPreprocessor",
    "PreprocessedClinicalData",
    "preprocess_clinical_input",
    "get_preprocessor",
    "get_preprocessor_v2",
    "CANONICAL_SYMPTOMS",
    "DiseaseRiskEngine",
    "ModelNotLoadedError",
    "get_engine",
    "ClinicalKnowledgeMatcher",
    "DifferentialDiagnosisCandidate",
    "get_knowledge_matcher",
]
