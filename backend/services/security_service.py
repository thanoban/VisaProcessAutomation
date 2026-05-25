def minimal_screening_status(status: str) -> str:
    allowed = {"CLEAR", "POSSIBLE_MATCH", "CONFIRMED_HIT", "SYSTEM_UNAVAILABLE"}
    return status if status in allowed else "SYSTEM_UNAVAILABLE"
