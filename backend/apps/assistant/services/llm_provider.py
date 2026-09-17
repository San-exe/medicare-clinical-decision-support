"""
LLM Provider Abstraction for Clinical Decision Support.

Provides a pluggable LLM interface supporting multiple generative providers
(Google Gemini, OpenAI) and a resilient literature-grounded extractive fallback
when live external API credentials are not configured in the environment.

Enforces Medical Safety:
- Grounded strictly in retrieved literature and clinical context.
- Distinguishes evidence from interpretation.
- Cites specific PMIDs.
- Refuses to fabricate unsupported medical claims, autonomous diagnoses, or prescriptions.
- Reminds user to consult licensed clinicians.
"""
import json
import logging
import os
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


CLINICAL_SYSTEM_PROMPT = """You are an evidence-grounded Clinical Decision Support Assistant.
Your responsibility is to provide accurate, literature-grounded clinical summaries to support healthcare providers and patients.
Strict Rules:
1. Base your answer strictly on the provided Medical Literature and Patient Context.
2. Clearly distinguish documented evidence from clinical interpretation.
3. Explicitly cite PMIDs from the literature provided (e.g., [PMID: 12345678]).
4. Do NOT fabricate clinical claims, diagnostic certainty, or specific drug dosages.
5. If the provided literature does not contain sufficient evidence to answer the question, state that explicitly.
6. Emphasize that clinical judgment and consultation with a licensed healthcare provider are required."""


class BaseLLMProvider:
    """Abstract interface for LLM clinical generation."""

    def generate_response(
        self,
        prompt: str,
        citations: List[Dict[str, Any]],
        patient_context: str = "",
    ) -> Dict[str, Any]:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider using REST API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-flash",
        timeout: float = 12.0,
    ):
        self.api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY", "")
            or os.getenv("GOOGLE_API_KEY", "")
            or os.getenv("LLM_API_KEY", "")
        ).strip()
        self.model = os.getenv("LLM_MODEL", "").strip() or model
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_response(
        self,
        prompt: str,
        citations: List[Dict[str, Any]],
        patient_context: str = "",
    ) -> Dict[str, Any]:
        if not self.is_configured:
            return GroundedExtractiveProvider().generate_response(prompt, citations, patient_context)

        lit_parts = []
        for i, cit in enumerate(citations, 1):
            pmid = cit.get("pmid", "N/A")
            title = cit.get("title", "")
            journal = cit.get("journal", "")
            year = cit.get("year", "")
            abstract = cit.get("abstract", "")
            snippet = f"[{i}] PMID: {pmid} | {title} ({journal}, {year})\nAbstract: {abstract}"
            lit_parts.append(snippet)

        literature_text = "\n\n".join(lit_parts) if lit_parts else "No specific PubMed literature retrieved."

        user_content = (
            f"Clinical Question: {prompt}\n\n"
            f"Patient Context: {patient_context or 'None'}\n\n"
            f"Retrieved Medical Evidence:\n{literature_text}\n\n"
            "Please generate an evidence-grounded clinical explanation citing the PMIDs above."
        )

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{CLINICAL_SYSTEM_PROMPT}\n\n{user_content}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
            },
        }

        try:
            res = requests.post(endpoint, json=payload, timeout=self.timeout)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    answer = "".join(p.get("text", "") for p in parts).strip()
                    if answer:
                        return {
                            "response": answer,
                            "provider": "gemini",
                            "model": self.model,
                            "grounded": bool(citations),
                            "llm_active": True,
                        }
            logger.warning("Gemini API call returned status %s: %s", res.status_code, res.text[:200])
        except Exception as e:
            logger.warning("Gemini LLM request failed: %s; falling back to extractive synthesis.", e)

        # Fallback to extractive synthesis
        return GroundedExtractiveProvider().generate_response(prompt, citations, patient_context)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI compatible LLM provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        timeout: float = 12.0,
    ):
        self.api_key = (api_key or os.getenv("OPENAI_API_KEY", "")).strip()
        self.model = os.getenv("LLM_MODEL", "").strip() or model
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_response(
        self,
        prompt: str,
        citations: List[Dict[str, Any]],
        patient_context: str = "",
    ) -> Dict[str, Any]:
        if not self.is_configured:
            return GroundedExtractiveProvider().generate_response(prompt, citations, patient_context)

        lit_parts = []
        for i, cit in enumerate(citations, 1):
            pmid = cit.get("pmid", "N/A")
            title = cit.get("title", "")
            journal = cit.get("journal", "")
            year = cit.get("year", "")
            abstract = cit.get("abstract", "")
            lit_parts.append(f"[{i}] PMID: {pmid} | {title} ({journal}, {year})\nAbstract: {abstract}")

        user_content = (
            f"Clinical Question: {prompt}\n\n"
            f"Patient Context: {patient_context or 'None'}\n\n"
            f"Retrieved Evidence:\n" + ("\n\n".join(lit_parts) if lit_parts else "No retrieved literature.")
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": CLINICAL_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.2,
        }

        try:
            res = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=self.timeout,
            )
            if res.status_code == 200:
                data = res.json()
                answer = data["choices"][0]["message"]["content"].strip()
                return {
                    "response": answer,
                    "provider": "openai",
                    "model": self.model,
                    "grounded": bool(citations),
                    "llm_active": True,
                }
        except Exception as e:
            logger.warning("OpenAI LLM request failed: %s; falling back to extractive synthesis.", e)

        return GroundedExtractiveProvider().generate_response(prompt, citations, patient_context)


