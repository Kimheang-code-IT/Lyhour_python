"""Temporary Excel payload cache (diskcache, no database)."""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

from loguru import logger

try:
    import diskcache as dc

    _HAS_DISKCACHE = True
except ImportError:
    dc = None  # type: ignore[assignment]
    _HAS_DISKCACHE = False

_DEFAULT_TTL = 60 * 60 * 24  # 24 hours
_CACHE_DIR_NAME = "excel_cache"


def _cache_dir() -> Path:
    base = Path.home() / ".kiec_engineering"
    base.mkdir(parents=True, exist_ok=True)
    return base / _CACHE_DIR_NAME


class ExcelSessionCache:
    """Store parsed Excel payloads temporarily on disk with TTL."""

    _instance: ExcelSessionCache | None = None

    def __init__(self) -> None:
        self._memory: dict[str, Any] = {}
        self._cache = None
        if _HAS_DISKCACHE and dc is not None:
            cache_path = _cache_dir()
            cache_path.mkdir(parents=True, exist_ok=True)
            self._cache = dc.Cache(str(cache_path), size_limit=256 * 1024 * 1024)

    @classmethod
    def instance(cls) -> ExcelSessionCache:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def put(self, session_id: str, payload: dict, *, ttl: int = _DEFAULT_TTL) -> None:
        data = pickle.dumps(payload)
        if self._cache is not None:
            self._cache.set(session_id, data, expire=ttl)
        else:
            self._memory[session_id] = payload
        logger.debug("Excel session cached: {}", session_id)

    def get(self, session_id: str) -> dict | None:
        if self._cache is not None:
            raw = self._cache.get(session_id)
            if raw is None:
                return None
            try:
                value = pickle.loads(raw)
            except Exception:
                logger.warning("Corrupt excel cache entry removed: {}", session_id)
                self.delete(session_id)
                return None
            return value if isinstance(value, dict) else None
        payload = self._memory.get(session_id)
        return payload if isinstance(payload, dict) else None

    def delete(self, session_id: str) -> None:
        if self._cache is not None:
            try:
                del self._cache[session_id]
            except KeyError:
                pass
        self._memory.pop(session_id, None)

    def clear(self) -> None:
        if self._cache is not None:
            self._cache.clear()
        self._memory.clear()
        logger.info("Excel session cache cleared")
