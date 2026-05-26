from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from backend.models.schemas import (
    AdditionalEvidenceRequest,
    Appointment,
    ApplicantMessageResponse,
    CasePacket,
    DecisionNotice,
    ExtensionAppointmentRequest,
    ExtensionDecisionRequest,
    ExtensionRequest,
    ExtensionRequestCreateRequest,
)
from backend.services.audit_service import AuditService
from backend.services.case_service import CaseService
from backend.services.notification_service import NotificationService
from backend.services.observability_service import ObservabilityService
from backend.services.utils import parse_utcish_datetime, utc_now


class ExtensionWorkflow:
    def __init__(self) -> None:
        self.case_service = CaseService()
        self.audit_service = AuditService()
        self.notification_service = NotificationService()
        self.observability_service = ObservabilityService()

    def create_extension_request(self, case_id: str, payload: ExtensionRequestCreateRequest) -> dict | None:
        case = self.case_service.get_case(case_id)
        if not case:
            return None

        if case.workflow.extension_state in {
            "EXTENSION_REQUESTED",
            "EXTENSION_APPOINTMENT_REQUIRED",
            "UNDER_EXTENSION_REVIEW",
        }:
            return {"status": "CONFLICT", "detail": "An extension workflow is already active for this case."}

        requires_appointment, appointment_reason = self._evaluate_appointment_need(case, payload)
        request = ExtensionRequest(
            request_id=f"EXT-{uuid4().hex[:10].upper()}",
            requested_new_departure_date=payload.requested_new_departure_date,
            reason=payload.reason,
            supporting_note=payload.supporting_note,
            requires_appointment=requires_appointment,
            appointment_required_reason=appointment_reason,
        )
        case.workflow.extension_requests.append(request)

        if requires_appointment:
            case.workflow.extension_state = "EXTENSION_APPOINTMENT_REQUIRED"
            case.workflow.current_holder = "MISSION_OR_HEAD_OFFICE"
            case.workflow.action_required_from = "MISSION_OR_HEAD_OFFICE"
            case.workflow.next_action = "SCHEDULE_EXTENSION_APPOINTMENT"
            case = self.case_service.save_case(case)
            case = self.case_service.update_state(
                case,
                "EXTENSION_APPOINTMENT_REQUIRED",
                actor="APPLICANT",
                description="Applicant submitted an extension request that requires appointment or manual handling.",
                action_owner="MISSION_OR_HEAD_OFFICE",
            )
            message = ApplicantMessageResponse(
                message_type="STATUS_UPDATE",
                subject=f"Extension appointment needed for case {case_id}",
                message="Your extension request needs appointment or manual handling before a decision can be reviewed. This is not a final visa decision.",
                required_actions=[
                    "Check the extension appointment instructions in your case timeline.",
                    "Wait for the mission or head-office handling step to schedule or confirm the appointment.",
                ],
                deadline="",
            )
        else:
            case.workflow.extension_state = "EXTENSION_REQUESTED"
            case.workflow.current_holder = "OFFICER"
            case.workflow.action_required_from = "OFFICER"
            case.workflow.next_action = "REVIEW_EXTENSION_REQUEST"
            case = self.case_service.save_case(case)
            case = self.case_service.update_state(
                case,
                "EXTENSION_REQUESTED",
                actor="APPLICANT",
                description="Applicant submitted a Sri Lanka tourist visit extension request.",
                action_owner="OFFICER",
            )
            message = ApplicantMessageResponse(
                message_type="STATUS_UPDATE",
                subject=f"Extension request received for case {case_id}",
                message="Your extension request has been recorded and is waiting for review. This is not a final visa decision.",
                required_actions=[],
                deadline="",
            )

        self.notification_service.store_message(case_id, message)
        self.audit_service.write_event(
            case_id=case_id,
            event_type="EXTENSION_REQUEST_CREATED",
            actor_type="APPLICANT",
            actor_id=case.applicant.contact_email,
            payload=request.model_dump(),
            policy_version=case.policy_context.policy_version,
            rule_version_used=case.policy_context.effective_rule_version,
            publication_reference=case.policy_context.publication_reference,
            policy_source_uri=case.policy_context.source_uri,
            **self._observability_event_kwargs(
                self.observability_service.record_workflow_outcome(
                    case,
                    request.model_dump(),
                    prompt_version=self.audit_service.prompt_version,
                    model_version=self.audit_service.model_version,
                )
            ),
        )
        return {
            "status": "RECORDED",
            "case_id": case_id,
            "extension_state": case.workflow.extension_state,
            "requires_appointment": requires_appointment,
            "appointment_required_reason": appointment_reason,
            "request_id": request.request_id,
            "human_decision_required": True,
        }

    def record_extension_appointment(self, case_id: str, payload: ExtensionAppointmentRequest) -> dict | None:
        case = self.case_service.get_case(case_id)
        if not case:
            return None
        if not case.workflow.extension_requests:
            return {"status": "CONFLICT", "detail": "No extension request exists for this case."}

        appointment = self._upsert_extension_appointment(case, payload)
        status_upper = payload.status.strip().upper()
        case.workflow.extension_state = (
            "UNDER_EXTENSION_REVIEW" if status_upper in {"COMPLETED", "ATTENDED"} else "EXTENSION_APPOINTMENT_REQUIRED"
        )
        case.workflow.current_holder = "OFFICER" if case.workflow.extension_state == "UNDER_EXTENSION_REVIEW" else "APPLICANT"
        case.workflow.action_required_from = case.workflow.current_holder
        case.workflow.next_action = (
            "REVIEW_EXTENSION_REQUEST"
            if case.workflow.extension_state == "UNDER_EXTENSION_REVIEW"
            else "ATTEND_EXTENSION_APPOINTMENT"
        )
        case = self.case_service.save_case(case)
        case = self.case_service.update_state(
            case,
            case.workflow.extension_state,
            actor="MISSION_OR_HEAD_OFFICE",
            description=(
                "Extension appointment was completed and the request returned for review."
                if case.workflow.extension_state == "UNDER_EXTENSION_REVIEW"
                else "Extension appointment details were recorded for applicant follow-up."
            ),
            action_owner=case.workflow.current_holder,
        )

        message = ApplicantMessageResponse(
            message_type="STATUS_UPDATE",
            subject=f"Extension appointment update for case {case_id}",
            message=(
                "Your extension appointment status has been updated and the request is back in review."
                if case.workflow.extension_state == "UNDER_EXTENSION_REVIEW"
                else "Your extension appointment details have been recorded. Follow the scheduled instructions before requesting a status escalation."
            ),
            required_actions=(
                []
                if case.workflow.extension_state == "UNDER_EXTENSION_REVIEW"
                else [
                    "Attend the extension appointment at the scheduled location and time.",
                    "Bring the same passport and supporting records used for the extension request.",
                ]
            ),
            deadline=appointment.scheduled_for if appointment.scheduled_for else "",
        )
        self.notification_service.store_message(case_id, message)
        self.audit_service.write_event(
            case_id=case_id,
            event_type="EXTENSION_APPOINTMENT_RECORDED",
            actor_type="SYSTEM",
            actor_id="extension_workflow",
            payload=appointment.model_dump(),
            policy_version=case.policy_context.policy_version,
            rule_version_used=case.policy_context.effective_rule_version,
            publication_reference=case.policy_context.publication_reference,
            policy_source_uri=case.policy_context.source_uri,
            **self._observability_event_kwargs(
                self.observability_service.record_workflow_outcome(
                    case,
                    appointment.model_dump(),
                    prompt_version=self.audit_service.prompt_version,
                    model_version=self.audit_service.model_version,
                )
            ),
        )
        return {
            "status": "RECORDED",
            "case_id": case_id,
            "extension_state": case.workflow.extension_state,
            "appointment": appointment.model_dump(),
            "human_decision_required": True,
        }

    def record_extension_decision(self, case_id: str, payload: ExtensionDecisionRequest) -> dict | None:
        case = self.case_service.get_case(case_id)
        if not case:
            return None
        if not case.workflow.extension_requests:
            return {"status": "CONFLICT", "detail": "No extension request exists for this case."}

        latest_request = case.workflow.extension_requests[-1]
        latest_request.decided_at = utc_now()
        latest_request.decided_by = payload.officer_id
        latest_request.decision_notes = payload.reason

        if payload.decision == "APPROVE":
            latest_request.status = "CLOSED"
            latest_request.decision = "APPROVED"
            case.visa_application.departure_date = latest_request.requested_new_departure_date
            case.workflow.extension_state = "EXTENSION_DECISION_RECORDED"
            case.workflow.current_holder = "APPLICANT"
            case.workflow.action_required_from = "APPLICANT"
            case.workflow.next_action = "REVIEW_EXTENSION_DECISION_NOTICE"
            case.workflow.decision_notice = DecisionNotice(
                message_type="STATUS_UPDATE",
                subject=f"Extension decision recorded for case {case_id}",
                summary="A human officer recorded an approved extension outcome for this case.",
                next_steps=[
                    "Review the updated departure date in your case record.",
                    "Follow any official overstay, endorsement, or travel instructions attached to the decision notice.",
                ],
            )
            case = self.case_service.save_case(case)
            case = self.case_service.update_state(
                case,
                "EXTENSION_DECISION_RECORDED",
                actor=payload.officer_id,
                description="Officer approved the extension request.",
                action_owner="APPLICANT",
            )
        elif payload.decision == "REQUEST_MORE_INFO":
            latest_request.status = "OPEN"
            latest_request.decision = "MORE_INFO_REQUIRED"
            case.workflow.extension_state = "EXTENSION_REQUESTED"
            case.workflow.current_holder = "APPLICANT"
            case.workflow.action_required_from = "APPLICANT"
            case.workflow.next_action = "RESPOND_TO_EXTENSION_INFORMATION_REQUEST"
            case.workflow.additional_evidence_requests.append(
                AdditionalEvidenceRequest(
                    request_id=f"EXT-EVID-{uuid4().hex[:8].upper()}",
                    requested_items=["EXTENSION_SUPPORTING_EVIDENCE"],
                    reason=payload.reason,
                    deadline="",
                    status="OPEN",
                )
            )
            case = self.case_service.save_case(case)
            case = self.case_service.update_state(
                case,
                "WAITING_FOR_DOCUMENTS",
                actor=payload.officer_id,
                description="Officer requested more information for the extension workflow.",
                action_owner="APPLICANT",
            )
        else:
            latest_request.status = "CLOSED"
            latest_request.decision = "REFUSED"
            case.workflow.extension_state = "EXTENSION_DECISION_RECORDED"
            case.workflow.current_holder = "APPLICANT"
            case.workflow.action_required_from = "APPLICANT"
            case.workflow.next_action = "REVIEW_EXTENSION_DECISION_NOTICE"
            case.workflow.decision_notice = DecisionNotice(
                message_type="STATUS_UPDATE",
                subject=f"Extension decision recorded for case {case_id}",
                summary="A human officer recorded a refused extension outcome for this case.",
                next_steps=["Review the official next-step instructions and any departure requirements in your case notice."],
            )
            case = self.case_service.save_case(case)
            case = self.case_service.update_state(
                case,
                "EXTENSION_DECISION_RECORDED",
                actor=payload.officer_id,
                description="Officer refused the extension request.",
                action_owner="APPLICANT",
            )

        final_notice = case.workflow.decision_notice
        message = ApplicantMessageResponse(
            message_type=final_notice.message_type if final_notice else "STATUS_UPDATE",
            subject=final_notice.subject if final_notice else f"Extension update for case {case_id}",
            message=final_notice.summary if final_notice else "Your extension request status has been updated.",
            required_actions=final_notice.next_steps if final_notice else [],
            deadline="",
        )
        self.notification_service.store_message(case_id, message)
        self.audit_service.write_event(
            case_id=case_id,
            event_type="EXTENSION_DECISION_RECORDED",
            actor_type="OFFICER",
            actor_id=payload.officer_id,
            payload=payload.model_dump(),
            policy_version=case.policy_context.policy_version,
            rule_version_used=case.policy_context.effective_rule_version,
            publication_reference=case.policy_context.publication_reference,
            policy_source_uri=case.policy_context.source_uri,
            human_action=payload.decision,
            **self._observability_event_kwargs(
                self.observability_service.record_human_decision(
                    case,
                    payload.model_dump(),
                    recommendation="EXTENSION_DECISION_RECORDED",
                    prompt_version=self.audit_service.prompt_version,
                    model_version=self.audit_service.model_version,
                )
            ),
        )
        return {
            "status": "RECORDED",
            "case_id": case_id,
            "extension_state": case.workflow.extension_state,
            "decision": payload.decision,
            "human_decision_required": True,
        }

    def _evaluate_appointment_need(
        self,
        case: CasePacket,
        payload: ExtensionRequestCreateRequest,
    ) -> tuple[bool, str]:
        original_departure = parse_utcish_datetime(case.visa_application.departure_date)
        requested_departure = parse_utcish_datetime(payload.requested_new_departure_date)
        if case.mock_profile.get("extension_requires_appointment"):
            return True, "Mock profile requires appointment-based extension handling."
        if case.workflow.manual_referral_reason:
            return True, "Manual referral is already active on the case."
        if original_departure and requested_departure and requested_departure > original_departure + timedelta(days=30):
            return True, "Requested extension exceeds the straight-through 30-day PoC threshold."
        return False, ""

    def _upsert_extension_appointment(self, case: CasePacket, payload: ExtensionAppointmentRequest) -> Appointment:
        for appointment in case.workflow.appointments:
            if appointment.appointment_type == "EXTENSION_APPOINTMENT":
                appointment.appointment_id = payload.appointment_id or appointment.appointment_id or f"EXT-APT-{uuid4().hex[:8].upper()}"
                appointment.status = payload.status
                appointment.location = payload.location
                appointment.scheduled_for = payload.scheduled_for
                appointment.instructions = payload.instructions
                return appointment

        appointment = Appointment(
            appointment_type="EXTENSION_APPOINTMENT",
            appointment_id=payload.appointment_id or f"EXT-APT-{uuid4().hex[:8].upper()}",
            status=payload.status,
            location=payload.location,
            scheduled_for=payload.scheduled_for,
            instructions=payload.instructions,
        )
        case.workflow.appointments.append(appointment)
        return appointment

    @staticmethod
    def _observability_event_kwargs(metadata: dict) -> dict:
        return {
            "trace_id": metadata.get("trace_id", ""),
            "observation_id": metadata.get("observation_id", ""),
            "observability_export_status": metadata.get("observability_export_status", ""),
            "observability_target": metadata.get("observability_target", ""),
            "evaluation_labels": metadata.get("evaluation_labels", []),
        }
