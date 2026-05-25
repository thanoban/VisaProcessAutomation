from __future__ import annotations

from backend.models.schemas import CasePacket


def calculate_risk_score(case: CasePacket) -> dict:
    profile = case.mock_profile
    risk_band = profile.get("risk_band", "LOW")
    score_map = {"LOW": 18, "MEDIUM": 44, "HIGH": 76, "CRITICAL": 92}
    indicators = profile.get("fraud_indicators", [])
    if profile.get("sudden_deposits"):
        indicators = list({*indicators, "SUDDEN_DEPOSITS"})
    recommended_route = "NORMAL_REVIEW"
    if risk_band in {"HIGH", "CRITICAL"}:
        recommended_route = "ENHANCED_REVIEW"
    if case.mock_profile.get("security_status") in {"POSSIBLE_MATCH", "CONFIRMED_HIT"}:
        recommended_route = "SECURITY_REVIEW"
    return {
        "risk_band": risk_band,
        "risk_score": score_map.get(risk_band, 50),
        "fraud_indicators": indicators,
        "evidence_based_reasons": case.mock_profile.get("risk_reasons", indicators),
        "protected_attribute_used": False,
        "recommended_route": recommended_route,
    }
