import os
import requests

BASE_URL = os.getenv("OPENFDA_BASE_URL", "https://api.fda.gov/drug")


def search_drug(name: str) -> dict:
    response = requests.get(
        f"{BASE_URL}/label.json",
        params={"search": f'openfda.brand_name:"{name}"', "limit": 5},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
