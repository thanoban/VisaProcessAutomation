from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any


def utc_now_datetime() -> datetime:
    return datetime.now(timezone.utc)


def utc_now() -> str:
    return utc_now_datetime().isoformat().replace("+00:00", "Z")


def parse_utcish_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def decision_urgency(value: str | None, *, now: datetime | None = None) -> str:
    due_at = parse_utcish_datetime(value)
    if not due_at:
        return "UNSCHEDULED"
    current_time = now or utc_now_datetime()
    if due_at < current_time:
        return "OVERDUE"
    if due_at <= current_time + timedelta(hours=48):
        return "DUE_WITHIN_48H"
    return "ON_TRACK"


def stable_hash(payload: Any) -> str:
    normalized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
