from __future__ import annotations

import os
from typing import Any

from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer


CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
COLLECTION_NAME = os.getenv("RAG_COLLECTION_NAME", "umkm_knowledge")
EMBED_MODEL = os.getenv("RAG_EMBED_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")


ANALYSIS_RULES = {
    "bundle_opportunity": {
        "preferred_doc_names": [
            "bundling_tactics",
            "inventory_management",
            "pricing_strategy",
        ],
        "preferred_categories": ["bundling", "inventory", "pricing"],
        "query_hint": "bundling cross sell produk pelengkap sering dibeli bersama paket hemat jual bareng",
    },
    "repeat_customer": {
        "preferred_doc_names": [
            "repeat_customer_tactics",
            "customer_retention",
        ],
        "preferred_categories": ["retention"],
        "query_hint": "pelanggan loyal repeat customer retention follow up pembelian ulang pelanggan tetap",
    },
    "high_value_customer": {
        "preferred_doc_names": [
            "customer_retention",
            "pricing_strategy",
        ],
        "preferred_categories": ["retention", "pricing"],
        "query_hint": "pelanggan bernilai tinggi total belanja terbesar personalisasi loyalty harga khusus",
    },
    "peak_hour": {
        "preferred_doc_names": [
            "peak_hour_marketing",
            "pricing_strategy",
        ],
        "preferred_categories": ["marketing", "pricing"],
        "query_hint": "jam ramai transaksi promosi operasional display stok checkout cepat",
    },
}


class RAGAgent:
    def __init__(self) -> None:
        self.client = PersistentClient(path=CHROMA_DB_PATH)
        self.collection = self.client.get_collection(name=COLLECTION_NAME)
        self.embedder = SentenceTransformer(
            EMBED_MODEL,
            local_files_only=True,
        )

    def count(self) -> int:
        return self.collection.count()

    def _normalize(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip().lower()

    def _build_query(self, query: str, mapped_analysis: str | None) -> str:
        if not mapped_analysis:
            return query

        rules = ANALYSIS_RULES.get(mapped_analysis, {})
        hint = rules.get("query_hint", "").strip()
        if not hint:
            return query

        return f"{query}\n\nKonteks bisnis: {hint}"

    def _embed_query(self, text: str) -> list[float]:
        embedding = self.embedder.encode(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return embedding.tolist()

    def _score_result(self, metadata: dict[str, Any], mapped_analysis: str | None) -> int:
        if not mapped_analysis:
            return 0

        rules = ANALYSIS_RULES.get(mapped_analysis, {})
        preferred_doc_names = [self._normalize(x) for x in rules.get("preferred_doc_names", [])]
        preferred_categories = [self._normalize(x) for x in rules.get("preferred_categories", [])]

        doc_name = self._normalize(metadata.get("doc_name"))
        category = self._normalize(metadata.get("category"))
        tags = self._normalize(metadata.get("tags"))
        section = self._normalize(metadata.get("section"))
        title = self._normalize(metadata.get("title"))

        score = 0

        if doc_name in preferred_doc_names:
            score += 8

        if category in preferred_categories:
            score += 5

        for item in preferred_doc_names + preferred_categories:
            if item and item in tags:
                score += 2
            if item and item in section:
                score += 1
            if item and item in title:
                score += 1

        # Stronger per-analysis boosts
        if mapped_analysis == "bundle_opportunity":
            if doc_name == "bundling_tactics":
                score += 6
            elif doc_name == "inventory_management":
                score += 2
            elif doc_name == "pricing_strategy":
                score += 1

        elif mapped_analysis == "repeat_customer":
            if doc_name == "repeat_customer_tactics":
                score += 6
            elif doc_name == "customer_retention":
                score += 3

        elif mapped_analysis == "high_value_customer":
            if doc_name == "customer_retention":
                score += 4
            elif doc_name == "pricing_strategy":
                score += 3

        elif mapped_analysis == "peak_hour":
            if doc_name == "peak_hour_marketing":
                score += 6
            elif doc_name == "pricing_strategy":
                score += 2

        if mapped_analysis in {"repeat_customer", "peak_hour", "bundle_opportunity"} and doc_name == "seasonal_indonesia":
            score -= 3

        return score

    def _query_collection(
        self,
        query: str,
        mapped_analysis: str | None,
        n_results: int,
    ) -> list[dict[str, Any]]:
        expanded_query = self._build_query(query, mapped_analysis)
        query_embedding = self._embed_query(expanded_query)

        raw = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=max(n_results * 5, 15),
        )

        documents = raw.get("documents", [[]])[0]
        metadatas = raw.get("metadatas", [[]])[0]
        distances = raw.get("distances", [[]])[0]

        combined = []
        for i, doc in enumerate(documents):
            metadata = metadatas[i] if i < len(metadatas) else {}
            distance = distances[i] if i < len(distances) else None
            analysis_score = self._score_result(metadata or {}, mapped_analysis)

            combined.append(
                {
                    "document": (doc or "").strip(),
                    "metadata": metadata or {},
                    "distance": distance,
                    "analysis_score": analysis_score,
                }
            )

        combined.sort(
            key=lambda x: (
                -x["analysis_score"],
                x["distance"] if x["distance"] is not None else 999999,
            )
        )
        return combined

    def _dedupe_docs(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen = set()
        final_items = []

        for item in items:
            doc = item["document"].strip()
            if not doc:
                continue

            signature = (
                self._normalize(item["metadata"].get("source")),
                self._normalize(item["metadata"].get("section")),
                doc[:120],
            )

            if signature in seen:
                continue

            seen.add(signature)
            final_items.append(item)

        return final_items

    def retrieve(
        self,
        query: str,
        mapped_analysis: str | None = None,
        n_results: int = 4,
    ) -> list[str]:
        ranked = self._query_collection(query, mapped_analysis, n_results)
        ranked = self._dedupe_docs(ranked)

        if not mapped_analysis:
            return [x["document"] for x in ranked[:n_results]]

        rules = ANALYSIS_RULES.get(mapped_analysis, {})
        preferred_doc_names = {
            self._normalize(x) for x in rules.get("preferred_doc_names", [])
        }
        preferred_categories = {
            self._normalize(x) for x in rules.get("preferred_categories", [])
        }

        exact_doc_matches = []
        category_matches = []
        fallback_matches = []

        for item in ranked:
            metadata = item["metadata"]
            doc_name = self._normalize(metadata.get("doc_name"))
            category = self._normalize(metadata.get("category"))

            if doc_name in preferred_doc_names:
                exact_doc_matches.append(item)
            elif category in preferred_categories:
                category_matches.append(item)
            else:
                fallback_matches.append(item)

        ordered = exact_doc_matches + category_matches + fallback_matches

        final_docs = []
        for item in ordered:
            final_docs.append(item["document"])
            if len(final_docs) >= n_results:
                break

        return final_docs

    def retrieve_debug(
        self,
        query: str,
        mapped_analysis: str | None = None,
        n_results: int = 4,
    ) -> list[dict[str, Any]]:
        ranked = self._query_collection(query, mapped_analysis, n_results)
        ranked = self._dedupe_docs(ranked)
        return ranked[:n_results]