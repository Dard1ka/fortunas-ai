from __future__ import annotations

from typing import Any

from app.prompt_builder import build_llm_prompt, build_llm_prompt_with_rag
from app.llm_service import call_ollama


class InsightAgent:
    def __init__(self, rag_agent=None, default_rag_results: int = 4) -> None:
        self.rag_agent = rag_agent
        self.default_rag_results = default_rag_results

    def compute_data_confidence(self, rows: list[dict[str, Any]]) -> str:
        row_count = len(rows)

        if row_count >= 10:
            return "high"
        if row_count >= 5:
            return "medium"
        if row_count >= 1:
            return "low"
        return "low"

    def retrieve_context(
        self,
        question: str,
        analysis_key: str,
        n_results: int | None = None,
    ) -> list[str]:
        if not self.rag_agent:
            return []

        try:
            return self.rag_agent.retrieve(
                query=question,
                mapped_analysis=analysis_key,
                n_results=n_results or self.default_rag_results,
            )
        except Exception:
            return []

    def build_prompt(
        self,
        question: str,
        analysis_key: str,
        rows: list[dict[str, Any]],
        rag_context: list[str],
    ) -> str:
        if rag_context:
            return build_llm_prompt_with_rag(
                question=question,
                mapped_analysis=analysis_key,
                rows=rows,
                rag_context=rag_context,
            )

        return build_llm_prompt(
            question=question,
            mapped_analysis=analysis_key,
            rows=rows,
        )

    def generate(
        self,
        question: str,
        analysis_key: str,
        bq_rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        rag_context = self.retrieve_context(
            question=question,
            analysis_key=analysis_key,
            n_results=self.default_rag_results,
        )

        prompt = self.build_prompt(
            question=question,
            analysis_key=analysis_key,
            rows=bq_rows,
            rag_context=rag_context,
        )

        llm_result = call_ollama(
            prompt,
            mapped_analysis=analysis_key,
            rows=bq_rows,
        )

        data_confidence = self.compute_data_confidence(bq_rows)
        llm_result["data_confidence"] = data_confidence

        return {
            "llm_output": llm_result,
            "rag_context": rag_context,
            "data_confidence": data_confidence,
        }