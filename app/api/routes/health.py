from __future__ import annotations

from fastapi import APIRouter

from app.analysis_registry import ANALYSIS_REGISTRY
from app.core.deps import get_rag_agent, rag_enabled, rag_init_error
from app.llm_service import check_ollama_health

router = APIRouter(tags=["health"])


EXAMPLE_QUESTIONS = {
    "repeat_customer": [
        "siapa pelanggan loyal saya?",
        "pelanggan mana yang paling sering belanja?",
    ],
    "peak_hour": [
        "jam berapa transaksi paling ramai?",
        "jam belanja paling padat kapan?",
    ],
    "bundle_opportunity": [
        "barang apa yang cocok dibundling?",
        "produk mana yang paling cocok dijual paket?",
    ],
    "high_value_customer": [
        "siapa customer dengan total belanja terbesar?",
        "siapa pembeli dengan nilai transaksi paling besar?",
    ],
}


@router.get("/")
def root() -> dict:
    return {"message": "Fortunas AI backend is running"}


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok", "rag_enabled": rag_enabled()}


@router.get("/llm/health")
def llm_health() -> dict:
    return check_ollama_health()


@router.get("/rag/health")
def rag_health() -> dict:
    agent = get_rag_agent()
    return {
        "status": "ok" if agent else "error",
        "rag_enabled": agent is not None,
        "collection_count": agent.count() if agent else 0,
        "error": rag_init_error(),
    }


@router.get("/rag/search")
def rag_search(query: str, analysis: str | None = None, n_results: int = 4) -> dict:
    agent = get_rag_agent()
    if not agent:
        return {
            "status": "error",
            "message": f"RAG belum siap: {rag_init_error()}",
            "results": [],
        }

    results = agent.retrieve_debug(
        query=query,
        mapped_analysis=analysis,
        n_results=n_results,
    )
    return {
        "status": "success",
        "query": query,
        "analysis": analysis,
        "count": len(results),
        "results": results,
    }


@router.get("/analyses")
def list_available_analyses() -> dict:
    return {
        "available_analyses": [
            {
                "key": key,
                "label": value["label"],
                "description": value["description"],
                "enabled": value["enabled"],
            }
            for key, value in ANALYSIS_REGISTRY.items()
        ]
    }


@router.get("/examples")
def get_examples() -> dict:
    return EXAMPLE_QUESTIONS
