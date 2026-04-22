from __future__ import annotations

from fastapi import APIRouter, Depends

from app.agents.insight_agent import InsightAgent
from app.agents.rag_agent import RAGAgent
from app.analysis_registry import ANALYSIS_REGISTRY
from app.core.deps import get_insight_agent, get_rag_agent
from app.intent_mapper import map_question_to_analysis
from app.schemas import AskRequest, AskResponse, LLMOutput
from app.services.pipeline import run_ask

router = APIRouter(tags=["ask"])


@router.post("/route")
def route_only(payload: AskRequest) -> dict:
    mapped_analysis = map_question_to_analysis(payload.question)
    return {
        "question": payload.question,
        "mapped_analysis": mapped_analysis,
        "supported": mapped_analysis in ANALYSIS_REGISTRY,
    }


@router.post("/ask", response_model=AskResponse)
def ask_question(
    payload: AskRequest,
    insight_agent: InsightAgent = Depends(get_insight_agent),
    rag_agent: RAGAgent | None = Depends(get_rag_agent),
) -> AskResponse:
    result = run_ask(
        question=payload.question,
        insight_agent=insight_agent,
        rag_agent=rag_agent,
    )

    llm_payload = result["llm_output"]
    llm_output = LLMOutput(**llm_payload) if llm_payload else None

    return AskResponse(
        question=payload.question,
        mapped_analysis=result["mapped_analysis"],
        status=result["status"],
        message=result["message"],
        agent_trace=result["agent_trace"],
        rows=result["rows"],
        llm_output=llm_output,
    )
