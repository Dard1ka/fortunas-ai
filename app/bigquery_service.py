import os
import threading
from typing import Optional
from dotenv import load_dotenv
from google.cloud import bigquery
from google.api_core import exceptions as gcp_exceptions

load_dotenv()

# ---------- Singleton client ----------
_client_lock = threading.Lock()
_client: Optional[bigquery.Client] = None


def get_bigquery_client() -> bigquery.Client:
    """Lazy singleton — client dibuat sekali, dipakai ulang antar request."""
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                if not credentials_path:
                    raise ValueError(
                        "GOOGLE_APPLICATION_CREDENTIALS belum di-set di file .env"
                    )
                _client = bigquery.Client.from_service_account_json(credentials_path)
    return _client


# ---------- Core execution ----------
def run_query(sql: str) -> list:
    """Backward compatible — dipakai main.py existing. Tidak diubah signature-nya."""
    client = get_bigquery_client()
    try:
        query_job = client.query(sql)
        results = query_job.result()
        return [dict(row.items()) for row in results]
    except gcp_exceptions.BadRequest as e:
        raise ValueError(f"BigQuery syntax error: {e.message}") from e
    except gcp_exceptions.Forbidden as e:
        raise PermissionError(f"BigQuery permission denied: {e.message}") from e
    except gcp_exceptions.GoogleAPIError as e:
        raise RuntimeError(f"BigQuery API error: {e}") from e


# ---------- Cost guard primitives ----------
def dry_run(sql: str) -> int:
    """
    Return total bytes yang akan di-scan TANPA execute query.
    Raises ValueError kalau SQL invalid.
    """
    client = get_bigquery_client()
    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    try:
        job = client.query(sql, job_config=job_config)
        return int(job.total_bytes_processed or 0)
    except gcp_exceptions.BadRequest as e:
        raise ValueError(f"Dry run gagal — SQL invalid: {e.message}") from e


def estimate_cost_gb(sql: str) -> float:
    """Helper: convert dry_run bytes ke GB."""
    return dry_run(sql) / 1e9


def run_query_safe(sql: str, max_gb: float = 1.0) -> dict:
    """
    Eksekusi query dengan cost guard.
    Return dict dengan rows + metadata, BUKAN list (beda dengan run_query).
    """
    bytes_scanned = dry_run(sql)
    gb_scanned = bytes_scanned / 1e9

    if gb_scanned > max_gb:
        raise ValueError(
            f"Query ditolak: estimasi scan {gb_scanned:.3f} GB > batas {max_gb} GB"
        )

    rows = run_query(sql)
    return {
        "rows": rows,
        "row_count": len(rows),
        "bytes_scanned": bytes_scanned,
        "gb_scanned": round(gb_scanned, 4),
    }