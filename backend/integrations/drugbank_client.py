"""Optional DrugBank integration boundary.
The SRS names DrugBank/OpenFDA; keep credentials and vendor-specific details out of app views.
"""


def get_drugbank_info(name: str) -> dict:
    raise NotImplementedError("Configure the licensed DrugBank API in Milestone 5.")
