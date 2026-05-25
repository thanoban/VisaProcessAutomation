from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any


def utc_now() -> str:
    return datetime.utcnow().isoformat()


def stable_hash(payload: Any) -> str:
    normalized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
