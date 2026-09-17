"""
Tier 2 Clinical Knowledge Base & Open-World Diagnostic Matcher.

Covers 500+ clinical conditions with ICD-10 codes, pathognomonic hallmarks,
secondary symptoms, typical vitals, and TF-IDF weighted Cosine / Jaccard similarity scoring.
"""
from dataclasses import dataclass, field
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

DEFAULT_KB_PATH = os.path.join(os.path.dirname(__file__), "clinical_kb_data.json")


@dataclass
class DifferentialDiagnosisCandidate:
    """Represents a scored candidate condition in the Tier 2 differential diagnosis."""
    condition_id: str
    name: str
    category: str
    icd10: str
    urgency: str
    score: float
    confidence_pct: float
    matched_features: List[str]
    matched_hallmarks: List[str]
    missing_hallmarks: List[str]
    description: str
    typical_vitals: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "name": self.name,
            "category": self.category,
            "icd10": self.icd10,
            "urgency": self.urgency,
            "score": self.score,
            "confidence_pct": self.confidence_pct,
            "matched_features": self.matched_features,
            "matched_hallmarks": self.matched_hallmarks,
            "missing_hallmarks": self.missing_hallmarks,
            "description": self.description,
            "typical_vitals": self.typical_vitals,
        }


class ClinicalKnowledgeMatcher:
    """
    Tier 2 retrieval and differential ranking engine.
    Matches observed patient symptoms against 500+ clinical conditions using
    TF-IDF weighted Cosine and Jaccard similarity with pathognomonic hallmark boosting.
    """

    HALLMARK_WEIGHT_MULTIPLIER = 2.5
    SECONDARY_WEIGHT_MULTIPLIER = 1.0

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path or DEFAULT_KB_PATH
        self.conditions: List[Dict[str, Any]] = []
        self.conditions_by_id: Dict[str, Dict[str, Any]] = {}
        self.idf_weights: Dict[str, float] = {}
        self.condition_vectors: Dict[str, Dict[str, float]] = {}
        self.condition_norms: Dict[str, float] = {}

        self._load_and_index()

    def _load_and_index(self) -> None:
        """Loads conditions catalog and computes TF-IDF index matrices."""
        with open(self.data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        self.conditions = raw_data.get("conditions", [])
        self.conditions_by_id = {c["id"]: c for c in self.conditions}
        n_conditions = max(1, len(self.conditions))

        # 1. Calculate Document Frequencies (DF)
        df_counts: Dict[str, int] = {}
        for cond in self.conditions:
            cond_symptoms = set(cond.get("pathognomonic_symptoms", []) + cond.get("secondary_symptoms", []))
            for s in cond_symptoms:
                df_counts[s] = df_counts.get(s, 0) + 1

        # 2. Calculate Inverse Document Frequency (IDF) with smoothing
        # Rare specific symptoms (e.g. jaundice, hematuria) get significantly higher weight than ubiquitous ones
        for sym, count in df_counts.items():
            # Smooth IDF formula: ln((N + 1) / (DF + 1)) + 1.0
            self.idf_weights[sym] = round(math.log((n_conditions + 1.0) / (count + 1.0)) + 1.0, 4)

        # 3. Precompute condition symptom vectors and L2 norms
        for cond in self.conditions:
            cid = cond["id"]
            patho_set = set(cond.get("pathognomonic_symptoms", []))
            sec_set = set(cond.get("secondary_symptoms", []))

            vec: Dict[str, float] = {}
            sum_sq = 0.0

            for s in patho_set:
                idf = self.idf_weights.get(s, 1.0)
                w = idf * self.HALLMARK_WEIGHT_MULTIPLIER
                vec[s] = w
                sum_sq += w * w

            for s in sec_set:
                if s not in vec:
                    idf = self.idf_weights.get(s, 1.0)
                    w = idf * self.SECONDARY_WEIGHT_MULTIPLIER
                    vec[s] = w
                    sum_sq += w * w

            self.condition_vectors[cid] = vec
            self.condition_norms[cid] = math.sqrt(sum_sq) if sum_sq > 0 else 1.0

    @property
    def condition_count(self) -> int:
        return len(self.conditions)

    def get_condition(self, condition_id: str) -> Optional[Dict[str, Any]]:
        return self.conditions_by_id.get(condition_id)

    def match(
        self,
        symptoms: Union[List[str], Set[str], str],
        vitals: Optional[Dict[str, float]] = None,
        top_k: int = 5,
        min_score: float = 0.05,
    ) -> List[DifferentialDiagnosisCandidate]:
        """
        Calculates differential diagnosis candidates based on TF-IDF Cosine/Jaccard similarity.

        Args:
            symptoms: List, set of symptom slugs, or free-text string/list.
            vitals: Optional patient vitals dictionary for clinical coherence verification.
            top_k: Number of highest ranking conditions to return.
            min_score: Threshold minimum composite score.

        Returns:
            List of DifferentialDiagnosisCandidate objects sorted descending by score.
        """
        # Resolve symptoms input to canonical set
        query_symptoms: Set[str] = set()
        if isinstance(symptoms, str):
            # Parse using v2 preprocessor
            from ai.preprocessing import get_preprocessor_v2
            prep = get_preprocessor_v2()
            parsed = prep.preprocess(symptoms)
            query_symptoms = set(parsed.canonical_symptoms)
        elif isinstance(symptoms, (list, set)):
            # Check if elements are already canonical slugs
            raw_elements = [str(s) for s in symptoms]
            if any(" " in s for s in raw_elements):
                from ai.preprocessing import get_preprocessor_v2
                prep = get_preprocessor_v2()
                parsed = prep.preprocess(raw_elements)
                query_symptoms = set(parsed.canonical_symptoms)
            else:
                query_symptoms = set(raw_elements)

        if not query_symptoms:
            return []

        # Build query vector and L2 norm
        query_vec: Dict[str, float] = {}
        query_sq = 0.0
        for s in query_symptoms:
            idf = self.idf_weights.get(s, 1.0)
            query_vec[s] = idf
            query_sq += idf * idf
        query_norm = math.sqrt(query_sq) if query_sq > 0 else 1.0

        candidates: List[DifferentialDiagnosisCandidate] = []

        for cond in self.conditions:
            cid = cond["id"]
            cond_vec = self.condition_vectors.get(cid, {})
            cond_norm = self.condition_norms.get(cid, 1.0)
            patho_set = set(cond.get("pathognomonic_symptoms", []))
            all_cond_syms = set(cond_vec.keys())

            intersection = query_symptoms.intersection(all_cond_syms)
            if not intersection:
                continue

            matched_hallmarks = sorted(list(intersection.intersection(patho_set)))
            missing_hallmarks = sorted(list(patho_set.difference(query_symptoms)))
            matched_features = sorted(list(intersection))

            # 1. TF-IDF Cosine Similarity
            dot_product = sum(query_vec[s] * cond_vec[s] for s in intersection)
            cosine_sim = dot_product / (query_norm * cond_norm)

            # 2. Weighted Jaccard Similarity
            intersection_weight = sum(cond_vec[s] for s in intersection)
            union_syms = query_symptoms.union(all_cond_syms)
            union_weight = sum(max(query_vec.get(s, 0.0), cond_vec.get(s, 0.0)) for s in union_syms)
            jaccard_sim = (intersection_weight / union_weight) if union_weight > 0 else 0.0

            # 3. Composite score (70% Cosine, 30% Jaccard)
            composite = 0.70 * cosine_sim + 0.30 * jaccard_sim

            # 4. Hallmark Coverage Adjustment
            if patho_set:
                hallmark_coverage = len(matched_hallmarks) / float(len(patho_set))
                if hallmark_coverage == 1.0:
                    composite = min(1.0, composite * 1.20)
                elif hallmark_coverage >= 0.5:
                    composite = min(1.0, composite * 1.08)
                elif hallmark_coverage == 0.0:
                    composite = composite * 0.75

            # 5. Vitals Coherence Adjustment (optional fine-tuning)
            if vitals:
                typ = cond.get("typical_vitals", {})
                if "body_temperature" in vitals and "body_temperature" in typ:
                    temp_patient = vitals["body_temperature"]
                    temp_typical = typ["body_temperature"]
                    # If both elevated (>38.0) or both normal (<=37.5)
                    if (temp_patient >= 38.0 and temp_typical >= 38.0) or (temp_patient <= 37.5 and temp_typical <= 37.5):
                        composite = min(1.0, composite * 1.04)

            score = round(max(0.0, min(1.0, composite)), 4)
            if score >= min_score:
                candidates.append(
                    DifferentialDiagnosisCandidate(
                        condition_id=cid,
                        name=cond.get("name", cid),
                        category=cond.get("category", "General"),
                        icd10=cond.get("icd10", ""),
                        urgency=cond.get("urgency", "routine"),
                        score=score,
                        confidence_pct=round(score * 100.0, 2),
                        matched_features=matched_features,
                        matched_hallmarks=matched_hallmarks,
                        missing_hallmarks=missing_hallmarks,
                        description=cond.get("description", ""),
                        typical_vitals=cond.get("typical_vitals", {}),
                    )
                )

        # Sort descending by score
        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates[:top_k]


# ---------------------------------------------------------------------------
# Singleton Factory
# ---------------------------------------------------------------------------

_KNOWLEDGE_MATCHER_INSTANCE: Optional[ClinicalKnowledgeMatcher] = None


def get_knowledge_matcher() -> ClinicalKnowledgeMatcher:
    """Returns singleton instance of the Tier 2 Clinical Knowledge Matcher."""
    global _KNOWLEDGE_MATCHER_INSTANCE
    if _KNOWLEDGE_MATCHER_INSTANCE is None:
        _KNOWLEDGE_MATCHER_INSTANCE = ClinicalKnowledgeMatcher()
    return _KNOWLEDGE_MATCHER_INSTANCE
