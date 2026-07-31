"""Regression: `app.llm_provider` harus bisa di-import TANPA dep `requests`.

Kenapa test ini ada: CI (`.github/workflows/ci.yml`) sengaja meng-install dep
minimal dan TIDAK meng-install `requirements.txt`, jadi `requests` tidak tersedia
di sana. Begitu ada modul app yang meng-import `llm_provider` di module scope
(mis. `app/services/category_ai.py` ← `app/api/routes/products.py`), seluruh
collection pytest ikut mati dengan ModuleNotFoundError — bukan karena testnya
salah, tapi karena dep call-time bocor ke import time.

`requests` hanya dipakai saat MEMANGGIL LLM, jadi import-nya lokal di dalam
fungsi. Test ini mengunci invariant itu supaya tidak regres lagi.
"""
from __future__ import annotations

import builtins
import importlib
import sys

import pytest

# Modul yang meng-import `llm_generate` di module scope — semuanya harus tetap
# bisa di-import tanpa `requests`.
LLM_CONSUMERS = (
    "app.llm_provider",
    "app.llm_service",
    "app.services.category_ai",
    "app.services.umkm_code",
    "app.services.voice_parser",
)


@pytest.fixture()
def no_requests(monkeypatch):
    """Sembunyikan `requests` seolah-olah berjalan di env CI minimal."""
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "requests" or name.startswith("requests."):
            raise ModuleNotFoundError("No module named 'requests'")
        return real_import(name, *args, **kwargs)

    # delitem/setattr lewat monkeypatch: nilai asli dikembalikan saat teardown,
    # jadi modul yang sudah ter-import di test lain tidak ikut rusak.
    monkeypatch.delitem(sys.modules, "requests", raising=False)
    for name in LLM_CONSUMERS:
        monkeypatch.delitem(sys.modules, name, raising=False)
    monkeypatch.setattr(builtins, "__import__", fake_import)


def test_llm_provider_imports_without_requests(no_requests):
    mod = importlib.import_module("app.llm_provider")
    assert callable(mod.llm_generate)
    assert callable(mod.check_llm_health)


@pytest.mark.parametrize("module_name", LLM_CONSUMERS)
def test_llm_consumers_import_without_requests(no_requests, module_name):
    assert importlib.import_module(module_name) is not None
