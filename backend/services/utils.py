from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def utc_now_datetime() -> datetime:
    return datetime.now(timezone.utc)


def utc_now() -> str:
    return utc_now_datetime().isoformat().replace("+00:00", "Z")


def stable_hash(payload: Any) -> str:
    normalized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
