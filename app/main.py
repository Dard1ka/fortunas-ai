from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    ask, auth, briefing, customer, dpa, health, ingest, report, scan, upload, voice, whatsapp,
)
from app.core.config import get_settings
from app.core.scheduler import start_scheduler, stop_scheduler
from app.db import init_db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("fortunas")


def _run_daily_briefing_job() -> None:
    # Multi-tenant: briefing terjadwal per-tenant belum diimplementasi.
    # Tiap tenant pakai POST /report/daily/run (on-demand) lewat token-nya.
    # Scheduler briefing dimatikan via BRIEFING_SCHEDULER_ENABLED=false.
    log.info("Scheduled briefing dilewati (multi-tenant: pakai /report/daily/run per tenant).")


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
    init_db()  # pastikan tabel SQLite (tenants/users) ada
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
    app.include_router(auth.router)
    app.include_router(ask.router)
    app.include_router(briefing.router)
    app.include_router(dpa.router)
    app.include_router(customer.router)
    app.include_router(scan.router)
    app.include_router(ingest.router)
    app.include_router(report.router)
    app.include_router(upload.router)
    app.include_router(voice.router)
    app.include_router(whatsapp.router)

    return app


app = create_app()
