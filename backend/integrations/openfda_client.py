"""
OpenFDA Integration Adapter.

Provides functional boundary and adapter methods routing to the canonical
OpenFDAService in apps.medicines.services.openfda_service.
"""
import os
import requests
from typing import Dict, Any, List
from apps.medicines.services.openfda_service import openfda_service, OpenFDAService

BASE_URL = os.getenv("OPENFDA_BASE_URL", "https://api.fda.gov/drug")


def search_drug(name: str, limit: int = 5) -> Dict[str, Any]:
    """
    Searches OpenFDA drug label records for brand or generic name.
    """
    clean_name = name.strip()
    if not clean_name:
        return {"results": [], "total": 0, "status": "empty"}

    try:
        response = requests.get(
            f"{BASE_URL}/label.json",
            params={"search": f'openfda.brand_name:"{clean_name}"+openfda.generic_name:"{clean_name}"', "limit": limit},
            timeout=openfda_service.TIMEOUT,
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return {"results": [], "total": 0, "status": "not_found", "message": f"No OpenFDA label found for '{clean_name}'."}
        else:
            return {"results": [], "total": 0, "status": "error", "message": f"OpenFDA returned status {response.status_code}."}
    except requests.RequestException as e:
        return {"results": [], "total": 0, "status": "error", "message": f"OpenFDA request failed: {str(e)}"}


def get_adverse_reactions(drug_name: str, limit: int = 5) -> Dict[str, Any]:
    """Retrieves adverse reactions via canonical openfda_service."""
    return openfda_service.get_adverse_reactions(drug_name, limit=limit)


def get_boxed_warnings_and_precautions(drug_name: str) -> Dict[str, Any]:
    """Retrieves boxed warnings & precautions via canonical openfda_service."""
    return openfda_service.get_boxed_warnings_and_precautions(drug_name)


def check_interactions(drug_list: List[str]) -> Dict[str, Any]:
    """Evaluates drug interactions via canonical openfda_service."""
    return openfda_service.check_interactions(drug_list)

