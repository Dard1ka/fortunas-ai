from __future__ import annotations

import json
import os
import tempfile
import threading
from datetime import datetime, timezone
from typing import Any

_lock = threading.Lock()


def _now_jakarta_iso() -> str:
    from zoneinfo import ZoneInfo

    try:
        tz = ZoneInfo("Asia/Jakarta")
    except Exception:
        tz = timezone.utc
    return datetime.now(tz).isoformat(timespec="seconds")


def _today_jakarta_date() -> str:
    from zoneinfo import ZoneInfo

    try:
        tz = ZoneInfo("Asia/Jakarta")
    except Exception:
        tz = timezone.utc
    return datetime.now(tz).strftime("%Y-%m-%d")


def _ensure_parent(path: str) -> None:
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def load_all(path: str) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        return []
    return []


def save_report(
    path: str,
    executive_summary: str,
    sections: list[dict[str, Any]],
    max_history: int = 30,
) -> dict[str, Any]:
    entry = {
        "generated_at": _now_jakarta_iso(),
        "date": _today_jakarta_date(),
        "executive_summary": executive_summary,
        "sections": sections,
    }

    with _lock:
        entries = load_all(path)
        entries = [e for e in entries if e.get("date") != entry["date"]]
        entries.append(entry)
        entries.sort(key=lambda e: e.get("generated_at", ""), reverse=True)
        entries = entries[:max_history]

        _ensure_parent(path)
        dir_name = os.path.dirname(path) or "."
        fd, tmp_path = tempfile.mkstemp(
            prefix=".daily_reports_", suffix=".json", dir=dir_name
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(entries, fh, ensure_ascii=False, indent=2)
            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise

    return entry


def get_latest(path: str) -> dict[str, Any] | None:
    entries = load_all(path)
    if not entries:
        return None
    entries.sort(key=lambda e: e.get("generated_at", ""), reverse=True)
    return entries[0]


def list_history(path: str, limit: int = 7) -> list[dict[str, Any]]:
    entries = load_all(path)
    entries.sort(key=lambda e: e.get("generated_at", ""), reverse=True)
    return entries[:limit]


def delete_report(path: str, generated_at: str) -> bool:
    """Hapus satu entry berdasarkan generated_at. Return True jika terhapus."""
    with _lock:
        entries = load_all(path)
        new_entries = [e for e in entries if e.get("generated_at") != generated_at]

        if len(new_entries) == len(entries):
            return False

        _ensure_parent(path)
        dir_name = os.path.dirname(path) or "."
        fd, tmp_path = tempfile.mkstemp(
            prefix=".daily_reports_", suffix=".json", dir=dir_name
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(new_entries, fh, ensure_ascii=False, indent=2)
            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise

    return True


def clear_all(path: str) -> int:
    """Hapus semua entry. Return jumlah yang dihapus."""
    with _lock:
        entries = load_all(path)
        count = len(entries)
        if count == 0:
            return 0
        _ensure_parent(path)
        dir_name = os.path.dirname(path) or "."
        fd, tmp_path = tempfile.mkstemp(
            prefix=".daily_reports_", suffix=".json", dir=dir_name
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump([], fh, ensure_ascii=False, indent=2)
            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise
    return count
