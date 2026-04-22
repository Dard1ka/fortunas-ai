from __future__ import annotations

from typing import Any

from app.agents.insight_agent import InsightAgent
from app.agents.rag_agent import RAGAgent
from app.analysis_registry import ANALYSIS_REGISTRY
from app.bigquery_service import run_query
from app.intent_mapper import map_question_to_analysis
from app.queries import QUERY_MAP


def resolve_analysis(question: str) -> tuple[dict | None, dict | None]:
    mapped_analysis = map_question_to_analysis(question)

    if mapped_analysis == "unknown":
        return None, {
            "mapped_analysis": "unknown",
            "status": "failed",
            "message": (
                "Pertanyaan belum dikenali. Coba tanyakan tentang pelanggan loyal, "
                "jam transaksi paling ramai, pelanggan paling bernilai, atau produk yang sering dibeli bersama."
            ),
            "trace_tail": ["Intent mapping failed"],
        }

    analysis_config = ANALYSIS_REGISTRY.get(mapped_analysis)
    if not analysis_config:
        return None, {
            "mapped_analysis": mapped_analysis,
            "status": "failed",
            "message": f"Analisis '{mapped_analysis}' belum terdaftar di ANALYSIS_REGISTRY.",
            "trace_tail": ["Analysis registry lookup failed"],
        }

    if not analysis_config.get("enabled", False):
        return None, {
            "mapped_analysis": mapped_analysis,
            "status": "failed",
            "message": f"Analisis '{mapped_analysis}' saat ini dinonaktifkan.",
            "trace_tail": ["Analysis is disabled"],
        }

    return {
        "mapped_analysis": mapped_analysis,
        "analysis_config": analysis_config,
    }, None


def execute_analysis(mapped_analysis: str) -> tuple[list[dict] | None, str | None]:
    sql = QUERY_MAP.get(mapped_analysis)
    if not sql:
        return None, f"Query untuk analisis '{mapped_analysis}' belum tersedia."

    rows = run_query(sql)
    return rows, None


def extract_rag_sources(
    rag_agent: RAGAgent | None,
    question: str,
    analysis_key: str,
    n_results: int = 4,
) -> list[str]:
    if not rag_agent:
        return []

    try:
        debug_items = rag_agent.retrieve_debug(
            query=question,
            mapped_analysis=analysis_key,
            n_results=n_results,
        )
    except Exception:
        return []

    seen: set[str] = set()
    ordered_sources: list[str] = []

    for item in debug_items:
        metadata = item.get("metadata") or {}
        doc_name = metadata.get("doc_name") or metadata.get("source")
        if not doc_name:
            continue
        label = _format_source_label(str(doc_name))
        if label in seen:
            continue
        seen.add(label)
        ordered_sources.append(label)

    return ordered_sources


def _format_source_label(doc_name: str) -> str:
    base = doc_name.replace(".md", "").strip()
    if not base:
        return doc_name
    words = base.replace("_", " ").replace("-", " ").split()
    return " ".join(word.capitalize() for word in words)


def run_ask(
    question: str,
    insight_agent: InsightAgent,
    rag_agent: RAGAgent | None,
) -> dict[str, Any]:
    resolved, error = resolve_analysis(question)
    if error:
        return {
            "status": error["status"],
            "mapped_analysis": error["mapped_analysis"],
            "message": error["message"],
            "agent_trace": [f"Question received: {question}", *error["trace_tail"]],
            "rows": [],
            "llm_output": None,
        }

    mapped_analysis = resolved["mapped_analysis"]
    analysis_config = resolved["analysis_config"]

    trace: list[str] = [
        f"Question received: {question}",
        f"Mapped analysis: {mapped_analysis}",
    ]

    try:
        rows, query_error = execute_analysis(mapped_analysis)
    except Exception as exc:
        trace.append("BigQuery execution failed")
        return {
            "status": "failed",
            "mapped_analysis": mapped_analysis,
            "message": f"Gagal menjalankan query BigQuery: {exc}",
            "agent_trace": trace,
            "rows": [],
            "llm_output": None,
        }

    if query_error:
        trace.append("SQL query lookup failed")
        return {
            "status": "failed",
            "mapped_analysis": mapped_analysis,
            "message": query_error,
            "agent_trace": trace,
            "rows": [],
            "llm_output": None,
        }

    trace.append("SQL query loaded successfully")

    if not rows:
        trace.append("BigQuery returned 0 rows")
        return {
            "status": "success",
            "mapped_analysis": mapped_analysis,
            "message": (
                f"Analisis '{analysis_config['label']}' berhasil dijalankan, "
                "tetapi tidak ada data yang cocok."
            ),
            "agent_trace": trace,
            "rows": [],
            "llm_output": None,
        }

    trace.append(f"BigQuery returned {len(rows)} rows")

    try:
        insight_result = insight_agent.generate(
            question=question,
            analysis_key=mapped_analysis,
            bq_rows=rows,
        )
    except Exception as exc:
        trace.append("LLM insight generation failed")
        return {
            "status": "partial_success",
            "mapped_analysis": mapped_analysis,
            "message": f"Query BigQuery berhasil, tetapi LLM gagal memberi insight: {exc}",
            "agent_trace": trace,
            "rows": rows,
            "llm_output": None,
        }

    llm_result = insight_result["llm_output"]
    rag_context = insight_result["rag_context"]

    if rag_context:
        trace.append(f"RAG returned {len(rag_context)} context chunks")
    else:
        trace.append("RAG context unavailable or empty")

    rag_sources = extract_rag_sources(rag_agent, question, mapped_analysis)
    if rag_sources:
        trace.append(f"RAG sources: {', '.join(rag_sources)}")

    trace.append(f"Data confidence: {llm_result['data_confidence']}")
    trace.append("LLM insight generated successfully")

    llm_output_payload = {
        "summary": llm_result["summary"],
        "top_findings": llm_result["top_findings"],
        "recommendation": llm_result["recommendation"],
        "data_confidence": llm_result["data_confidence"],
        "rag_sources": rag_sources,
    }

    return {
        "status": "success",
        "mapped_analysis": mapped_analysis,
        "message": (
            f"Pertanyaan dipetakan ke analisis '{analysis_config['label']}', "
            "query berhasil dijalankan, dan insight berhasil dibuat."
        ),
        "agent_trace": trace,
        "rows": rows,
        "llm_output": llm_output_payload,
    }


