from __future__ import annotations

from uuid import uuid4

from backend.models.schemas import (
    AdditionalEvidenceRequest,
    ApplicantMessageResponse,
    Appointment,
    CasePacket,
    DecisionNotice,
    NationalityExceptionRule,
    OfficerBrief,
    OfficerBriefAgentResult,
    OfficerDecisionRequest,
    PolicyRequirementsResponse,
    PortClearanceEvent,
)
from backend.services.audit_service import AuditService
from backend.services.case_service import CaseService
from backend.services.notification_service import NotificationService
from backend.services.policy_service import load_policy_manifest
from backend.services.sri_lanka_reference_service import SriLankaReferenceService
from backend.services.utils import stable_hash
from tools.audit_tools import write_audit_log
from tools.case_tools import check_payment_status, get_application, get_uploaded_documents
from tools.document_tools import check_photo_quality, extract_document_fields, validate_passport
from tools.financial_tools import calculate_bank_statement_metrics, parse_employment_letter
from tools.notification_tools import create_evidence_request, notify_applicant
from tools.policy_tools import retrieve_policy_sections
from tools.risk_tools import calculate_risk_score
from tools.security_tools import query_previous_visa_history, query_security_screening


class TouristVisaWorkflow:
    def __init__(self) -> None:
        self.case_service = CaseService()
        self.audit_service = AuditService()
        self.notification_service = NotificationService()
        self.reference_service = SriLankaReferenceService()

    def process_case(self, case_id: str) -> dict | None:
        case = get_application(case_id)
        if not case:
            return None

        case = self._apply_governance_context(case)
        case.workflow.current_holder = "SYSTEM"
        case.workflow.action_required_from = "SYSTEM"
        case.workflow.next_action = "RUN_INTAKE_PRECHECK"
        case.workflow.eta_status = "ETA_UNDER_PRECHECK"
        case = self.case_service.save_case(case)
        case = self.case_service.update_state(
            case,
            "UNDER_PRECHECK",
            actor="SYSTEM",
            description="Sri Lanka tourist visit pre-check started.",
            action_owner="SYSTEM",
        )

        intake = self._run_intake(case)
        self._store_agent_output(case, intake)

        if intake["status"] != "COMPLETE":
            return self._handle_evidence_loop(case, intake)

        exception_rule = self.reference_service.find_exception_rule(case)
        if exception_rule:
            return self._handle_manual_referral(case, intake, exception_rule)

        case = self.case_service.get_case(case.case_id)
        case.workflow.current_holder = "SYSTEM"
        case.workflow.action_required_from = "SYSTEM"
        case.workflow.next_action = "RUN_ELIGIBILITY_ANALYSIS"
        case.workflow.eta_status = "ETA_UNDER_ANALYSIS"
        case = self.case_service.save_case(case)
        case = self.case_service.update_state(
            case,
            "UNDER_ANALYSIS",
            actor="SYSTEM",
            description="Sri Lanka tourist visit automated analysis started.",
            action_owner="SYSTEM",
        )

        document = self._run_document_validator(case)
        financial = self._run_financial(case)
        policy = self._run_policy(case, financial)
        security = self._run_security(case)
        risk = self._run_risk(case)

        outputs = [intake, document, financial, policy, security, risk]
        for output in outputs[1:]:
            self._store_agent_output(case, output)

        recommendation, blocking_issues, risk_flags = self._route(outputs)
        case = self.case_service.get_case(case.case_id)
        case = self._update_workflow_for_recommendation(case, recommendation, blocking_issues, policy.get("missing_evidence", []))

        supervisor_output = self._supervisor_output(case, outputs, recommendation, blocking_issues, risk_flags)
        self._store_agent_output(case, supervisor_output)

        if case.workflow.current_state == "READY_FOR_OFFICER_REVIEW":
            officer_brief_output = self._run_officer_liaison(case, outputs, supervisor_output)
            self._store_agent_output(case, officer_brief_output)
            self.audit_service.write_event(
                case_id=case.case_id,
                event_type="CASE_READY_FOR_OFFICER_REVIEW",
                actor_type="SYSTEM",
                actor_id="workflow",
                payload=supervisor_output,
                recommendation=recommendation,
                evidence_ids=supervisor_output["evidence_references"],
                policy_ids=[ref["policy_id"] for ref in supervisor_output["policy_references"]],
                policy_version=case.policy_context.policy_version,
                rule_version_used=case.policy_context.effective_rule_version,
                publication_reference=case.policy_context.publication_reference,
                policy_source_uri=case.policy_context.source_uri,
            )
        else:
            self.audit_service.write_event(
                case_id=case.case_id,
                event_type="CASE_WAITING_FOR_APPLICANT",
                actor_type="SYSTEM",
                actor_id="workflow",
                payload=supervisor_output,
                recommendation=recommendation,
                evidence_ids=supervisor_output["evidence_references"],
                policy_ids=[ref["policy_id"] for ref in supervisor_output["policy_references"]],
                policy_version=case.policy_context.policy_version,
                rule_version_used=case.policy_context.effective_rule_version,
                publication_reference=case.policy_context.publication_reference,
                policy_source_uri=case.policy_context.source_uri,
            )
        return supervisor_output

    def submit_officer_decision(self, case_id: str, payload: OfficerDecisionRequest) -> dict | None:
        case = self.case_service.get_case(case_id)
        if not case:
            return None

        recommendation = case.agent_outputs.get("supervisor_agent", {}).get("recommendation", "")
        override_required = payload.decision == "REJECT" and recommendation == "APPROVE_READY"
        if payload.decision != "REQUEST_MORE_INFO" and recommendation and payload.override_reason:
            override_required = True
        case.override_required = override_required

        if payload.decision == "APPROVE":
            case.workflow.eta_status = "ETA_ISSUED"
            case.workflow.port_clearance_state = "PENDING_PORT_CLEARANCE"
            case.workflow.current_holder = "PORT_OF_ENTRY"
            case.workflow.action_required_from = "PORT_OF_ENTRY"
            case.workflow.next_action = "PRESENT_PASSPORT_AT_PORT_OF_ENTRY"
            case.workflow.decision_notice = DecisionNotice(
                message_type="STATUS_UPDATE",
                subject=f"Tourist visit authorization ready for case {case_id}",
                summary="The case has completed officer review. Travel documents must still be presented for port-of-entry clearance.",
                next_steps=[
                    "Carry the passport used for the application.",
                    "Retain ETA or authorization proof for travel and check-in.",
                    "Be ready for immigration clearance at the Sri Lanka port of entry.",
                ],
            )
            case.workflow.port_clearance_events.append(
                PortClearanceEvent(
                    event_type="AUTHORIZATION_READY",
                    status="PENDING_PORT_CLEARANCE",
                    notes="Authorization is ready, but final entry clearance remains with the port-of-entry officer.",
                )
            )
            case = self.case_service.save_case(case)
            case = self.case_service.update_state(
                case,
                "POST_DECISION_FULFILLMENT",
                actor=payload.officer_id,
                description="Officer approved the case for authorization issuance and port-of-entry follow-up.",
                action_owner="PORT_OF_ENTRY",
            )
        elif payload.decision == "REQUEST_MORE_INFO":
            request = AdditionalEvidenceRequest(
                request_id=f"REQ-{uuid4()}",
                requested_items=["ADDITIONAL_SUPPORTING_EVIDENCE"],
                reason=payload.reason,
                status="OPEN",
            )
            case.workflow.additional_evidence_requests.append(request)
            case.workflow.eta_status = "ETA_ADDITIONAL_EVIDENCE_REQUIRED"
            case.workflow.current_holder = "APPLICANT"
            case.workflow.action_required_from = "APPLICANT"
            case.workflow.next_action = "RESPOND_TO_INFORMATION_REQUEST"
            case = self.case_service.save_case(case)
            case = self.case_service.update_state(
                case,
                "WAITING_FOR_DOCUMENTS",
                actor=payload.officer_id,
                description="Officer requested more information from the applicant.",
                action_owner="APPLICANT",
            )
        elif payload.decision == "ESCALATE":
            case.workflow.current_holder = "SUPERVISOR"
            case.workflow.action_required_from = "SUPERVISOR"
            case.workflow.next_action = "SUPERVISOR_ESCALATION_REVIEW"
            case.workflow.eta_status = "ETA_ESCALATED"
            case = self.case_service.save_case(case)
            case = self.case_service.update_state(
                case,
                "READY_FOR_OFFICER_REVIEW",
                actor=payload.officer_id,
                description="Officer escalated the case for supervisor review.",
                action_owner="SUPERVISOR",
            )
        else:
            case.workflow.eta_status = "ETA_REFUSED"
            case.workflow.port_clearance_state = "NOT_APPLICABLE"
            case.workflow.current_holder = "APPLICANT"
            case.workflow.action_required_from = "APPLICANT"
            case.workflow.next_action = "REVIEW_DECISION_NOTICE"
            case.workflow.decision_notice = DecisionNotice(
                message_type="STATUS_UPDATE",
                subject=f"Update for case {case_id}",
                summary="The human officer has recorded a final decision on the case.",
                next_steps=["Review the decision notice and any official next-step instructions."],
            )
            case = self.case_service.save_case(case)
            case = self.case_service.update_state(
                case,
                "DECISION_RECORDED",
                actor=payload.officer_id,
                description="Officer recorded a final decision.",
                action_owner="APPLICANT",
            )

        event = self.audit_service.write_event(
            case_id=case_id,
            event_type="OFFICER_DECISION_RECORDED",
            actor_type="OFFICER",
            actor_id=payload.officer_id,
            payload=payload.model_dump(),
            policy_version=case.policy_context.policy_version,
            rule_version_used=case.policy_context.effective_rule_version,
            publication_reference=case.policy_context.publication_reference,
            policy_source_uri=case.policy_context.source_uri,
            recommendation=recommendation,
            human_action=payload.decision,
            override_reason=payload.override_reason,
        )

        final_message = case.workflow.decision_notice
        if final_message is None:
            final_message = DecisionNotice(
                message_type="STATUS_UPDATE",
                subject=f"Update for case {case_id}",
                summary="Your application status has been updated. Please sign in to view the latest next steps.",
                next_steps=[],
            )
        applicant_message = ApplicantMessageResponse(
            message_type=final_message.message_type,
            subject=final_message.subject,
            message=final_message.summary,
            required_actions=final_message.next_steps,
            deadline="",
        )
        self.notification_service.store_message(case_id, applicant_message)
        return {"status": "RECORDED", "audit_event": event, "human_decision_required": True}

    def send_applicant_message(self, case_id: str) -> ApplicantMessageResponse | None:
        case = self.case_service.get_case(case_id)
        if not case:
            return None
        if case.applicant_message_history:
            return ApplicantMessageResponse.model_validate(case.applicant_message_history[-1])
        message = ApplicantMessageResponse(
            message_type="STATUS_UPDATE",
            subject=f"Case {case_id} is under review",
            message="Your case is still under review by the Sri Lanka visa processing team. This is not a final decision.",
            required_actions=[],
            deadline="",
        )
        return self.notification_service.store_message(case_id, message)

    def get_policy_requirements(self, visa_class: str) -> PolicyRequirementsResponse:
        active_rules = self.reference_service.get_active_rules()
        manifest = load_policy_manifest()
        retrieved = retrieve_policy_sections(
            visa_class,
            "Sri Lanka",
            active_rules.active_policy_version.effective_date,
        )
        return PolicyRequirementsResponse(
            visa_class=visa_class.upper(),
            workflow_pack=retrieved["workflow_pack"],
            policy_version=retrieved["policy_version"],
            effective_date=active_rules.active_policy_version.effective_date,
            source_uri=retrieved["source_uri"],
            official_sources=manifest.get("official_sources", []),
            verified_at=manifest.get("verified_at", ""),
            requirements=[
                {"policy_id": section["policy_id"], "requirement": section["requirement"]}
                for section in retrieved["sections"]
            ],
        )

    def _run_intake(self, case: CasePacket) -> dict:
        docs = get_uploaded_documents(case.case_id)
        doc_types = {doc["document_type"] for doc in docs}
        required = {"PASSPORT", "BANK_STATEMENT", "FLIGHT_ITINERARY"}
        missing = sorted(required - doc_types)
        invalid = []
        if not check_payment_status(case.case_id)["is_complete"]:
            missing.append("PAYMENT_CONFIRMATION")
        if case.mock_profile.get("force_invalid_upload"):
            invalid.append("Unreadable file detected and replacement is required.")
        if case.mock_profile.get("unofficial_payment_reference"):
            invalid.append("Payment reference does not match an official channel.")
        status = "COMPLETE"
        if missing:
            status = "INCOMPLETE"
        elif invalid:
            status = "NEEDS_REVIEW"
        return {
            "agent_name": "intake_completeness_agent",
            "status": status,
            "missing_items": missing,
            "invalid_items": invalid,
            "evidence_ids_checked": [doc["document_id"] for doc in docs],
            "applicant_message": "Upload missing or replacement items to continue Sri Lanka ETA processing." if missing or invalid else "",
            "confidence": 0.98,
            "tool_calls": [{"tool": "get_uploaded_documents"}, {"tool": "check_payment_status"}],
        }

    def _run_document_validator(self, case: CasePacket) -> dict:
        passport_doc = next(doc for doc in case.documents if doc.document_type == "PASSPORT")
        extracted = extract_document_fields(case, passport_doc.document_id)
        validation = validate_passport(extracted, case.applicant.full_name)
        photo = check_photo_quality(case, passport_doc.document_id)
        mismatches = []
        if not validation["name_match"]:
            mismatches.append("Full name does not match application form.")
        status = "VALID" if validation["valid"] and photo["photo_quality"] == "PASS" else "INVALID"
        if case.mock_profile.get("document_needs_review"):
            status = "NEEDS_REVIEW"
        return {
            "agent_name": "document_validator_agent",
            "status": status,
            "document_findings": validation["findings"],
            "identity_mismatches": mismatches,
            "extracted_fields": {
                "passport_number": extracted["passport_number"],
                "full_name": extracted["full_name"],
                "date_of_birth": extracted["date_of_birth"],
                "nationality": extracted["nationality"],
                "expiry_date": extracted["expiry_date"],
            },
            "evidence_ids_checked": [passport_doc.document_id],
            "confidence": 0.93,
            "requires_human_review": True,
            "tool_calls": [{"tool": "extract_document_fields"}, {"tool": "validate_passport"}, {"tool": "check_photo_quality"}],
        }

    def _run_financial(self, case: CasePacket) -> dict:
        bank_doc = next(doc for doc in case.documents if doc.document_type == "BANK_STATEMENT")
        metrics = calculate_bank_statement_metrics(case, bank_doc.document_id)
        employment = parse_employment_letter(case)
        status = "PASS"
        if metrics["average_balance"] < float(case.mock_profile.get("minimum_required_funds", 1500.0)):
            status = "FAIL"
        elif metrics["suspicious_patterns"]:
            status = "NEEDS_REVIEW"
        return {
            "agent_name": "financial_employment_agent",
            "status": status,
            "financial_summary": f"Average balance {metrics['average_balance']} {metrics['currency']} against Sri Lanka tourist visit threshold.",
            "average_balance": metrics["average_balance"],
            "currency": metrics["currency"],
            "suspicious_patterns": metrics["suspicious_patterns"],
            "employment_ties": case.mock_profile.get("employment_ties", "STRONG"),
            "home_country_ties": case.mock_profile.get("home_country_ties", "STRONG"),
            "evidence_ids_checked": [bank_doc.document_id],
            "confidence": 0.9,
            "employment_letter": employment,
            "tool_calls": [{"tool": "calculate_bank_statement_metrics"}, {"tool": "parse_employment_letter"}],
        }

    def _run_policy(self, case: CasePacket, financial: dict) -> dict:
        retrieved = retrieve_policy_sections(
            case.visa_application.visa_class,
            case.policy_context.country,
            case.policy_context.effective_date,
        )
        missing_evidence = []
        criteria = []
        policy_flags = case.mock_profile.get("policy_failures", [])
        if case.mock_profile.get("conflicting_publication"):
            policy_flags = list({*policy_flags, "PUBLICATION_CONFLICT"})
        for section in retrieved["sections"]:
            status = "SATISFIED"
            reason = "Requirement supported by available evidence."
            evidence_ids = [doc.document_id for doc in case.documents]
            if section["policy_id"] == "TOURIST-12-B" and financial["average_balance"] < section["minimum_funds"]:
                status = "NOT_SATISFIED"
                reason = "Average balance below required threshold."
            if section["policy_id"] in policy_flags:
                status = "NOT_SATISFIED"
                reason = "Mock policy failure triggered for test scenario."
            if section.get("required_document") and section["required_document"] not in {doc.document_type for doc in case.documents}:
                status = "MISSING_EVIDENCE"
                reason = f"Missing required document {section['required_document']}."
                missing_evidence.append(section["required_document"])
            criteria.append(
                {
                    "policy_id": section["policy_id"],
                    "requirement": section["requirement"],
                    "status": status,
                    "evidence_ids": evidence_ids,
                    "reason": reason,
                }
            )
        if case.mock_profile.get("conflicting_publication"):
            criteria.append(
                {
                    "policy_id": "SL-RULE-CONFLICT",
                    "requirement": "Public publication wording and active internal rule pack must align.",
                    "status": "UNCLEAR",
                    "evidence_ids": [],
                    "reason": "Public and internal publication references conflict and require governance confirmation.",
                }
            )
            missing_evidence.append("ACTIVE_RULE_CONFIRMATION")
        eligibility_status = "MEETS_REQUIREMENTS"
        if any(item["status"] == "NOT_SATISFIED" for item in criteria):
            eligibility_status = "DOES_NOT_MEET"
        elif any(item["status"] in {"MISSING_EVIDENCE", "UNCLEAR"} for item in criteria):
            eligibility_status = "UNCLEAR"
        return {
            "agent_name": "policy_compliance_agent",
            "visa_class": case.visa_application.visa_class,
            "policy_version": retrieved["policy_version"],
            "rule_version_used": case.policy_context.effective_rule_version,
            "publication_reference": case.policy_context.publication_reference,
            "policy_source_uri": retrieved["source_uri"],
            "official_sources": case.policy_context.official_sources,
            "verified_at": case.policy_context.verified_at,
            "eligibility_status": eligibility_status,
            "criteria": criteria,
            "missing_evidence": missing_evidence,
            "confidence": 0.92,
            "tool_calls": [{"tool": "retrieve_policy_sections"}],
        }

    def _run_security(self, case: CasePacket) -> dict:
        history = query_previous_visa_history(case, case.applicant.passport_number)
        screening = query_security_screening(
            case,
            {"passport_number": case.applicant.passport_number, "full_name": case.applicant.full_name},
        )
        return {
            "agent_name": "security_background_agent",
            "security_status": screening["security_status"],
            "match_categories": screening["match_categories"],
            "requires_manual_security_review": True,
            "disclosure_level": "OFFICER_ONLY",
            "tool_call_references": screening["tool_call_references"] + [{"tool": "query_previous_visa_history", "history": history}],
            "confidence": 0.88,
            "tool_calls": [{"tool": "query_security_screening"}, {"tool": "query_previous_visa_history"}],
        }

    def _run_risk(self, case: CasePacket) -> dict:
        score = calculate_risk_score(case)
        return {
            "agent_name": "risk_fraud_agent",
            "risk_band": score["risk_band"],
            "risk_score": score["risk_score"],
            "fraud_indicators": score["fraud_indicators"],
            "evidence_based_reasons": score["evidence_based_reasons"],
            "protected_attribute_used": False,
            "recommended_route": score["recommended_route"],
            "confidence": 0.87,
            "tool_calls": [{"tool": "calculate_risk_score"}],
        }

    def _run_officer_liaison(self, case: CasePacket, outputs: list[dict], supervisor: dict) -> dict:
        brief = OfficerBrief(
            case_id=case.case_id,
            visa_class=case.visa_application.visa_class,
            applicant_summary=(
                f"{case.applicant.full_name}, passport {case.applicant.passport_number}, "
                f"travel purpose: {case.visa_application.purpose_of_travel}, workflow pack: {case.workflow.workflow_pack}"
            ),
            recommendation=supervisor["recommendation"],
            confidence=supervisor["confidence"],
            agent_results=[
                OfficerBriefAgentResult(
                    agent_name=item["agent_name"],
                    status=item.get("status", item.get("security_status", item.get("risk_band", "INFO"))),
                    summary=self._brief_summary(item),
                    risk_level=self._risk_level(item),
                )
                for item in outputs
            ],
            key_evidence=supervisor["evidence_references"],
            policy_references=supervisor["policy_references"],
            risk_flags=supervisor["risk_flags"],
            missing_items=outputs[0].get("missing_items", []),
            questions_for_officer=self._officer_questions(supervisor),
            recommendation_panel={
                "recommendation": supervisor["recommendation"],
                "human_decision_required": True,
                "next_action": supervisor["next_action"],
                "current_holder": supervisor["current_holder"],
                "action_required_from": supervisor["action_required_from"],
            },
            evidence_viewer={
                "passport_fields": outputs[1].get("extracted_fields", {}),
                "bank_statement_metrics": {
                    "average_balance": outputs[2].get("average_balance"),
                    "currency": outputs[2].get("currency"),
                    "suspicious_patterns": outputs[2].get("suspicious_patterns", []),
                },
                "itinerary_evidence": [doc.document_id for doc in case.documents if doc.document_type == "FLIGHT_ITINERARY"],
                "rule_version_used": case.policy_context.effective_rule_version,
                "publication_reference": case.policy_context.publication_reference,
                "policy_source_uri": case.policy_context.source_uri,
                "official_sources": case.policy_context.official_sources,
                "verified_at": case.policy_context.verified_at,
            },
            audit_timeline=self.case_service.list_audit_events(case.case_id),
        )
        self.case_service.save_officer_brief(brief)
        return {
            "agent_name": "officer_liaison_agent",
            "officer_brief": brief.model_dump(),
            "tool_calls": [{"tool": "create_officer_brief"}],
        }

    def _route(self, outputs: list[dict]) -> tuple[str, list[str], list[str]]:
        intake, document, financial, policy, security, risk = outputs
        blocking_issues: list[str] = []
        risk_flags = list(risk.get("fraud_indicators", []))

        if intake["status"] == "INCOMPLETE":
            blocking_issues.extend(intake["missing_items"])
            return "REQUEST_MORE_INFO", blocking_issues, risk_flags
        if intake["status"] == "NEEDS_REVIEW":
            blocking_issues.extend(intake.get("invalid_items", []))
            return "REQUEST_MORE_INFO", blocking_issues, risk_flags
        if security["security_status"] in ["POSSIBLE_MATCH", "CONFIRMED_HIT", "SYSTEM_UNAVAILABLE"]:
            blocking_issues.append(f"Security status {security['security_status']}.")
            return "ENHANCED_REVIEW", blocking_issues, risk_flags
        if document["status"] in ["INVALID", "NEEDS_REVIEW"]:
            blocking_issues.append("Document validation requires officer attention.")
            return "ENHANCED_REVIEW", blocking_issues, risk_flags
        if risk["risk_band"] in ["HIGH", "CRITICAL"]:
            blocking_issues.append("Elevated fraud or anomaly indicators detected.")
            return "ENHANCED_REVIEW", blocking_issues, risk_flags
        if financial["status"] == "FAIL":
            blocking_issues.append("Financial evidence below threshold.")
            return "REQUEST_MORE_INFO", blocking_issues, risk_flags
        if financial["status"] == "NEEDS_REVIEW":
            blocking_issues.append("Financial evidence needs clarification or additional support.")
            return "REQUEST_MORE_INFO", blocking_issues, risk_flags
        if policy["eligibility_status"] == "DOES_NOT_MEET":
            blocking_issues.append("Policy requirements are not fully met.")
            return "REFUSAL_DRAFT_READY", blocking_issues, risk_flags
        if policy["eligibility_status"] == "UNCLEAR":
            blocking_issues.append("Policy assessment needs more evidence or governance confirmation.")
            return "REQUEST_MORE_INFO", blocking_issues, risk_flags
        return "APPROVE_READY", blocking_issues, risk_flags

    def _handle_evidence_loop(self, case: CasePacket, intake: dict) -> dict:
        case = self.case_service.get_case(case.case_id)
        missing_items = intake["missing_items"] + intake.get("invalid_items", [])
        request = AdditionalEvidenceRequest(
            request_id=f"REQ-{uuid4()}",
            requested_items=missing_items,
            reason="Sri Lanka tourist visit processing requires the missing or replacement evidence listed.",
            deadline=case.decision_due_at or "",
            status="OPEN",
        )
        case.workflow.additional_evidence_requests.append(request)
        case.workflow.current_holder = "APPLICANT"
        case.workflow.action_required_from = "APPLICANT"
        case.workflow.next_action = "UPLOAD_REQUIRED_DOCUMENTS"
        case.workflow.eta_status = "ETA_ADDITIONAL_EVIDENCE_REQUIRED"
        case = self.case_service.save_case(case)
        case = self.case_service.update_state(
            case,
            "WAITING_FOR_DOCUMENTS",
            actor="SYSTEM",
            description="Case is waiting for missing or replacement evidence from the applicant.",
            action_owner="APPLICANT",
        )
        applicant_message = create_evidence_request(case.case_id, missing_items)
        self.notification_service.store_message(case.case_id, applicant_message)
        notify_applicant(case.case_id, applicant_message)
        self.audit_service.write_event(
            case_id=case.case_id,
            event_type="CASE_WAITING_FOR_DOCUMENTS",
            actor_type="SYSTEM",
            actor_id="workflow",
            payload=applicant_message.model_dump(),
            policy_version=case.policy_context.policy_version,
            rule_version_used=case.policy_context.effective_rule_version,
            publication_reference=case.policy_context.publication_reference,
            policy_source_uri=case.policy_context.source_uri,
        )
        supervisor_output = self._supervisor_output(
            case,
            [intake],
            "REQUEST_MORE_INFO",
            missing_items or ["Missing required evidence."],
        )
        self._store_agent_output(case, supervisor_output)
        return supervisor_output

    def _handle_manual_referral(self, case: CasePacket, intake: dict, rule: NationalityExceptionRule) -> dict:
        case = self.case_service.get_case(case.case_id)
        case.workflow.manual_referral_reason = rule.reason
        case.workflow.current_holder = "MISSION_OR_HEAD_OFFICE"
        case.workflow.action_required_from = "MISSION_OR_HEAD_OFFICE"
        case.workflow.next_action = "MANUAL_SPONSOR_OR_EXCEPTION_REVIEW"
        case.workflow.eta_status = "ETA_MANUAL_REVIEW"
        if not case.workflow.appointments:
            case.workflow.appointments.append(
                Appointment(
                    appointment_type="MANUAL_REFERRAL_REVIEW",
                    status="PENDING_SCHEDULING",
                    location="Head Office / Mission",
                    instructions="Manual sponsor or nationality exception review is required before ETA can proceed.",
                )
            )
        case = self.case_service.save_case(case)
        case = self.case_service.update_state(
            case,
            "REFERRED_TO_MANUAL_REVIEW",
            actor="SYSTEM",
            description=rule.reason,
            action_owner="MISSION_OR_HEAD_OFFICE",
        )
        supervisor_output = {
            "agent_name": "supervisor_agent",
            "case_id": case.case_id,
            "visa_class": case.visa_application.visa_class,
            "case_state": case.workflow.current_state,
            "recommendation": "ENHANCED_REVIEW",
            "confidence": 0.91,
            "human_decision_required": True,
            "summary_for_officer": "The case requires manual Sri Lanka sponsor or nationality exception handling before it can move through the straight-through ETA path.",
            "called_agents": [intake["agent_name"], "audit_compliance_agent"],
            "blocking_issues": [rule.reason],
            "risk_flags": [],
            "policy_references": [],
            "evidence_references": [doc.document_id for doc in case.documents],
            "next_action": case.workflow.next_action,
            "current_holder": case.workflow.current_holder,
            "action_required_from": case.workflow.action_required_from,
            "workflow_pack": case.workflow.workflow_pack,
            "rule_version_used": case.policy_context.effective_rule_version,
            "publication_reference": case.policy_context.publication_reference,
            "policy_version": case.policy_context.policy_version,
            "policy_source_uri": case.policy_context.source_uri,
            "official_sources": case.policy_context.official_sources,
            "verified_at": case.policy_context.verified_at,
            "manual_referral_reason": case.workflow.manual_referral_reason,
            "eta_status": case.workflow.eta_status,
            "port_clearance_state": case.workflow.port_clearance_state,
            "tool_calls": [],
        }
        self._store_agent_output(case, supervisor_output)
        self.audit_service.write_event(
            case_id=case.case_id,
            event_type="CASE_MANUAL_REFERRAL",
            actor_type="SYSTEM",
            actor_id="workflow",
            payload=supervisor_output,
            policy_version=case.policy_context.policy_version,
            rule_version_used=case.policy_context.effective_rule_version,
            publication_reference=case.policy_context.publication_reference,
            policy_source_uri=case.policy_context.source_uri,
            recommendation="ENHANCED_REVIEW",
        )
        return supervisor_output

    def _update_workflow_for_recommendation(
        self,
        case: CasePacket,
        recommendation: str,
        blocking_issues: list[str],
        missing_evidence: list[str],
    ) -> CasePacket:
        if recommendation == "REQUEST_MORE_INFO":
            request = AdditionalEvidenceRequest(
                request_id=f"REQ-{uuid4()}",
                requested_items=missing_evidence or blocking_issues,
                reason="Additional evidence or governance clarification is required for this Sri Lanka tourist visit case.",
                deadline=case.decision_due_at or "",
                status="OPEN",
            )
            case.workflow.additional_evidence_requests.append(request)
            case.workflow.current_holder = "APPLICANT"
            case.workflow.action_required_from = "APPLICANT"
            case.workflow.next_action = "RESPOND_TO_INFORMATION_REQUEST"
            case.workflow.eta_status = "ETA_ADDITIONAL_EVIDENCE_REQUIRED"
            case = self.case_service.save_case(case)
            return self.case_service.update_state(
                case,
                "WAITING_FOR_DOCUMENTS",
                actor="SYSTEM",
                description="Case needs more information before Sri Lanka ETA processing can continue.",
                action_owner="APPLICANT",
            )
        case.workflow.current_holder = "OFFICER"
        case.workflow.action_required_from = "OFFICER"
        case.workflow.next_action = "HUMAN_OFFICER_FINAL_REVIEW"
        case.workflow.eta_status = "ETA_UNDER_OFFICER_REVIEW"
        case = self.case_service.save_case(case)
        return self.case_service.update_state(
            case,
            "READY_FOR_OFFICER_REVIEW",
            actor="SYSTEM",
            description="Case has completed automated preparation and is ready for officer review.",
            action_owner="OFFICER",
        )

    def _supervisor_output(
        self,
        case: CasePacket,
        outputs: list[dict],
        recommendation: str,
        blocking_issues: list[str],
        risk_flags: list[str] | None = None,
    ) -> dict:
        policy_output = next((item for item in outputs if item["agent_name"] == "policy_compliance_agent"), {})
        confidence = round(sum(item.get("confidence", 0.85) for item in outputs) / max(len(outputs), 1), 2)
        called_agents = [item["agent_name"] for item in outputs] + ["audit_compliance_agent"]
        evidence_refs = [doc.document_id for doc in case.documents]
        policy_refs = [
            {
                "policy_id": item["policy_id"],
                "requirement": item["requirement"],
                "status": item["status"],
            }
            for item in policy_output.get("criteria", [])
        ]
        return {
            "agent_name": "supervisor_agent",
            "case_id": case.case_id,
            "visa_class": case.visa_application.visa_class,
            "case_state": case.workflow.current_state,
            "recommendation": recommendation,
            "confidence": confidence,
            "human_decision_required": True,
            "summary_for_officer": self._summary_for_officer(recommendation),
            "called_agents": called_agents,
            "blocking_issues": blocking_issues,
            "risk_flags": risk_flags or [],
            "policy_references": policy_refs,
            "evidence_references": evidence_refs,
            "next_action": case.workflow.next_action,
            "current_holder": case.workflow.current_holder,
            "action_required_from": case.workflow.action_required_from,
            "workflow_pack": case.workflow.workflow_pack,
            "policy_version": case.policy_context.policy_version,
            "rule_version_used": case.policy_context.effective_rule_version,
            "publication_reference": case.policy_context.publication_reference,
            "policy_source_uri": case.policy_context.source_uri,
            "official_sources": case.policy_context.official_sources,
            "verified_at": case.policy_context.verified_at,
            "manual_referral_reason": case.workflow.manual_referral_reason,
            "eta_status": case.workflow.eta_status,
            "port_clearance_state": case.workflow.port_clearance_state,
            "tool_calls": [],
        }

    def _store_agent_output(self, case: CasePacket, output: dict) -> None:
        refreshed_case = self.case_service.get_case(case.case_id)
        refreshed_case.agent_outputs[output["agent_name"]] = output
        self.case_service.save_case(refreshed_case)
        self.audit_service.write_agent_output(case.case_id, output)
        write_audit_log(case.case_id, output["agent_name"], stable_hash({"case_id": case.case_id}), output)

    def _apply_governance_context(self, case: CasePacket) -> CasePacket:
        active_rules = self.reference_service.get_active_rules()
        manifest = load_policy_manifest()
        case.policy_context.country = "Sri Lanka"
        case.policy_context.policy_version = active_rules.active_policy_version.policy_version
        case.policy_context.effective_date = active_rules.active_policy_version.effective_date
        case.policy_context.effective_rule_version = active_rules.active_policy_version.rule_version
        case.policy_context.publication_reference = active_rules.active_policy_version.publication_reference
        case.policy_context.source_uri = manifest.get("source_uri", "")
        case.policy_context.official_sources = manifest.get("official_sources", active_rules.official_sources)
        case.policy_context.verified_at = manifest.get("verified_at", active_rules.verified_at)
        case.policy_context.publication_channels = active_rules.active_circulars[0].publications
        case.workflow.workflow_pack = active_rules.workflow_pack
        return self.case_service.save_case(case)

    def _summary_for_officer(self, recommendation: str) -> str:
        if recommendation == "APPROVE_READY":
            return "The applicant passed the core checks and the case is ready for Sri Lanka officer review before any authorization is issued."
        if recommendation == "REQUEST_MORE_INFO":
            return "The case needs additional evidence, replacement documents, or governance clarification before officer review can conclude."
        if recommendation == "ENHANCED_REVIEW":
            return "The case triggered manual referral, security, document, or risk conditions that require enhanced Sri Lanka review."
        return "The case appears not to meet at least one policy requirement and a refusal draft can be prepared for officer review."

    def _brief_summary(self, output: dict) -> str:
        for key in (
            "financial_summary",
            "applicant_message",
            "eligibility_status",
            "security_status",
            "risk_band",
            "status",
        ):
            if key in output:
                return str(output[key])
        return output["agent_name"]

    def _risk_level(self, output: dict) -> str:
        if output["agent_name"] == "risk_fraud_agent":
            return output["risk_band"]
        if output["agent_name"] == "security_background_agent":
            return output["security_status"]
        return "INFO"

    def _officer_questions(self, supervisor: dict) -> list[str]:
        questions = ["Confirm that the recommendation aligns with the Sri Lanka case record, active rule pack, and local operating procedures."]
        if supervisor["manual_referral_reason"]:
            questions.append("Review whether the manual referral reason still applies and whether sponsor or head-office handling is complete.")
        if supervisor["recommendation"] == "ENHANCED_REVIEW":
            questions.append("Review highlighted risk, document, or security signals before taking legal action.")
        if supervisor["recommendation"] == "REQUEST_MORE_INFO":
            questions.append("Confirm the exact missing evidence wording before the applicant is contacted.")
        if supervisor["eta_status"] == "ETA_UNDER_OFFICER_REVIEW":
            questions.append("Remember that ETA issuance does not remove port-of-entry clearance requirements.")
        return questions
