"""Milestone 4 symptom/NLP processing boundary."""


def normalize_symptoms(text: str) -> list[str]:
    return [item.strip() for item in text.split(",") if item.strip()]
