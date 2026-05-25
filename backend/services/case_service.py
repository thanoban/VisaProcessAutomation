from __future__ import annotations

from typing import Iterable

from sqlalchemy import select

from backend.database.session import SessionLocal
from backend.models.db import AuditEventRecord, CaseRecord, NotificationRecord, OfficerBriefRecord
from backend.models.schemas import (
    ApplicationCreateRequest,
    CasePacket,
    CaseStatusResponse,
    DocumentItem,
    OfficerBrief,
)
from backend.services.utils import utc_now


class CaseService:
    def create_case(self, payload: ApplicationCreateRequest) -> CasePacket:
        case = CasePacket(
            case_id=payload.case_id,
            applicant=payload.applicant,
            visa_application=payload.visa_application,
            documents=payload.documents,
            policy_context=payload.policy_context,
            submission_channel=payload.submission_channel,
            decision_due_at=payload.decision_due_at,
            retention_class=payload.retention_class,
            mock_profile=payload.mock_profile,
            status_timeline=[{"state": "SUBMITTED", "timestamp": utc_now(), "actor": "SYSTEM"}],
        )
        with SessionLocal() as session:
            record = CaseRecord(
                case_id=case.case_id,
                applicant=case.applicant.model_dump(),
                visa_application=case.visa_application.model_dump(),
                documents=[d.model_dump() for d in case.documents],
                policy_context=case.policy_context.model_dump(),
                agent_outputs=case.agent_outputs,
                workflow=case.workflow.model_dump(),
                audit=case.audit.model_dump(),
                submission_channel=case.submission_channel,
                status_timeline=case.status_timeline,
                applicant_message_history=case.applicant_message_history,
                security_handling_code=case.security_handling_code,
                decision_due_at=case.decision_due_at,
                override_required=case.override_required,
                retention_class=case.retention_class,
                mock_profile=case.mock_profile,
            )
            session.merge(record)
            session.commit()
        return case

    def get_case(self, case_id: str) -> CasePacket | None:
        with SessionLocal() as session:
            record = session.get(CaseRecord, case_id)
            return self._record_to_case(record) if record else None

    def save_case(self, case: CasePacket) -> CasePacket:
        case.audit.updated_at = utc_now()
        with SessionLocal() as session:
            record = CaseRecord(
                case_id=case.case_id,
                applicant=case.applicant.model_dump(),
                visa_application=case.visa_application.model_dump(),
                documents=[d.model_dump() for d in case.documents],
                policy_context=case.policy_context.model_dump(),
                agent_outputs=case.agent_outputs,
                workflow=case.workflow.model_dump(),
                audit=case.audit.model_dump(),
                submission_channel=case.submission_channel,
                status_timeline=case.status_timeline,
                applicant_message_history=case.applicant_message_history,
                security_handling_code=case.security_handling_code,
                decision_due_at=case.decision_due_at,
                override_required=case.override_required,
                retention_class=case.retention_class,
                mock_profile=case.mock_profile,
            )
            session.merge(record)
            session.commit()
        return case

    def add_documents(self, case_id: str, documents: Iterable[DocumentItem]) -> CasePacket | None:
        case = self.get_case(case_id)
        if not case:
            return None
        case.documents.extend(documents)
        return self.save_case(case)

    def update_state(self, case: CasePacket, new_state: str, actor: str = "SYSTEM") -> CasePacket:
        if case.workflow.current_state != new_state:
            case.workflow.previous_states.append(case.workflow.current_state)
            case.workflow.current_state = new_state
            case.status_timeline.append({"state": new_state, "timestamp": utc_now(), "actor": actor})
        return self.save_case(case)

    def save_officer_brief(self, brief: OfficerBrief) -> None:
        with SessionLocal() as session:
            session.merge(OfficerBriefRecord(case_id=brief.case_id, payload=brief.model_dump()))
            session.commit()

    def get_officer_brief(self, case_id: str) -> OfficerBrief | None:
        with SessionLocal() as session:
            record = session.get(OfficerBriefRecord, case_id)
            return OfficerBrief.model_validate(record.payload) if record else None

    def list_audit_events(self, case_id: str) -> list[dict]:
        with SessionLocal() as session:
            stmt = select(AuditEventRecord).where(AuditEventRecord.case_id == case_id)
            records = session.execute(stmt).scalars().all()
            return [record.payload for record in records]

    def get_case_status(self, case: CasePacket) -> CaseStatusResponse:
        latest_message = case.applicant_message_history[-1] if case.applicant_message_history else None
        required_actions = latest_message.get("required_actions", []) if latest_message else []
        return CaseStatusResponse(
            case_id=case.case_id,
            status=case.workflow.current_state,
            latest_message=latest_message,
            required_actions=required_actions,
            uploaded_documents=[doc.model_dump() for doc in case.documents],
            deadlines={"decision_due_at": case.decision_due_at},
            service_notices=[
                {"code": "HUMAN_REVIEW_REQUIRED", "message": "Final legal decision remains with an immigration officer."}
            ],
            timeline=case.status_timeline,
        )

    def add_notification(self, case_id: str, payload: dict) -> None:
        with SessionLocal() as session:
            session.add(NotificationRecord(case_id=case_id, channel="EMAIL", payload=payload))
            session.commit()

    def _record_to_case(self, record: CaseRecord) -> CasePacket:
        return CasePacket.model_validate(
            {
                "case_id": record.case_id,
                "applicant": record.applicant,
                "visa_application": record.visa_application,
                "documents": record.documents,
                "policy_context": record.policy_context,
                "agent_outputs": record.agent_outputs,
                "workflow": record.workflow,
                "audit": record.audit,
                "submission_channel": record.submission_channel,
                "status_timeline": record.status_timeline,
                "applicant_message_history": record.applicant_message_history,
                "security_handling_code": record.security_handling_code,
                "decision_due_at": record.decision_due_at,
                "override_required": record.override_required,
                "retention_class": record.retention_class,
                "mock_profile": record.mock_profile,
            }
        )
