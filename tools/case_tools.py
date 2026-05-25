from __future__ import annotations

from backend.models.schemas import CasePacket, OfficerBrief, OfficerDecisionRequest
from backend.services.case_service import CaseService

case_service = CaseService()


def get_application(case_id: str) -> CasePacket | None:
    return case_service.get_case(case_id)


def get_uploaded_documents(case_id: str) -> list[dict]:
    case = case_service.get_case(case_id)
    return [doc.model_dump() for doc in case.documents] if case else []


def check_payment_status(case_id: str) -> dict:
    case = case_service.get_case(case_id)
    status = case.visa_application.payment_status if case else "UNKNOWN"
    return {"case_id": case_id, "payment_status": status, "is_complete": status == "PAID"}


def update_case_state(case_id: str, new_state: str) -> CasePacket | None:
    case = case_service.get_case(case_id)
    if not case:
        return None
    return case_service.update_state(case, new_state)


def create_officer_brief(case_id: str, agent_outputs: dict) -> OfficerBrief | None:
    case = case_service.get_case(case_id)
    if not case:
        return None
    return OfficerBrief.model_validate(agent_outputs["officer_brief"])


def submit_officer_decision(case_id: str, decision: str, officer_id: str, reason: str, override_reason: str = "") -> dict:
    payload = OfficerDecisionRequest(decision=decision, officer_id=officer_id, reason=reason, override_reason=override_reason)
    return payload.model_dump()
