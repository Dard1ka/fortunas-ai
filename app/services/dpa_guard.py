"""Guardrail DPA deterministik (pure, nol I/O).

Dipakai run_ask untuk menolak pertanyaan/jawaban yang melanggar forbidden_rules
DPA tenant SEBELUM & SESUDAH memanggil Gemini. Tidak bergantung kepatuhan LLM.
"""
from __future__ import annotations

import re


def normalize_rules(rules: list[str] | None) -> list[str]:
    """Trim + lowercase + buang kosong + dedupe (jaga urutan)."""
    out: list[str] = []
    seen: set[str] = set()
    for r in rules or []:
        v = (r or "").strip().lower()
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out


def find_violations(text: str, forbidden_rules: list[str] | None) -> list[str]:
    """Subset forbidden_rules yang muncul di `text` (word-boundary, case-insensitive)."""
    rules = normalize_rules(forbidden_rules)
    if not rules or not text:
        return []
    low = text.lower()
    return [rule for rule in rules if re.search(r"\b" + re.escape(rule) + r"\b", low)]


def check_question(question: str, forbidden_rules: list[str] | None) -> list[str]:
    return find_violations(question or "", forbidden_rules)


def check_answer(llm_output: dict | None, forbidden_rules: list[str] | None) -> list[str]:
    if not llm_output:
        return []
    parts: list[str] = [str(llm_output.get("summary") or "")]
    for key in ("top_findings", "recommendation"):
        val = llm_output.get(key) or []
        if isinstance(val, list):
            parts.extend(str(x) for x in val)
        else:
            parts.append(str(val))
    return find_violations(" \n ".join(parts), forbidden_rules)


def build_refusal(violations: list[str], tenant_name: str = "") -> str:
    topics = ", ".join(violations) if violations else "topik tertentu"
    biz = f" {tenant_name}" if tenant_name else " Anda"
    return (
        f"Maaf, sesuai aturan bisnis{biz}, topik berikut tidak bisa dibahas: {topics}. "
        "Silakan ajukan pertanyaan lain seputar data penjualan Anda."
    )
