from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "umkm_docs"
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", str(BASE_DIR.parent.parent / "chroma_db"))
COLLECTION_NAME = os.getenv("RAG_COLLECTION_NAME", "umkm_knowledge")
EMBED_MODEL = os.getenv(
    "RAG_EMBED_MODEL",
    "paraphrase-multilingual-MiniLM-L12-v2",
)

FILE_CATEGORY_MAP = {
    "pricing_strategy": "pricing",
    "bundling_tactics": "bundling",
    "customer_retention": "retention",
    "inventory_management": "inventory",
    "peak_hour_marketing": "marketing",
    "seasonal_indonesia": "seasonal",
    "repeat_customer_tactics": "retention",
}

FILE_TAG_MAP = {
    "pricing_strategy": "pricing,diskon,margin,pelanggan_bernilai,jam_ramai,bundling",
    "bundling_tactics": "bundling,cross_sell,paket_hemat,produk_pelengkap",
    "customer_retention": "retention,loyalty,pelanggan_loyal,follow_up,crm",
    "inventory_management": "inventory,stock,slow_moving,fast_moving,bundling",
    "peak_hour_marketing": "peak_hour,marketing,jam_ramai,promo,operasional",
    "seasonal_indonesia": "seasonal,indonesia,ramadan,lebaran,harbolnas,gajian",
    "repeat_customer_tactics": "repeat_customer,retention,reactivation,follow_up,loyalty",
}


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return fallback.replace("_", " ").title()


def split_sections(markdown_text: str) -> list[tuple[str, str]]:
    text = normalize_text(markdown_text)

    matches = list(re.finditer(r"^##\s+(.+)$", text, flags=re.MULTILINE))
    if not matches:
        return [("Full Document", text)]

    sections: list[tuple[str, str]] = []

    first_start = matches[0].start()
    intro = text[:first_start].strip()
    if intro:
        sections.append(("Introduction", intro))

    for i, match in enumerate(matches):
        section_title = match.group(1).strip()
        section_start = match.end()
        section_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_body = text[section_start:section_end].strip()

        if section_body:
            sections.append((section_title, section_body))

    return sections


def split_large_text(text: str, max_words: int = 220) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_words = 0

    for paragraph in paragraphs:
        para_words = len(paragraph.split())

        if current and current_words + para_words > max_words:
            chunks.append("\n\n".join(current).strip())
            current = [paragraph]
            current_words = para_words
        else:
            current.append(paragraph)
            current_words += para_words

    if current:
        chunks.append("\n\n".join(current).strip())

    return chunks


def build_chunks_from_file(file_path: Path) -> list[dict]:
    raw_text = file_path.read_text(encoding="utf-8")
    raw_text = normalize_text(raw_text)

    title = extract_title(raw_text, file_path.stem)
    category = FILE_CATEGORY_MAP.get(file_path.stem, "general")
    tags = FILE_TAG_MAP.get(file_path.stem, "umkm,bisnis,knowledge")

    sections = split_sections(raw_text)

    chunks: list[dict] = []
    chunk_idx = 0

    for section_title, section_body in sections:
        subchunks = split_large_text(section_body, max_words=220)

        if not subchunks:
            continue

        for sub_idx, subchunk in enumerate(subchunks):
            document_text = (
                f"Document: {title}\n"
                f"Category: {category}\n"
                f"Section: {section_title}\n\n"
                f"{subchunk}"
            )

            chunk_id = f"{file_path.stem}::{chunk_idx}"
            chunks.append(
                {
                    "id": chunk_id,
                    "document": document_text,
                    "metadata": {
                        "source": file_path.name,
                        "doc_name": file_path.stem,
                        "title": title,
                        "section": section_title,
                        "category": category,
                        "tags": tags,
                        "chunk_index": chunk_idx,
                        "subchunk_index": sub_idx,
                    },
                }
            )
            chunk_idx += 1

    return chunks


def get_collection(reset: bool = False):
    client = PersistentClient(path=CHROMA_DB_PATH)

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"[INFO] Existing collection '{COLLECTION_NAME}' deleted.")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "UMKM business knowledge for Fortunas RAG"},
    )
    return collection


def delete_existing_chunks_for_source(collection, source_filename: str) -> None:
    try:
        existing = collection.get(where={"source": source_filename})
        existing_ids = existing.get("ids", [])
        if existing_ids:
            collection.delete(ids=existing_ids)
            print(f"[INFO] Deleted {len(existing_ids)} old chunks from {source_filename}")
    except Exception as exc:
        print(f"[WARN] Could not delete old chunks for {source_filename}: {exc}")


def ingest_docs(reset: bool = False) -> None:
    if not DOCS_DIR.exists():
        raise FileNotFoundError(f"Docs directory not found: {DOCS_DIR}")

    md_files = sorted(DOCS_DIR.glob("*.md"))
    if not md_files:
        raise FileNotFoundError(f"No .md files found in: {DOCS_DIR}")

    collection = get_collection(reset=reset)
    embedder = SentenceTransformer(
        EMBED_MODEL,
        local_files_only=True,
    )

    total_chunks = 0

    for file_path in md_files:
        delete_existing_chunks_for_source(collection, file_path.name)

        chunks = build_chunks_from_file(file_path)
        if not chunks:
            print(f"[WARN] No chunks created for {file_path.name}")
            continue

        ids = [c["id"] for c in chunks]
        documents = [c["document"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        embeddings = embedder.encode(
            documents,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        ).tolist()

        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        total_chunks += len(chunks)
        print(f"[OK] Ingested {len(chunks)} chunks from {file_path.name}")

    print(f"\n[DONE] Total chunks ingested: {total_chunks}")
    print(f"[DONE] Collection count: {collection.count()}")
    print(f"[DONE] Chroma DB path: {CHROMA_DB_PATH}")
    print(f"[DONE] Embed model: {EMBED_MODEL}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest UMKM markdown docs into ChromaDB")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and recreate collection before ingest",
    )
    args = parser.parse_args()

    ingest_docs(reset=args.reset)