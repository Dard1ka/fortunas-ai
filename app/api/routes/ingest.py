from __future__ import annotations

import importlib

from fastapi import APIRouter, HTTPException

from app.core.deps import get_rag_agent
from app.schemas import IngestResponse

router = APIRouter(tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
def trigger_ingest(reset: bool = False) -> IngestResponse:
    try:
        ingest_module = importlib.import_module("app.knowledge.ingest")
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Knowledge ingestion module tidak tersedia: {exc}",
        )

    ingest_fn = getattr(ingest_module, "ingest_docs", None)
    if not callable(ingest_fn):
        raise HTTPException(
            status_code=500,
            detail="Fungsi 'ingest_docs' tidak ditemukan di app.knowledge.ingest.",
        )

    try:
        ingest_fn(reset=reset)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingestion gagal: {exc}")

    get_rag_agent.cache_clear()
    agent = get_rag_agent()
    chunk_count = agent.count() if agent else 0

    return IngestResponse(
        status="success",
        message="Ingestion selesai. Collection sudah di-reload.",
        ingested_chunks=chunk_count,
        docs=[],
    )
