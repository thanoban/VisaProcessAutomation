from fastapi import APIRouter, HTTPException, status

from backend.models.schemas import (
    ApplicantMessageResponse,
    ApplicationCreateRequest,
    AuthorizationStatusResponse,
    CasePacket,
    CaseStatusResponse,
    ChecklistResponse,
    DocumentUploadRequest,
    GovernanceRulesResponse,
    OfficerBrief,
    OfficerDecisionRequest,
    PolicyRequirementsResponse,
    SupervisorQueueSummary,
    SystemNotice,
)
from backend.services.case_service import CaseService
from backend.services.sri_lanka_reference_service import SriLankaReferenceService
from backend.workflows.tourist_visa_workflow import TouristVisaWorkflow

router = APIRouter()
case_service = CaseService()
workflow = TouristVisaWorkflow()
sri_lanka_reference = SriLankaReferenceService()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "visaflow-mas"}


@router.get("/system/notices", response_model=list[SystemNotice])
def get_system_notices() -> list[SystemNotice]:
    return [
        SystemNotice(
            code="SCHEDULED_MAINTENANCE",
            message="Document processing sandbox maintenance window is mock-configured for the PoC.",
            level="INFO",
        )
    ]


@router.post("/applications", response_model=CasePacket, status_code=status.HTTP_201_CREATED)
def create_application(payload: ApplicationCreateRequest) -> CasePacket:
    return case_service.create_case(payload)


@router.post("/cases/{case_id}/documents", response_model=CasePacket)
def upload_documents(case_id: str, payload: DocumentUploadRequest) -> CasePacket:
    case = case_service.add_documents(case_id, payload.documents)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/cases/{case_id}/process")
def process_case(case_id: str) -> dict:
    result = workflow.process_case(case_id)
    if not result:
        raise HTTPException(status_code=404, detail="Case not found")
    return result


@router.get("/cases/{case_id}", response_model=CasePacket)
def get_case(case_id: str) -> CasePacket:
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.get("/cases/{case_id}/status", response_model=CaseStatusResponse)
def get_case_status(case_id: str) -> CaseStatusResponse:
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case_service.get_case_status(case)


@router.get("/cases/{case_id}/timeline")
def get_case_timeline(case_id: str) -> list[dict]:
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case_service.get_case_timeline(case)


@router.get("/cases/{case_id}/authorization-status", response_model=AuthorizationStatusResponse)
def get_authorization_status(case_id: str) -> AuthorizationStatusResponse:
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return AuthorizationStatusResponse(
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


@router.get("/cases/{case_id}/officer-brief", response_model=OfficerBrief)
def get_officer_brief(case_id: str) -> OfficerBrief:
    brief = case_service.get_officer_brief(case_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Officer brief not found")
    return brief


@router.get("/cases/{case_id}/audit")
def get_audit(case_id: str) -> list[dict]:
    return case_service.list_audit_events(case_id)


@router.post("/cases/{case_id}/officer-decision")
def submit_officer_decision(case_id: str, payload: OfficerDecisionRequest) -> dict:
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return workflow.submit_officer_decision(case_id, payload)


@router.post("/cases/{case_id}/messages", response_model=ApplicantMessageResponse)
def send_message(case_id: str) -> ApplicantMessageResponse:
    message = workflow.send_applicant_message(case_id)
    if not message:
        raise HTTPException(status_code=404, detail="Case not found")
    return message


@router.get("/policies/{visa_class}/requirements", response_model=PolicyRequirementsResponse)
def get_policy_requirements(visa_class: str) -> PolicyRequirementsResponse:
    return workflow.get_policy_requirements(visa_class)


@router.get("/checklists/tourist-visit", response_model=ChecklistResponse)
def get_tourist_visit_checklist() -> ChecklistResponse:
    return sri_lanka_reference.get_tourist_checklist()


@router.get("/governance/rules/active", response_model=GovernanceRulesResponse)
def get_active_governance_rules() -> GovernanceRulesResponse:
    return sri_lanka_reference.get_active_rules()


@router.get("/supervisor/queues", response_model=SupervisorQueueSummary)
def get_supervisor_queues() -> SupervisorQueueSummary:
    return sri_lanka_reference.build_queue_summary(case_service.list_cases())
