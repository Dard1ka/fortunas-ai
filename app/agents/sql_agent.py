import os
import re
from typing import Optional

from app.queries import NAMED_QUERIES
from app.bigquery_service import run_query_safe, dry_run
from app.sql_guards import validate_adhoc_sql
from app.schema_context import get_schema_context


class SQLAgentError(Exception):
    """Base error untuk SQLAgent."""


class SQLAgent:
    def __init__(
        self,
        max_gb_named: float = 2.0,
        max_gb_adhoc: float = 1.0,
        adhoc_limit: int = 1000,
    ):
        self.max_gb_named = max_gb_named
        self.max_gb_adhoc = max_gb_adhoc
        self.adhoc_limit = adhoc_limit

    # ---------- Named query path ----------
    def run_named_query(self, analysis_key: str) -> dict:
        meta = NAMED_QUERIES.get(analysis_key)
        if not meta:
            raise SQLAgentError(
                f"Named query '{analysis_key}' tidak ditemukan di NAMED_QUERIES."
            )

        sql = meta["sql"]
        # Cost guard untuk named query (terutama bundle_opportunity)
        try:
            result = run_query_safe(sql, max_gb=self.max_gb_named)
        except ValueError as e:
            raise SQLAgentError(f"Named query '{analysis_key}' ditolak: {e}") from e

        return {
            "type": "named",
            "analysis_key": analysis_key,
            "cost_tier": meta.get("cost_tier", "unknown"),
            **result,
        }

    # ---------- Adhoc query path ----------
    def run_adhoc_query(
        self,
        nl_question: str,
        llm_callable: Optional[callable] = None,
    ) -> dict:
        """
        nl_question: pertanyaan natural language dari user
        llm_callable: fungsi yang menerima prompt string dan return string SQL.
                      Default: pakai _generate_sql_with_ollama internal.
        """
        if not nl_question or not nl_question.strip():
            raise SQLAgentError("Pertanyaan kosong.")

        # 1. Generate SQL dari LLM (HANYA schema, tanpa raw data)
        prompt = self._build_sql_prompt(nl_question)
        generator = llm_callable or self._generate_sql_with_ollama
        raw_sql = generator(prompt)
        sql = self._extract_sql(raw_sql)

        # 2. Guardrails: SELECT-only + force LIMIT
        try:
            safe_sql = validate_adhoc_sql(sql, default_limit=self.adhoc_limit)
        except ValueError as e:
            raise SQLAgentError(f"Adhoc SQL ditolak guard: {e}") from e

        # 3. Dry run + cost check + execute
        try:
            result = run_query_safe(safe_sql, max_gb=self.max_gb_adhoc)
        except ValueError as e:
            raise SQLAgentError(f"Adhoc SQL gagal cost check: {e}") from e

        return {
            "type": "adhoc",
            "nl_question": nl_question,
            "generated_sql": safe_sql,
            **result,
        }

    # ---------- Helpers ----------
    def _build_sql_prompt(self, nl_question: str) -> str:
        return f"""You are a BigQuery SQL expert. Generate ONE BigQuery Standard SQL query that answers the user's question.

{get_schema_context()}

Rules:
- Only output SQL, no explanation, no markdown fences.
- Must be SELECT only. No INSERT/UPDATE/DELETE/DDL.
- Always include LIMIT (max {self.adhoc_limit}).
- Always filter quantity > 0 AND price > 0.
- Use the table reference exactly as: `{os.getenv("BIGQUERY_PROJECT_ID", "fortunasai")}.{os.getenv("BIGQUERY_DATASET", "fortunas_ai")}.{os.getenv("BIGQUERY_TABLE", "online_retail")}`

User question: {nl_question}

SQL:"""

    def _extract_sql(self, raw: str) -> str:
        if not raw:
            raise SQLAgentError("LLM mengembalikan SQL kosong.")
        cleaned = raw.strip()

        # 1. Coba ambil dari markdown fence dulu
        fence_match = re.search(r"```(?:sql)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
        if fence_match:
            cleaned = fence_match.group(1).strip()
        else:
            # 2. Tidak ada fence — cari posisi keyword SELECT atau WITH pertama
            #    (case insensitive, harus standalone word)
            sql_start = re.search(r"\b(SELECT|WITH)\b", cleaned, re.IGNORECASE)
            if sql_start:
                cleaned = cleaned[sql_start.start():].strip()

        # 3. Buang trailing prose setelah SQL selesai (kalau ada)
        #    Heuristik sederhana: potong di newline kosong ganda
        cleaned = cleaned.split("\n\n")[0].strip()

        if not cleaned:
            raise SQLAgentError(f"SQL kosong setelah extraction. Raw: {raw[:200]}")
        return cleaned

    def _strip_think_block(self, text: str) -> str:
        """Qwen3 sering output <think>...</think> sebelum jawaban asli. Buang."""
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    def _generate_sql_with_ollama(self, prompt: str) -> str:
        import requests

        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        model = os.getenv("OLLAMA_SQL_MODEL", os.getenv("OLLAMA_MODEL", "qwen3:8b"))

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "think": False,  # Disable reasoning mode (Ollama parameter resmi)
            "options": {
                "temperature": 0.1,
                "num_predict": 1500,
            },
        }

        try:
            response = requests.post(f"{base_url}/api/generate", json=payload, timeout=300)
            response.raise_for_status()
        except requests.RequestException as e:
            raise SQLAgentError(f"Gagal call Ollama: {e}") from e

        data = response.json()

        if data.get("error"):
            raise SQLAgentError(f"Ollama error: {data['error']}")

        # Primary: ambil dari "response"
        raw = (data.get("response") or "").strip()

        # Fallback: kalau kosong, ambil dari "thinking" (Qwen3 di Ollama baru)
        if not raw:
            raw = (data.get("thinking") or "").strip()

        if not raw:
            raise SQLAgentError(
                f"Ollama return response & thinking kosong. Payload keys: {list(data.keys())}"
            )

        # Strip <think> block kalau ada (jaga-jaga untuk model lain)
        return self._strip_think_block(raw)