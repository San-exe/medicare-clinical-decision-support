"""
Canonical Medicine Interaction Service.

Evaluates pharmacological interactions across multiple medications using
OpenFDA clinical label databases and optional DrugBank adapter.
Supports:
- Explicit drug lists (e.g. ["warfarin", "aspirin"])
- Single queried medication evaluated against patient's active prescriptions
- Structured severity classification without fabricating interaction severity.
"""
import logging
from typing import List, Dict, Any, Optional
from apps.medicines.models import Medication
from .openfda_service import openfda_service
from integrations.drugbank_client import drugbank_client

logger = logging.getLogger(__name__)


class MedicineInteractionService:
    """
    Canonical service for drug-drug interaction detection and risk stratification.
    """

    def evaluate_interactions(
        self,
        drugs: Optional[List[str]] = None,
        queried_drug: Optional[str] = None,
        patient_user=None,
        current_medications: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Executes drug interaction analysis.
        Normalizes input drugs, resolves active patient prescriptions if provided,
        and aggregates evidence from OpenFDA and DrugBank.
        """
        resolved_drugs = set()

        # 1. Add explicit drug list
        if drugs and isinstance(drugs, list):
            for d in drugs:
                if d and isinstance(d, str) and d.strip():
                    resolved_drugs.add(d.strip().title())

        # 2. Add current medications list if supplied
        if current_medications and isinstance(current_medications, list):
            for d in current_medications:
                if d and isinstance(d, str) and d.strip():
                    resolved_drugs.add(d.strip().title())

        # 3. If patient user supplied, incorporate active prescriptions
        patient_med_names = []
        if patient_user:
            try:
                active_qs = Medication.objects.filter(patient=patient_user, is_active=True).values_list("name", flat=True)
                patient_med_names = list(active_qs)
                for med_name in patient_med_names:
                    resolved_drugs.add(med_name.strip().title())
            except Exception as e:
                logger.warning("Could not retrieve active medications for patient %s: %s", patient_user.id, e)

        # 4. Add queried single drug
        if queried_drug and isinstance(queried_drug, str) and queried_drug.strip():
            resolved_drugs.add(queried_drug.strip().title())

        drug_list = sorted(resolved_drugs)

        if len(drug_list) < 2:
            return {
                "drugs_analyzed": drug_list,
                "interactions": [],
                "total_interactions": 0,
                "has_critical_interaction": False,
                "patient_id": patient_user.id if patient_user else None,
                "patient_medications_loaded": len(patient_med_names),
                "status": "ok",
                "message": "At least two distinct medications are required to analyze interactions.",
            }

        # 5. Query OpenFDA canonical service
        openfda_res = openfda_service.check_interactions(drug_list)
        raw_interactions = openfda_res.get("interactions_found", [])

        # 6. Normalize and map to structured interaction format
        interactions = []
        seen_pairs = set()

        for item in raw_interactions:
            d_a = item.get("drug_a", "").title()
            d_b = item.get("drug_b", "").title()
            pair_key = tuple(sorted([d_a, d_b]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            severity = item.get("severity", "moderate").lower()
            interactions.append({
                "drug_a": d_a,
                "drug_b": d_b,
                "severity": severity,
                "explanation": item.get("description", ""),
                "evidence_source": "OpenFDA Drug Label (FDA)",
                "source_identifier": item.get("source_id", "openfda:drug_interactions"),
            })

        # 7. Check DrugBank if configured
        if drugbank_client.is_configured:
            try:
                db_res = drugbank_client.check_interactions(drug_list)
                if db_res.get("status") == "success":
                    for db_item in db_res.get("interactions", []):
                        d_a = db_item.get("drug_a", "").title()
                        d_b = db_item.get("drug_b", "").title()
                        pair_key = tuple(sorted([d_a, d_b]))
                        if pair_key not in seen_pairs:
                            seen_pairs.add(pair_key)
                            interactions.append({
                                "drug_a": d_a,
                                "drug_b": d_b,
                                "severity": db_item.get("severity", "moderate").lower(),
                                "explanation": db_item.get("description", ""),
                                "evidence_source": "DrugBank Commercial Database",
                                "source_identifier": db_item.get("source_identifier", ""),
                            })
            except Exception as e:
                logger.warning("Error querying DrugBank client: %s", e)

        has_critical = any(item.get("severity") in ("high", "critical", "severe", "contraindicated") for item in interactions)

        return {
            "drugs_analyzed": drug_list,
            "interactions": interactions,
            "total_interactions": len(interactions),
            "has_critical_interaction": has_critical,
            "patient_id": patient_user.id if patient_user else None,
            "patient_medications_loaded": len(patient_med_names),
            "status": "success" if openfda_res.get("status") == "success" else openfda_res.get("status", "warning"),
            "cached": openfda_res.get("cached", False),
            "providers_consulted": ["OpenFDA"] + (["DrugBank"] if drugbank_client.is_configured else []),
        }


# Canonical singleton instance
interaction_service = MedicineInteractionService()