class GroundedExtractiveProvider(BaseLLMProvider):
    """
    Evidence-grounded extractive synthesizer.
    Used when external LLM credentials are not configured or when network is offline.
    Directly formats retrieved PubMed evidence and patient context without hallucination.
    """

    def generate_response(
        self,
        prompt: str,
        citations: List[Dict[str, Any]],
        patient_context: str = "",
    ) -> Dict[str, Any]:
        paragraphs = []

        # 1. Clinical query scope
        clean_q = prompt.strip()
        paragraphs.append(
            f"Clinical Assessment regarding '{clean_q}': "
            "Evidence-based guidelines prioritize early risk stratification, systematic symptom monitoring, "
            "and protocolized clinical management."
        )

        # 2. Patient Context
        if patient_context:
            paragraphs.append(
                f"Patient Clinical Context: {patient_context} "
                "Active medications and laboratory findings must be reviewed for potential contraindications."
            )

        # 3. Evidence grounding
        if citations:
            evidence_lines = []
            for i, cit in enumerate(citations[:4], 1):
                pmid = cit.get("pmid", "N/A")
                title = cit.get("title", "Clinical Study")
                journal = cit.get("journal", "PubMed Literature")
                year = cit.get("year", "Recent")
                abstract = cit.get("abstract", "")
                entry = f"[{i}] {title} ({journal}, {year}) [PMID: {pmid}]"
                if abstract and len(abstract) > 30:
                    summary_snippet = abstract[:220].rstrip(".") + "..."
                    entry += f"\n    Key Finding: {summary_snippet}"
                evidence_lines.append(entry)

            paragraphs.append("Relevant peer-reviewed literature:\n• " + "\n• ".join(evidence_lines))
        else:
            paragraphs.append(
                "No direct peer-reviewed literature matches were retrieved for this specific query. "
                "Clinicians should refer to standard guideline-directed medical therapy (GDMT)."
            )

        # 4. Clinical safety triage
        paragraphs.append(
            "Clinical Advisory: In the presence of acute or worsening symptoms (such as acute chest discomfort, "
            "severe dyspnea, or altered mental status), immediate medical evaluation is required."
        )

        return {
            "response": "\n\n".join(paragraphs),
            "provider": "extractive_synthesizer",
            "model": "rule_based_grounding",
            "grounded": bool(citations),
            "llm_active": False,
        }


def get_llm_provider() -> BaseLLMProvider:
    """
    Factory resolving active LLM provider based on environment configuration.
    """
    provider_name = os.getenv("LLM_PROVIDER", "").strip().lower()

    if provider_name == "gemini" or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        gemini = GeminiProvider()
        if gemini.is_configured:
            return gemini

    if provider_name == "openai" or os.getenv("OPENAI_API_KEY"):
        openai_prov = OpenAIProvider()
        if openai_prov.is_configured:
            return openai_prov

    return GroundedExtractiveProvider()
