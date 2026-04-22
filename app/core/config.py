from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    app_name: str = "Fortunas AI Backend"
    app_version: str = "1.0.0"

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    bigquery_project_id: str = os.getenv("BIGQUERY_PROJECT_ID", "fortunasai")
    bigquery_dataset: str = os.getenv("BIGQUERY_DATASET", "fortunas_ai")
    bigquery_table: str = os.getenv("BIGQUERY_TABLE", "online_retail")

    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3:8b")

    chroma_db_path: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    rag_collection_name: str = os.getenv("RAG_COLLECTION_NAME", "umkm_knowledge")
    rag_default_n_results: int = int(os.getenv("RAG_DEFAULT_N_RESULTS", "4"))

    briefing_cron_hour: int = int(os.getenv("BRIEFING_CRON_HOUR", "6"))
    briefing_cron_minute: int = int(os.getenv("BRIEFING_CRON_MINUTE", "0"))
    briefing_timezone: str = os.getenv("BRIEFING_TIMEZONE", "Asia/Jakarta")
    briefing_scheduler_enabled: bool = (
        os.getenv("BRIEFING_SCHEDULER_ENABLED", "true").lower() == "true"
    )

    daily_report_path: str = os.getenv(
        "DAILY_REPORT_PATH", "./app/data/daily_reports.json"
    )
    daily_report_history_days: int = int(os.getenv("DAILY_REPORT_HISTORY_DAYS", "7"))

    knowledge_docs_dir: str = os.getenv(
        "KNOWLEDGE_DOCS_DIR", "./app/knowledge/umkm_docs"
    )

    # WhatsApp retry scheduler — interval retry untuk baris Sheet ber-status failed/pending
    wa_retry_enabled: bool = (
        os.getenv("WA_RETRY_ENABLED", "false").lower() == "true"
    )
    wa_retry_interval_minutes: int = int(os.getenv("WA_RETRY_INTERVAL_MINUTES", "15"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
