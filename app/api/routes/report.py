from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.agents.insight_agent import InsightAgent
from app.agents.rag_agent import RAGAgent
from app.core.config import get_settings
from app.core.deps import get_insight_agent, get_rag_agent
from app.schemas import DailyReportEntry, DailyReportResponse
from app.services import report_store
from app.services.pipeline import run_full_briefing

router = APIRouter(tags=["report"])


@router.get("/report/daily", response_model=DailyReportResponse)
def get_daily_report() -> DailyReportResponse:
    settings = get_settings()
    latest = report_store.get_latest(settings.daily_report_path)
    history = report_store.list_history(
        settings.daily_report_path,
        limit=settings.daily_report_history_days,
    )

    if not latest:
        return DailyReportResponse(
            status="empty",
            message="Belum ada briefing harian tersimpan. Jalankan POST /report/daily/run atau /briefing terlebih dahulu.",
            latest=None,
            history=[],
        )

    return DailyReportResponse(
        status="success",
        message=f"Briefing harian terakhir: {latest.get('date', '')} ({latest.get('generated_at', '')}).",
        latest=DailyReportEntry(**latest),
        history=[DailyReportEntry(**entry) for entry in history],
    )


@router.post("/report/daily/run", response_model=DailyReportResponse)
def run_and_save_daily_report(
    insight_agent: InsightAgent = Depends(get_insight_agent),
    rag_agent: RAGAgent | None = Depends(get_rag_agent),
) -> DailyReportResponse:
    settings = get_settings()
    briefing = run_full_briefing(insight_agent=insight_agent, rag_agent=rag_agent)

    entry = report_store.save_report(
        path=settings.daily_report_path,
        executive_summary=briefing["executive_summary"],
        sections=briefing["sections"],
    )
    history = report_store.list_history(
        settings.daily_report_path,
        limit=settings.daily_report_history_days,
    )

    return DailyReportResponse(
        status="success",
        message=f"Briefing harian tersimpan untuk {entry.get('date', '')}.",
        latest=DailyReportEntry(**entry),
        history=[DailyReportEntry(**e) for e in history],
    )


@router.delete("/report/daily", response_model=DailyReportResponse)
def delete_daily_report_entry(
    generated_at: str | None = Query(
        default=None,
        description="generated_at dari entry yang ingin dihapus. Kosongkan + all=true untuk hapus semua.",
    ),
    all: bool = Query(default=False, description="Set true untuk hapus seluruh history."),
) -> DailyReportResponse:
    settings = get_settings()

    if all:
        removed = report_store.clear_all(settings.daily_report_path)
        return DailyReportResponse(
            status="success" if removed > 0 else "empty",
            message=(
                f"Berhasil menghapus {removed} entry history."
                if removed > 0
                else "Tidak ada history untuk dihapus."
            ),
            latest=None,
            history=[],
        )

    if not generated_at:
        raise HTTPException(
            status_code=400,
            detail="Parameter generated_at wajib diisi, atau gunakan all=true untuk hapus semua.",
        )

    deleted = report_store.delete_report(settings.daily_report_path, generated_at)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Entry dengan generated_at={generated_at} tidak ditemukan.",
        )

    latest = report_store.get_latest(settings.daily_report_path)
    history = report_store.list_history(
        settings.daily_report_path,
        limit=settings.daily_report_history_days,
    )

    return DailyReportResponse(
        status="success",
        message=f"Entry {generated_at} berhasil dihapus.",
        latest=DailyReportEntry(**latest) if latest else None,
        history=[DailyReportEntry(**e) for e in history],
    )
