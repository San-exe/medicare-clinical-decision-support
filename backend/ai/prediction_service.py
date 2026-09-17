"""Milestone 4 AI service boundary.
Keep ML loading/inference out of DRF views; call these services from predictions/services.py.
"""


def predict_disease(input_data: dict) -> dict:
    raise NotImplementedError("Connect the trained Scikit-learn/XGBoost model in Milestone 4.")
