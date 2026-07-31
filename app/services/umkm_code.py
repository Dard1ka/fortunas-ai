"""Generate kode publik UMKM dari alamat lengkap (mis. Kudus → KDS-001).

Alur:
  1. AI (llm_provider, Gemini) mengekstrak NAMA KOTA/KABUPATEN dari alamat lengkap.
     Kalau LLM gagal/mati → fallback heuristik (segmen alamat).
  2. Prefix 3 huruf = konsonan pertama nama kota (Kudus→KDS, Semarang→SMR).
     Deterministik & mudah ditebak, jadi tak tergantung LLM untuk hasil akhir.
  3. Nomor urut = maksimum urut existing untuk prefix itu + 1 → 'KDS-001'.

Dipakai saat UMKM mengisi alamat (registrasi / profil). Kode dipakai pelanggan
untuk memesan tanpa scan QR.
"""
from __future__ import annotations

import json
import logging
import re

from app.llm_provider import llm_generate

logger = logging.getLogger(__name__)

# Kata yang bukan bagian nama kota, dibuang saat heuristik/normalisasi.
_ADMIN_WORDS = {
    "kota", "kabupaten", "kab", "kec", "kecamatan", "kelurahan", "desa",
    "provinsi", "jl", "jalan", "no", "rt", "rw", "blok", "gang", "gg",
}


def _prefix_from_city(city: str) -> str:
    """3 huruf kapital dari konsonan nama kota (Kudus→KDS). Fallback huruf apa adanya."""
    letters = re.sub(r"[^a-z]", "", (city or "").lower())
    consonants = re.sub(r"[aeiou]", "", letters)
    base = (consonants or letters)[:3]
    return base.upper().ljust(3, "X") if base else "XXX"


def _heuristic_city(address: str) -> str:
    """Tebak kota tanpa LLM: cari token setelah 'kota'/'kabupaten', atau segmen
    koma yang paling mungkin (bukan angka/kode pos)."""
    low = (address or "").lower()
    m = re.search(r"\b(?:kota|kabupaten|kab\.?)\s+([a-z]+)", low)
    if m:
        return m.group(1)
    # Segmen koma non-numerik terpanjang yang bukan kata administratif.
    segs = [s.strip() for s in re.split(r"[,\n]", address or "") if s.strip()]
    cands = []
    for seg in segs:
        words = [w for w in re.findall(r"[A-Za-z]+", seg)
                 if w.lower() not in _ADMIN_WORDS]
        if words and not re.search(r"\d", seg):
            cands.append(" ".join(words))
    return (cands[-1] if cands else (segs[0] if segs else "")).strip()


def extract_city(address: str) -> str:
    """Ekstrak nama kota/kabupaten dari alamat lengkap via LLM; fallback heuristik."""
    addr = (address or "").strip()
    if not addr:
        return ""
    try:
        raw = llm_generate(
            "Ekstrak NAMA KOTA atau KABUPATEN dari alamat Indonesia berikut. "
            "Balas HANYA JSON: {\"city\": \"NamaKota\"} tanpa kata 'Kota'/'Kabupaten'.\n\n"
            f"Alamat: {addr}",
            json_mode=True, temperature=0.0, max_tokens=40, timeout=20,
        )
        city = str(json.loads(raw).get("city", "")).strip()
        # Bersihkan kata administratif yang mungkin ikut.
        city = " ".join(w for w in city.split() if w.lower() not in _ADMIN_WORDS)
        if city:
            return city
    except Exception as exc:  # noqa: BLE001 — jangan gagalkan pembuatan kode
        logger.warning("Ekstrak kota via LLM gagal (%s); pakai heuristik.", exc)
    return _heuristic_city(addr)


def _next_sequence(prefix: str, existing_codes: list[str]) -> int:
    max_n = 0
    for code in existing_codes:
        m = re.match(rf"^{re.escape(prefix)}-(\d+)$", (code or "").strip().upper())
        if m:
            max_n = max(max_n, int(m.group(1)))
    return max_n + 1


def generate_umkm_code(address: str, existing_codes: list[str] | None = None) -> dict:
    """Return {'code': 'KDS-001', 'city': 'Kudus', 'prefix': 'KDS'} dari alamat.

    Selalu menghasilkan kode valid (fallback prefix 'XXX' bila kota tak terdeteksi).
    """
    existing = existing_codes or []
    city = extract_city(address)
    prefix = _prefix_from_city(city)
    seq = _next_sequence(prefix, existing)
    return {"code": f"{prefix}-{seq:03d}", "city": city, "prefix": prefix}
