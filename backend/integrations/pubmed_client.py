import os
import requests

BASE_URL = os.getenv("PUBMED_BASE_URL", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils")


def search_pubmed(query: str, retmax: int = 5) -> list[dict]:
    # Milestone 5: replace with robust parsing, retries, rate limits, and source normalization.
    params = {"db": "pubmed", "term": query, "retmax": retmax, "retmode": "json"}
    response = requests.get(f"{BASE_URL}/esearch.fcgi", params=params, timeout=10)
    response.raise_for_status()
    ids = response.json().get("esearchresult", {}).get("idlist", [])
    return [{"pmid": pmid} for pmid in ids]
