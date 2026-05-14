from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import ollama
import requests

from .config import AppConfig, load_config
from .error_handler import OllamaNotRunningError

LOGGER = logging.getLogger(__name__)


def _cache_path(config: AppConfig) -> Path:
    return config.cache_dir / "ollama_embeddings.json"


def _load_cache(path: Path) -> dict[str, list[float]]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict):
            return {str(k): list(v) for k, v in payload.items()}
    except (json.JSONDecodeError, OSError):
        return {}
    return {}


def _save_cache(path: Path, payload: dict[str, list[float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle)


def check_ollama(base_url: str, timeout_seconds: int = 3) -> None:
    try:
        response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=timeout_seconds)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise OllamaNotRunningError("Start Ollama with: ollama serve") from exc


def init_ollama(config: AppConfig | None = None) -> None:
    cfg = config or load_config()
    check_ollama(cfg.ollama_base_url, timeout_seconds=cfg.request_timeout_seconds)


def generate_text(
    prompt: str,
    *,
    model: str | None = None,
    base_url: str | None = None,
    temperature: float = 0.7,
    timeout_seconds: int | None = None,
) -> str:
    config = load_config()
    target_model = model or config.ollama_chat_model
    target_url = base_url or config.ollama_base_url
    check_ollama(target_url, timeout_seconds=config.request_timeout_seconds)

    client = ollama.Client(host=target_url)
    try:
        response: dict[str, Any] = client.generate(
            model=target_model,
            prompt=prompt,
            options={"temperature": temperature},
            stream=False,
            keep_alive="5m",
        )
    except Exception as exc:  # pragma: no cover - depends on Ollama runtime
        raise OllamaNotRunningError("Start Ollama with: ollama serve") from exc

    return str(response.get("response", "")).strip()


def embed_text(
    text: str,
    *,
    model: str | None = None,
    base_url: str | None = None,
) -> list[float]:
    config = load_config()
    target_model = model or config.ollama_embed_model
    target_url = base_url or config.ollama_base_url
    check_ollama(target_url, timeout_seconds=config.request_timeout_seconds)

    cache_file = _cache_path(config)
    cache = _load_cache(cache_file)
    cache_key = f"{target_model}:{text.strip().lower()}"
    if cache_key in cache:
        return cache[cache_key]

    client = ollama.Client(host=target_url)
    try:
        response: dict[str, Any] = client.embeddings(model=target_model, prompt=text)
    except Exception as exc:  # pragma: no cover - depends on Ollama runtime
        raise OllamaNotRunningError("Start Ollama with: ollama serve") from exc

    vector = response.get("embedding") or []
    if not isinstance(vector, list):
        vector = []

    cache[cache_key] = [float(value) for value in vector]
    _save_cache(cache_file, cache)
    return cache[cache_key]
