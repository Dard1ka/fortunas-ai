from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.agents.insight_agent import InsightAgent
from app.agents.rag_agent import RAGAgent
from app.core.deps import get_insight_agent, get_rag_agent
from app.schemas import BriefingResponse, BriefingSection
from app.services.pipeline import (
    build_deterministic_executive_summary,
    enabled_analyses,
    run_briefing_section,
    run_full_briefing,
)

router = APIRouter(tags=["briefing"])


@router.get("/briefing", response_model=BriefingResponse)
def auto_briefing(
    insight_agent: InsightAgent = Depends(get_insight_agent),
    rag_agent: RAGAgent | None = Depends(get_rag_agent),
) -> BriefingResponse:
    result = run_full_briefing(insight_agent=insight_agent, rag_agent=rag_agent)
    sections = [BriefingSection(**s) for s in result["sections"]]

    return BriefingResponse(
        status=result["status"],
        message=result["message"],
        executive_summary=result["executive_summary"],
        sections=sections,
        agent_trace=result["agent_trace"],
    )


@router.get("/briefing/stream")
def briefing_stream(
    insight_agent: InsightAgent = Depends(get_insight_agent),
    rag_agent: RAGAgent | None = Depends(get_rag_agent),
) -> StreamingResponse:
    def event_generator():
        analyses = enabled_analyses()
        total = len(analyses)
        completed_sections: list[dict] = []

        for idx, (analysis_key, config) in enumerate(analyses):
            yield (
                f"data: {json.dumps({'event': 'step', 'index': idx, 'total': total, 'analysis': analysis_key, 'label': config['label'], 'phase': 'query'})}\n\n"
            )

            section, _section_trace = run_briefing_section(
                analysis_key=analysis_key,
                analysis_config=config,
                insight_agent=insight_agent,
                rag_agent=rag_agent,
            )

            if section["status"] == "success":
                yield (
                    f"data: {json.dumps({'event': 'step', 'index': idx, 'total': total, 'analysis': analysis_key, 'label': config['label'], 'phase': 'insight', 'row_count': section['row_count']})}\n\n"
                )

            yield f"data: {json.dumps({'event': 'section', 'index': idx, 'section': section})}\n\n"
            completed_sections.append(section)

        successful = [s for s in completed_sections if s["status"] == "success"]
        executive_summary = build_deterministic_executive_summary(successful)

        yield (
            f"data: {json.dumps({'event': 'done', 'executive_summary': executive_summary, 'total_success': len(successful), 'total': len(completed_sections)})}\n\n"
        )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
