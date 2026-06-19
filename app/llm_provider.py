"""Lapisan LLM provider-agnostic.

Pilih backend via env LLM_PROVIDER:
  - "ollama" (default) → model lokal (qwen3:8b) via Ollama
  - "openai"           → ChatGPT (OpenAI API)

Semua pemanggilan LLM di app (insight, voice parser, SQL agent) lewat
`llm_generate()` supaya ganti provider cukup ubah .env tanpa sentuh kode.
"""
from __future__ import annotations

import os

import requests
from dotenv import load_dotenv

load_dotenv()


def get_provider() -> str:
    return os.getenv("LLM_PROVIDER", "ollama").strip().lower()


def get_model() -> str:
    provider = get_provider()
    if provider == "openai":
        return os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if provider == "gemini":
        return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    return os.getenv("OLLAMA_MODEL", "qwen3:8b")


def llm_generate(
    prompt: str,
    *,
    json_mode: bool = False,
    temperature: float = 0.1,
    max_tokens: int = 1000,
    timeout: int = 120,
) -> str:
    """Kirim prompt → kembalikan teks jawaban. Routing berdasar LLM_PROVIDER.

    json_mode=True memaksa output berupa JSON object (Ollama: format=json,
    OpenAI: response_format json_object, Gemini: responseMimeType application/json
    — prompt sebaiknya tetap menyebut kata 'json')."""
    provider = get_provider()
    if provider == "openai":
        return _openai_generate(prompt, json_mode, temperature, max_tokens, timeout)
    if provider == "gemini":
        return _gemini_generate(prompt, json_mode, temperature, max_tokens, timeout)
    return _ollama_generate(prompt, json_mode, temperature, max_tokens, timeout)


def _ollama_generate(prompt, json_mode, temperature, max_tokens, timeout) -> str:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    if json_mode:
        payload["format"] = "json"
    res = requests.post(f"{base_url}/api/generate", json=payload, timeout=timeout)
    res.raise_for_status()
    data = res.json()
    if data.get("error"):
        raise RuntimeError(f"Ollama error: {data['error']}")
    text = (data.get("response") or "").strip()
    if not text:  # qwen3 kadang taruh jawaban di 'thinking'
        text = (data.get("thinking") or "").strip()
    return text


def _openai_generate(prompt, json_mode, temperature, max_tokens, timeout) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY belum di-set di .env")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    res = requests.post(
        f"{base_url}/chat/completions",
        json=payload,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=timeout,
    )
    if res.status_code >= 400:
        # Munculkan pesan error OpenAI yang informatif (mis. invalid key, quota).
        try:
            detail = res.json().get("error", {}).get("message", res.text)
        except Exception:  # noqa: BLE001
            detail = res.text
        raise RuntimeError(f"OpenAI error {res.status_code}: {detail}")
    data = res.json()
    return (data["choices"][0]["message"]["content"] or "").strip()


def _gemini_generate(prompt, json_mode, temperature, max_tokens, timeout) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY belum di-set di .env")
    base_url = os.getenv(
        "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"
    )
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    gen_config: dict = {
        "temperature": temperature,
        "maxOutputTokens": max_tokens,
        # Matikan "thinking" (model 2.5) supaya tidak menghabiskan token output &
        # tidak bikin balasan kosong untuk tugas ekstraksi/JSON sederhana.
        "thinkingConfig": {"thinkingBudget": 0},
    }
    if json_mode:
        gen_config["responseMimeType"] = "application/json"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": gen_config,
    }

    # Key dikirim sebagai query param (?key=), bukan Bearer.
    url = f"{base_url}/models/{model}:generateContent?key={api_key}"
    res = requests.post(url, json=payload, timeout=timeout)
    if res.status_code >= 400:
        try:
            detail = res.json().get("error", {}).get("message", res.text)
        except Exception:  # noqa: BLE001
            detail = res.text
        raise RuntimeError(f"Gemini error {res.status_code}: {detail}")

    data = res.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini tidak mengembalikan kandidat: {data}")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise RuntimeError(f"Gemini mengembalikan teks kosong. Raw: {data}")
    return text


def check_llm_health() -> dict:
    """Status koneksi LLM sesuai provider aktif (untuk endpoint /llm/health)."""
    provider = get_provider()
    model = get_model()
    if provider == "openai":
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            res = requests.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15,
            )
            res.raise_for_status()
            return {"status": "ok", "provider": "openai", "model": model}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "provider": "openai", "model": model, "error": str(e)}

    if provider == "gemini":
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            base_url = os.getenv(
                "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"
            )
            res = requests.get(f"{base_url}/models?key={api_key}", timeout=15)
            res.raise_for_status()
            return {"status": "ok", "provider": "gemini", "model": model}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "provider": "gemini", "model": model, "error": str(e)}

    # ollama
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    try:
        res = requests.get(f"{base_url}/api/tags", timeout=10)
        res.raise_for_status()
        models = [m.get("name", "") for m in res.json().get("models", [])]
        return {
            "status": "ok",
            "provider": "ollama",
            "model": model,
            "available_models": models,
            "model_available": model in models,
        }
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "provider": "ollama", "model": model, "error": str(e)}
