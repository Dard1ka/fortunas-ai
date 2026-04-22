from __future__ import annotations

import logging
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import get_settings

log = logging.getLogger("fortunas.scheduler")


_scheduler: BackgroundScheduler | None = None


def start_scheduler(
    briefing_job: Callable[[], None],
    wa_retry_job: Callable[[], None] | None = None,
) -> BackgroundScheduler | None:
    global _scheduler

    settings = get_settings()
    if not settings.briefing_scheduler_enabled:
        log.info("Briefing scheduler disabled via config.")
        return None

    if _scheduler and _scheduler.running:
        return _scheduler

    scheduler = BackgroundScheduler(timezone=settings.briefing_timezone)
    scheduler.add_job(
        briefing_job,
        trigger=CronTrigger(
            hour=settings.briefing_cron_hour,
            minute=settings.briefing_cron_minute,
            timezone=settings.briefing_timezone,
        ),
        id="daily_briefing",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    log.info(
        "Daily briefing scheduled at %02d:%02d %s",
        settings.briefing_cron_hour,
        settings.briefing_cron_minute,
        settings.briefing_timezone,
    )

    # WA retry — interval-based, off-by-default
    if wa_retry_job and settings.wa_retry_enabled:
        scheduler.add_job(
            wa_retry_job,
            trigger=IntervalTrigger(minutes=settings.wa_retry_interval_minutes),
            id="wa_retry",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        log.info(
            "WA retry job scheduled every %d minutes",
            settings.wa_retry_interval_minutes,
        )

    scheduler.start()
    _scheduler = scheduler
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None