def run_briefing_section(
    analysis_key: str,
    analysis_config: dict,
    insight_agent: InsightAgent,
    rag_agent: RAGAgent | None,
) -> tuple[dict[str, Any], list[str]]:
    trace_lines: list[str] = [f"Running analysis: {analysis_config['label']}"]

    try:
        rows, query_error = execute_analysis(analysis_key)
    except Exception as exc:
        trace_lines.append(f"{analysis_config['label']}: BigQuery execution failed")
        return {
            "analysis_type": analysis_key,
            "label": analysis_config["label"],
            "status": "error",
            "summary": f"Gagal: {exc}",
            "top_findings": [],
            "recommendation": [],
            "row_count": 0,
            "data_confidence": "low",
            "rag_sources": [],
        }, trace_lines

    if query_error or not rows:
        trace_lines.append(f"{analysis_config['label']}: no data")
        return {
            "analysis_type": analysis_key,
            "label": analysis_config["label"],
            "status": "no_data",
            "summary": "Tidak ada data yang tersedia untuk analisis ini.",
            "top_findings": [],
            "recommendation": [],
            "row_count": 0,
            "data_confidence": "low",
            "rag_sources": [],
        }, trace_lines

    trace_lines.append(
        f"{analysis_config['label']}: BigQuery returned {len(rows)} rows"
    )

    try:
        insight_result = insight_agent.generate(
            question=f"Berikan analisis {analysis_config['label']}",
            analysis_key=analysis_key,
            bq_rows=rows,
        )
    except Exception as exc:
        trace_lines.append(
            f"{analysis_config['label']}: insight generation failed — {exc}"
        )
        return {
            "analysis_type": analysis_key,
            "label": analysis_config["label"],
            "status": "error",
            "summary": f"Gagal: {exc}",
            "top_findings": [],
            "recommendation": [],
            "row_count": len(rows),
            "data_confidence": "low",
            "rag_sources": [],
        }, trace_lines

    llm_result = insight_result["llm_output"]
    rag_context = insight_result["rag_context"]
    rag_sources = extract_rag_sources(
        rag_agent,
        question=f"Berikan analisis {analysis_config['label']}",
        analysis_key=analysis_key,
    )

    if rag_context:
        trace_lines.append(
            f"{analysis_config['label']}: RAG returned {len(rag_context)} chunks"
        )
    else:
        trace_lines.append(f"{analysis_config['label']}: no RAG context")

    trace_lines.append(
        f"{analysis_config['label']}: data confidence {llm_result['data_confidence']}"
    )
    trace_lines.append(f"{analysis_config['label']}: insight generated")

    return {
        "analysis_type": analysis_key,
        "label": analysis_config["label"],
        "status": "success",
        "summary": llm_result["summary"],
        "top_findings": llm_result["top_findings"],
        "recommendation": llm_result["recommendation"],
        "row_count": len(rows),
        "data_confidence": llm_result["data_confidence"],
        "rag_sources": rag_sources,
    }, trace_lines


def build_deterministic_executive_summary(sections: list[dict]) -> str:
    successful_sections = [s for s in sections if s.get("status") == "success"]
    if not successful_sections:
        return ""

    by_type = {s.get("analysis_type"): s for s in successful_sections}

    sentences: list[str] = []
    for key in (
        "repeat_customer",
        "high_value_customer",
        "peak_hour",
        "bundle_opportunity",
    ):
        section = by_type.get(key)
        if not section:
            continue
        summary = (section.get("summary") or "").strip()
        if summary:
            sentences.append(summary)

    return " ".join(sentences)


def enabled_analyses() -> list[tuple[str, dict]]:
    return [
        (key, config)
        for key, config in ANALYSIS_REGISTRY.items()
        if config.get("enabled", False)
    ]


def run_full_briefing(
    insight_agent: InsightAgent,
    rag_agent: RAGAgent | None,
) -> dict[str, Any]:
    trace: list[str] = ["Auto-briefing started"]
    sections: list[dict] = []

    for analysis_key, config in enabled_analyses():
        section, section_trace = run_briefing_section(
            analysis_key=analysis_key,
            analysis_config=config,
            insight_agent=insight_agent,
            rag_agent=rag_agent,
        )
        sections.append(section)
        trace.extend(section_trace)

    successful = [s for s in sections if s["status"] == "success"]
    executive_summary = build_deterministic_executive_summary(successful)

    if successful:
        trace.append("Executive summary generated deterministically")

    return {
        "status": "success" if successful else "failed",
        "message": f"Briefing selesai: {len(successful)}/{len(sections)} analisis berhasil.",
        "executive_summary": executive_summary,
        "sections": sections,
        "agent_trace": trace,
    }
