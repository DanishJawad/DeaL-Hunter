from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def is_cache_fresh(path: Path, ttl_seconds: int) -> bool:
    if not path.exists():
        return False
    if ttl_seconds <= 0:
        return True
    age_seconds = time.time() - path.stat().st_mtime
    return age_seconds <= ttl_seconds


def load_cached_json(path: Path, ttl_seconds: int) -> tuple[bool, Any | None]:
    if not is_cache_fresh(path, ttl_seconds):
        return False, None
    try:
        return True, read_json(path)
    except json.JSONDecodeError:
        return False, None


def save_cached_json(path: Path, payload: Any) -> None:
    write_json(path, payload)
