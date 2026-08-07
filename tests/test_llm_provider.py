"""Regression: `get_provider()` default harus "gemini", bukan "ollama".

Kenapa test ini ada: sebelumnya `get_provider()` default ke `"ollama"`. Deploy
mana pun yang lupa menyetel `LLM_PROVIDER` akan gagal dengan connection-refused
ke server Ollama yang tidak pernah dijalankan (127.0.0.1:11434) — pesan error
yang menunjuk ke arah yang salah, dan tidak ada test yang menangkapnya. Gemini
2.5 Flash sudah lama menjadi provider produksi sebenarnya, jadi default kode
harus mencerminkan itu.

`get_provider()` hanya baca `os.getenv` murni (tanpa import SDK apa pun di
module scope — lihat `test_llm_provider_import.py`), jadi test ini aman jalan
di bawah dependency set minimal CI.
"""
from __future__ import annotations

from app.llm_provider import get_provider


def test_get_provider_defaults_to_gemini_when_unset(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    assert get_provider() == "gemini"


def test_get_provider_respects_explicit_value_stripped_and_lowercased(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "  Ollama  ")
    assert get_provider() == "ollama"
