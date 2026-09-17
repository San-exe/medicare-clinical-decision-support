"""
PubMed Integration Adapter.

Provides functional integration boundary delegating to the canonical
PubMedService in apps.assistant.services.pubmed_service.
"""
import os
from typing import List, Dict, Any
from apps.assistant.services.pubmed_service import pubmed_service, PubMedService

BASE_URL = os.getenv("PUBMED_BASE_URL", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils")


def search_pubmed(query: str, retmax: int = 5, fetch_abstracts: bool = True) -> List[Dict[str, Any]]:
    """
    Searches PubMed and retrieves citations with metadata and abstracts.
    Preserves backwards-compatible schema where each citation includes 'pmid'.
    """
    clean_query = query.strip()
    if not clean_query:
        return []

    res = pubmed_service.search_pubmed(clean_query, limit=retmax, fetch_abstracts=fetch_abstracts)
    citations = res.get("citations", [])
    return citations

