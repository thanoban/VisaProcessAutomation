from __future__ import annotations

from backend.models.schemas import CasePacket
from backend.services.security_service import minimal_screening_status


def query_security_screening(case: CasePacket, identity_bundle: dict) -> dict:
    status = minimal_screening_status(case.mock_profile.get("security_status", "CLEAR"))
    return {
        "security_status": status,
        "match_categories": case.mock_profile.get("security_match_categories", []),
        "tool_call_references": [{"system": "mock_security_screening", "status": status}],
    }


def query_previous_visa_history(case: CasePacket, passport_number: str) -> dict:
    return {
        "passport_number": passport_number,
        "previous_approvals": case.mock_profile.get("previous_approvals", 0),
        "previous_refusals": case.mock_profile.get("previous_refusals", 0),
        "overstays": case.mock_profile.get("overstays", 0),
        "violations": case.mock_profile.get("violations", 0),
    }
