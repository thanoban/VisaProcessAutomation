from __future__ import annotations

from typing import Iterable

from sqlalchemy import select

from backend.database.session import SessionLocal
from backend.models.db import AuditEventRecord, CaseRecord, NotificationRecord, OfficerBriefRecord
from backend.models.schemas import (
    AuthorizationStatusResponse,
    ApplicationCreateRequest,
    CasePacket,
    CaseTimelineEvent,
    CaseStatusResponse,
    DocumentItem,
    OfficerBrief,
    WorkflowState,
)
from backend.services.utils import utc_now
from backend.services.utils import decision_urgency


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
            workflow=WorkflowState(
                current_state="SUBMITTED",
                current_holder="SYSTEM",
                next_action="PRECHECK_APPLICATION",
                action_required_from="SYSTEM",
                eta_status="ETA_SUBMITTED",
            ),
            status_timeline=[
                CaseTimelineEvent(
                    state="SUBMITTED",
                    timestamp=utc_now(),
                    actor="SYSTEM",
                    description="Sri Lanka tourist visit case submitted for pre-check.",
                    action_owner="SYSTEM",
                )
            ],
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
                status_timeline=[event.model_dump() for event in case.status_timeline],
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
                status_timeline=[event.model_dump() for event in case.status_timeline],
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
        incoming_documents = list(documents)
        if not incoming_documents:
            return case

        documents_by_type = {document.document_type: document for document in case.documents}
        for document in incoming_documents:
            documents_by_type[document.document_type] = document
        case.documents = list(documents_by_type.values())

        open_requests = [request for request in case.workflow.additional_evidence_requests if request.status == "OPEN"]
        for request in open_requests:
            request.status = "RESPONDED"

        case.workflow.current_holder = "SYSTEM"
        case.workflow.action_required_from = "SYSTEM"
        case.workflow.next_action = "RECHECK_SUBMITTED_DOCUMENTS"
        if open_requests or case.workflow.current_state == "WAITING_FOR_DOCUMENTS":
            case.workflow.eta_status = "ETA_DOCUMENT_RESPONSE_RECEIVED"
            case = self.append_timeline_event(
                case,
                state=case.workflow.current_state,
                actor="APPLICANT",
                description="Applicant submitted additional or replacement documents for re-check.",
                action_owner="SYSTEM",
            )
            return case

        return self.save_case(case)

    def update_state(
        self,
        case: CasePacket,
        new_state: str,
        actor: str = "SYSTEM",
        description: str = "",
        action_owner: str | None = None,
    ) -> CasePacket:
        if case.workflow.current_state != new_state:
            case.workflow.previous_states.append(case.workflow.current_state)
            case.workflow.current_state = new_state
            case.status_timeline.append(
                CaseTimelineEvent(
                    state=new_state,
                    timestamp=utc_now(),
                    actor=actor,
                    description=description,
                    action_owner=action_owner,
                )
            )
        if action_owner:
            case.workflow.current_holder = action_owner
        return self.save_case(case)

    def append_timeline_event(
        self,
        case: CasePacket,
        *,
        state: str,
        actor: str,
        description: str,
        action_owner: str | None = None,
    ) -> CasePacket:
        case.status_timeline.append(
            CaseTimelineEvent(
                state=state,
                timestamp=utc_now(),
                actor=actor,
                description=description,
                action_owner=action_owner,
            )
        )
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

    def get_case_timeline(self, case: CasePacket) -> list[dict]:
        return [event.model_dump() for event in case.status_timeline]

    def list_cases(self) -> list[CasePacket]:
        with SessionLocal() as session:
            records = session.execute(select(CaseRecord)).scalars().all()
            return [self._record_to_case(record) for record in records]

    def get_case_status(self, case: CasePacket) -> CaseStatusResponse:
        latest_message = case.applicant_message_history[-1] if case.applicant_message_history else None
        required_actions = latest_message.get("required_actions", []) if latest_message else []
        authorization_status = AuthorizationStatusResponse(
            case_id=case.case_id,
            workflow_pack=case.workflow.workflow_pack,
            eta_status=case.workflow.eta_status,
            port_clearance_state=case.workflow.port_clearance_state,
            manual_referral_reason=case.workflow.manual_referral_reason,
            action_required_from=case.workflow.action_required_from,
            next_action=case.workflow.next_action,
            policy_version=case.policy_context.policy_version,
            effective_date=case.policy_context.effective_date,
            rule_version_used=case.policy_context.effective_rule_version,
            publication_reference=case.policy_context.publication_reference,
            source_uri=case.policy_context.source_uri,
            official_sources=case.policy_context.official_sources,
            verified_at=case.policy_context.verified_at,
        )
        service_notices = [
            {"code": "HUMAN_REVIEW_REQUIRED", "message": "Final legal decision remains with an immigration officer."}
        ]
        if case.workflow.manual_referral_reason:
            service_notices.append(
                {
                    "code": "MANUAL_REFERRAL_ACTIVE",
                    "message": "This case is following a manual referral route and may require mission or head-office handling before ETA can proceed.",
                }
            )
        if case.workflow.appointments:
            service_notices.append(
                {
                    "code": "APPOINTMENT_TRACKING_ACTIVE",
                    "message": "A review or service appointment is attached to this case. Check the appointment instructions and status before traveling or following up.",
                }
            )
        if case.workflow.port_clearance_state == "PENDING_PORT_CLEARANCE":
            service_notices.append(
                {
                    "code": "PORT_CLEARANCE_PENDING",
                    "message": "Travel authorization is not the same as final port-of-entry clearance. Carry the same passport and supporting records for inspection.",
                }
            )
        if case.workflow.extension_state != "NOT_REQUESTED":
            service_notices.append(
                {
                    "code": "EXTENSION_WORKFLOW_ACTIVE",
                    "message": "An extension-related workflow is active for this case. Follow the latest extension instructions and service channel guidance.",
                }
            )
        return CaseStatusResponse(
            case_id=case.case_id,
            status=case.workflow.current_state,
            latest_message=latest_message,
            required_actions=required_actions,
            additional_evidence_requests=[request.model_dump() for request in case.workflow.additional_evidence_requests],
            uploaded_documents=[doc.model_dump() for doc in case.documents],
            deadlines={
                "decision_due_at": case.decision_due_at,
                "decision_urgency": decision_urgency(case.decision_due_at),
            },
            service_notices=service_notices,
            timeline=[event.model_dump() for event in case.status_timeline],
            current_holder=case.workflow.current_holder,
            next_action=case.workflow.next_action,
            action_required_from=case.workflow.action_required_from,
            authorization_status=authorization_status.model_dump(),
            port_clearance_state=case.workflow.port_clearance_state,
            extension_state=case.workflow.extension_state,
            manual_referral_reason=case.workflow.manual_referral_reason,
            appointments=[appointment.model_dump() for appointment in case.workflow.appointments],
            decision_notice=case.workflow.decision_notice.model_dump() if case.workflow.decision_notice else None,
            port_clearance_events=[event.model_dump() for event in case.workflow.port_clearance_events],
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
