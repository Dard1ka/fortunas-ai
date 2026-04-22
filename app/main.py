from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import ask, briefing, health, ingest, report, upload, whatsapp
from app.core.config import get_settings
from app.core.deps import get_insight_agent, get_rag_agent
from app.core.scheduler import start_scheduler, stop_scheduler
from app.services import report_store
from app.services.pipeline import run_full_briefing

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("fortunas")


def _run_daily_briefing_job() -> None:
    settings = get_settings()
    try:
        briefing = run_full_briefing(
            insight_agent=get_insight_agent(),
            rag_agent=get_rag_agent(),
        )
        report_store.save_report(
            path=settings.daily_report_path,
            executive_summary=briefing["executive_summary"],
            sections=briefing["sections"],
        )
        log.info(
            "Daily briefing saved: %s (%d successful sections)",
            briefing["message"],
            sum(1 for s in briefing["sections"] if s.get("status") == "success"),
        )
    except Exception as exc:
        log.exception("Daily briefing job failed: %s", exc)


def _run_wa_retry_job() -> None:
    try:
        from app.services.wa_pipeline import retry_failed_rows

        summary = retry_failed_rows(max_rows=200)
        log.info(
            "WA retry tick: scanned=%d inserted=%d still_failed=%d skipped=%d",
            summary["scanned"], summary["inserted"],
            summary["still_failed"], summary["skipped_malformed"],
        )
    except Exception as exc:
        log.exception("WA retry job failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler(_run_daily_briefing_job, wa_retry_job=_run_wa_retry_job)
    try:
        yield
    finally:
        stop_scheduler()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Asisten analisis perilaku pelanggan untuk UMKM",
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(ask.router)
    app.include_router(briefing.router)
    app.include_router(ingest.router)
    app.include_router(report.router)
    app.include_router(upload.router)
    app.include_router(whatsapp.router)

    return app


app = create_app()
