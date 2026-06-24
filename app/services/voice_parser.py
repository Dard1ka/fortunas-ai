"""Voice transcript → structured transaction extractor.

Two tiers:
1. Fast regex/heuristic — handles cleanly-formatted voice transcripts where the
   user says invoice/product/qty/harga keywords in roughly the expected order
   (e.g. "Invoice 489438, sabun cuci, qty 10, harga 8500").
2. LLM fallback (Qwen3:8b via Ollama) — for messy free-form transcripts with
   spoken numbers ("delapan ribu lima ratus" → 8500), code-switching, or
   reordered fields.

Output keys: invoice, product, qty, unit_price, total, customer, country,
confidence. Field types are not yet coerced — that happens in wa_validator.
"""
from __future__ import annotations

import json
import re
from typing import Any


from app.llm_provider import llm_generate

# ───── Indonesian spoken-number map for the regex tier ─────

_NUMBER_WORDS_ID = {
    "nol": 0, "kosong": 0,
    "satu": 1, "dua": 2, "tiga": 3, "empat": 4, "lima": 5,
    "enam": 6, "tujuh": 7, "delapan": 8, "sembilan": 9,
    "sepuluh": 10, "sebelas": 11,
}

_NUMBER_SCALES_ID = {
    "ratus": 100,
    "ribu": 1_000,
    "rb": 1_000,
    "juta": 1_000_000,
    "jt": 1_000_000,
    "miliar": 1_000_000_000,
    "milyar": 1_000_000_000,
}


def _word_to_int_id(text: str) -> int | None:
    """Convert phrases like 'delapan ribu lima ratus' → 8500. Conservative: only
    handles up to millions. Returns None if it can't extract a number."""
    if not text:
        return None
    s = text.strip().lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    tokens = s.split()
    if not tokens:
        return None

    # If transcript already contains digits, take the first numeric run.
    digits = re.search(r"\d[\d.,]*", s)
    if digits:
        # Strip thousand separators like 8.500 → 8500
        raw = digits.group(0).replace(".", "").replace(",", "")
        try:
            return int(raw)
        except ValueError:
            pass

    total = 0
    current = 0
    matched_any = False
    for tok in tokens:
        if tok in ("se",):
            continue
        if tok.startswith("se") and tok[2:] in _NUMBER_SCALES_ID:
            scale = _NUMBER_SCALES_ID[tok[2:]]
            current = max(current, 1) * scale
            total += current
            current = 0
            matched_any = True
            continue
        if tok in _NUMBER_WORDS_ID:
            current += _NUMBER_WORDS_ID[tok]
            matched_any = True
        elif tok in _NUMBER_SCALES_ID:
            scale = _NUMBER_SCALES_ID[tok]
            current = max(current, 1) * scale
            total += current
            current = 0
            matched_any = True

    if not matched_any:
        return None
    return total + current


# ───── Regex fast path ─────

_INVOICE_RE = re.compile(r"(?:invoice|no\.?\s*invoice|invoiceno)[\s:]+([A-Za-z0-9\-]+)", re.IGNORECASE)
_QTY_RE     = re.compile(r"(?:qty|quantity|jumlah|sebanyak)[\s:]+([\w\s\-]+?)(?:[,\.]|$|harga|untuk|seharga|@)", re.IGNORECASE)
_PRICE_RE   = re.compile(r"(?:harga|seharga|price|@)[\s:]+([\w\s\-]+?)(?:[,\.]|$|untuk|pelanggan|negara)", re.IGNORECASE)
_CUSTOMER_RE = re.compile(r"(?:pelanggan|customer)[\s:]+([\w\s\-\.]+?)(?:[,\.]|$|negara|country)", re.IGNORECASE)
_COUNTRY_RE = re.compile(r"(?:negara|country)[\s:]+([\w\s\-]+?)(?:[,\.]|$)", re.IGNORECASE)


def _normalize_invoice(s: str) -> str:
    # Accept INV-2024, 489438, "INV 2024". Strip whitespace; keep original casing.
    return s.strip()


def _extract_product(transcript: str, invoice: str | None) -> str:
    """The product name typically sits after the invoice clause and before the
    first qty keyword. Falls back to the chunk between commas if structure differs."""
    s = transcript
    if invoice:
        idx = s.lower().find(invoice.lower())
        if idx >= 0:
            s = s[idx + len(invoice):]

    s = re.split(r"\b(?:qty|quantity|jumlah|sebanyak|harga|seharga|price)\b", s, maxsplit=1, flags=re.IGNORECASE)[0]
    s = s.strip(",.;:- \n")
    return s.strip()


