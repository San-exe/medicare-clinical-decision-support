"""
RAG Service Orchestration Boundary.

Provides external API entry point routing to the canonical
RAGAssistantEngine in apps.assistant.services.rag_engine.
"""
from typing import Dict, Any, Optional
from apps.assistant.services.rag_engine import rag_assistant_engine, MANDATORY_REGULATORY_DISCLAIMER
from apps.assistant.services.pubmed_service import pubmed_service
from apps.assistant.services.llm_provider import get_llm_provider


def answer_with_evidence(
    question: str,
    patient_user=None,
    limit_citations: int = 3,
) -> Dict[str, Any]:
    """
    Synthesizes an evidence-grounded clinical response for a clinical question.
    Can be used standalone or within authenticated user sessions.
    """
    clean_q = question.strip()
    if not clean_q:
        return {
            "query": "",
            "response": "Clinical question cannot be empty.",
            "citations": [],
            "disclaimer": MANDATORY_REGULATORY_DISCLAIMER,
            "status": "empty",
        }

    # 1. Literature Retrieval
    pubmed_res = pubmed_service.search_pubmed(clean_q, limit=limit_citations, fetch_abstracts=True)
    citations = pubmed_res.get("citations", [])

    # 2. Patient Context
    patient_context = rag_assistant_engine._build_patient_context(patient_user) if patient_user else ""

    # 3. LLM Generation
    llm_res = get_llm_provider().generate_response(clean_q, citations, patient_context)

    return {
        "query": clean_q,
        "response": llm_res.get("response", ""),
        "citations": citations,
        "disclaimer": MANDATORY_REGULATORY_DISCLAIMER,
        "provider": llm_res.get("provider", "extractive"),
        "model": llm_res.get("model", "grounded_rules"),
        "grounded": llm_res.get("grounded", bool(citations)),
        "status": "success" if citations else "no_results",
    }

