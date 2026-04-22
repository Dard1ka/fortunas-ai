from __future__ import annotations

from functools import lru_cache

from app.agents.insight_agent import InsightAgent
from app.agents.rag_agent import RAGAgent


_rag_init_error: str = ""


@lru_cache(maxsize=1)
def get_rag_agent() -> RAGAgent | None:
    global _rag_init_error
    try:
        return RAGAgent()
    except Exception as exc:
        _rag_init_error = str(exc)
        return None


@lru_cache(maxsize=1)
def get_insight_agent() -> InsightAgent:
    return InsightAgent(rag_agent=get_rag_agent())


def rag_init_error() -> str:
    get_rag_agent()
    return _rag_init_error


def rag_enabled() -> bool:
    return get_rag_agent() is not None