def regex_parse(transcript: str) -> dict[str, Any] | None:
    """Return a parsed dict if the heuristic finds all critical fields, else None."""
    if not transcript:
        return None

    invoice_match = _INVOICE_RE.search(transcript)
    qty_match = _QTY_RE.search(transcript)
    price_match = _PRICE_RE.search(transcript)

    # Invoice TIDAK lagi wajib — dibuat otomatis di lapisan route/pipeline.
    # Cukup qty + price untuk dianggap transkrip terstruktur (fast path).
    if not (qty_match and price_match):
        return None

    invoice = _normalize_invoice(invoice_match.group(1)) if invoice_match else ""
    qty = _word_to_int_id(qty_match.group(1))
    price = _word_to_int_id(price_match.group(1))
    if qty is None or price is None:
        return None

    product = _extract_product(transcript, invoice)

    customer_match = _CUSTOMER_RE.search(transcript)
    country_match = _COUNTRY_RE.search(transcript)
    customer = customer_match.group(1).strip() if customer_match else ""
    country = country_match.group(1).strip() if country_match else "Indonesia"

    return {
        "invoice": invoice,
        "product": product,
        "qty": qty,
        "unit_price": price,
        "total": qty * price,
        "customer": customer,
        "country": country,
        "confidence": 0.92,
        "source": "regex",
    }


# ───── LLM fallback ─────

_PROMPT_TEMPLATE = """Kamu adalah parser transaksi toko UMKM. Ekstrak struktur transaksi dari ucapan singkat berikut.

Output WAJIB berupa object JSON tunggal dengan field:
- invoice (string)
- product (string)
- qty (integer)
- unit_price (integer Rupiah, bukan desimal — \"delapan ribu lima ratus\" → 8500)
- total (integer Rupiah = qty * unit_price)
- customer (string, kosong kalau tidak disebut)
- country (string, default \"Indonesia\")

Aturan:
- Bahasa Indonesia. Angka tersebut bisa berupa kata (\"delapan ribu lima ratus\") atau digit (\"8500\").
- JANGAN tambahkan field lain.
- JANGAN bungkus dalam markdown.

UCAPAN:
\"\"\"{transcript}\"\"\"

JSON:"""


def llm_parse(transcript: str) -> dict[str, Any] | None:
    """Call LLM (provider via LLM_PROVIDER: ollama/openai) for free-form transcripts.
    Returns None on any failure."""
    prompt = _PROMPT_TEMPLATE.format(transcript=transcript)
    try:
        raw = llm_generate(
            prompt, json_mode=True, temperature=0.05, max_tokens=400, timeout=120
        )
        if not raw:
            return None
        data = json.loads(raw)
    except Exception:  # noqa: BLE001 — LLM/parse gagal → fallback ke None
        return None

    try:
        qty = int(data.get("qty") or 0)
        unit_price = int(data.get("unit_price") or 0)
    except (TypeError, ValueError):
        return None

    confidence = _score_completeness(data)

    return {
        "invoice": str(data.get("invoice") or "").strip(),
        "product": str(data.get("product") or "").strip(),
        "qty": qty,
        "unit_price": unit_price,
        "total": int(data.get("total") or (qty * unit_price)),
        "customer": str(data.get("customer") or "").strip(),
        "country": str(data.get("country") or "Indonesia").strip(),
        "confidence": confidence,
        "source": "llm",
    }


def _score_completeness(data: dict[str, Any]) -> float:
    fields = ["invoice", "product", "qty", "unit_price"]
    filled = sum(1 for f in fields if data.get(f))
    return round(0.55 + 0.1 * filled, 2)


# ───── Entry ─────


def parse_transcript(transcript: str) -> dict[str, Any]:
    """Parse a voice transcript. Tries regex first, falls back to LLM.

    Always returns a dict — confidence will be 0.0 and fields will be empty if
    nothing extractable.
    """
    if not transcript or not transcript.strip():
        return {
            "invoice": "", "product": "", "qty": 0,
            "unit_price": 0, "total": 0, "customer": "",
            "country": "Indonesia", "confidence": 0.0, "source": "empty",
        }

    fast = regex_parse(transcript)
    if fast is not None:
        return fast

    llm = llm_parse(transcript)
    if llm is not None:
        return llm

    return {
        "invoice": "", "product": "", "qty": 0,
        "unit_price": 0, "total": 0, "customer": "",
        "country": "Indonesia", "confidence": 0.0, "source": "failed",
    }
