from __future__ import annotations

from backend.models.schemas import ApplicantMessageResponse


def create_evidence_request(case_id: str, missing_items: list[str]) -> ApplicantMessageResponse:
    return ApplicantMessageResponse(
        message_type="MISSING_DOCUMENTS",
        subject=f"Additional information needed for case {case_id}",
        message="Please upload the missing items listed below so processing can continue. This is not a visa decision.",
        required_actions=missing_items,
        deadline="2026-12-31",
    )


def notify_applicant(case_id: str, message: ApplicantMessageResponse) -> dict:
    return {"case_id": case_id, "status": "QUEUED", "message": message.model_dump()}
