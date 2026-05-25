from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


Recommendation = Literal["APPROVE_READY", "REQUEST_MORE_INFO", "ENHANCED_REVIEW", "REFUSAL_DRAFT_READY"]
OfficerDecision = Literal["APPROVE", "REJECT", "REQUEST_MORE_INFO", "ESCALATE"]


class Applicant(BaseModel):
    full_name: str
    date_of_birth: str
    nationality: str
    passport_number: str
    contact_email: str
    phone: str | None = None


class VisaApplication(BaseModel):
    visa_class: str = "TOURIST"
    purpose_of_travel: str
    arrival_date: str
    departure_date: str
    sponsor: str | None = None
    destination_address: str | None = None
    country_of_application: str = "UNSPECIFIED"
    payment_status: str = "PAID"


class DocumentItem(BaseModel):
    document_id: str
    document_type: str
    file_uri: str
    uploaded_at: str | None = None
    status: Literal["UPLOADED", "PROCESSED", "INVALID"] = "UPLOADED"


class PolicyContext(BaseModel):
    country: str = "UNSPECIFIED"
    policy_version: str = "tourist-policy-v1"
    effective_date: str = "2026-01-01"


class WorkflowState(BaseModel):
    current_state: str = "SUBMITTED"
    previous_states: list[str] = Field(default_factory=list)
    assigned_officer: str | None = None
    sla_deadline: str | None = None


class AuditInfo(BaseModel):
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    workflow_version: str = "v1.0"


class AgentEnvelope(BaseModel):
    agent_name: str
    case_id: str
    status: str
    summary: str
    findings: list[Any] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    policy_ids: list[str] = Field(default_factory=list)
    confidence: float
    requires_human_review: bool = True
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    details: dict[str, Any] = Field(default_factory=dict)


class OfficerBriefAgentResult(BaseModel):
    agent_name: str
    status: str
    summary: str
    risk_level: str = "INFO"


class OfficerBrief(BaseModel):
    case_id: str
    visa_class: str
    applicant_summary: str
    recommendation: Recommendation
    confidence: float
    human_decision_required: bool = True
    agent_results: list[OfficerBriefAgentResult]
    key_evidence: list[str]
    policy_references: list[dict[str, Any]]
    risk_flags: list[str]
    missing_items: list[str]
    questions_for_officer: list[str]
    final_decision_options: list[OfficerDecision] = Field(
        default_factory=lambda: ["APPROVE", "REJECT", "REQUEST_MORE_INFO", "ESCALATE"]
    )
    recommendation_panel: dict[str, Any] = Field(default_factory=dict)
    evidence_viewer: dict[str, Any] = Field(default_factory=dict)
    audit_timeline: list[dict[str, Any]] = Field(default_factory=list)


class AuditEvent(BaseModel):
    audit_id: str
    case_id: str
    timestamp: str
    event_type: str
    actor_type: Literal["AGENT", "OFFICER", "SYSTEM", "APPLICANT"]
    actor_id: str
    agent_name: str | None = None
    prompt_version: str = ""
    model_version: str = ""
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    input_hash: str = ""
    output_hash: str = ""
    evidence_ids: list[str] = Field(default_factory=list)
    policy_ids: list[str] = Field(default_factory=list)
    recommendation: str = ""
    human_action: str = ""
    override_reason: str = ""
    ip_address: str = ""
    session_id: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)


class CasePacket(BaseModel):
    case_id: str
    applicant: Applicant
    visa_application: VisaApplication
    documents: list[DocumentItem]
    policy_context: PolicyContext = Field(default_factory=PolicyContext)
    agent_outputs: dict[str, Any] = Field(default_factory=dict)
    workflow: WorkflowState = Field(default_factory=WorkflowState)
    audit: AuditInfo = Field(default_factory=AuditInfo)
    submission_channel: str = "ONLINE_PORTAL"
    status_timeline: list[dict[str, Any]] = Field(default_factory=list)
    applicant_message_history: list[dict[str, Any]] = Field(default_factory=list)
    security_handling_code: str = "STANDARD"
    decision_due_at: str | None = None
    override_required: bool = False
    retention_class: str = "STANDARD_VISA"
    mock_profile: dict[str, Any] = Field(default_factory=dict)


class ApplicationCreateRequest(BaseModel):
    case_id: str
    applicant: Applicant
    visa_application: VisaApplication
    documents: list[DocumentItem] = Field(default_factory=list)
    policy_context: PolicyContext = Field(default_factory=PolicyContext)
    submission_channel: str = "ONLINE_PORTAL"
    decision_due_at: str | None = None
    retention_class: str = "STANDARD_VISA"
    mock_profile: dict[str, Any] = Field(default_factory=dict)


class DocumentUploadRequest(BaseModel):
    documents: list[DocumentItem]


class ApplicantMessageResponse(BaseModel):
    message_type: str
    subject: str
    message: str
    required_actions: list[str] = Field(default_factory=list)
    deadline: str = ""


class CaseStatusResponse(BaseModel):
    case_id: str
    status: str
    latest_message: dict[str, Any] | None = None
    required_actions: list[str] = Field(default_factory=list)
    uploaded_documents: list[dict[str, Any]] = Field(default_factory=list)
    deadlines: dict[str, Any] = Field(default_factory=dict)
    service_notices: list[dict[str, Any]] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)


class OfficerDecisionRequest(BaseModel):
    decision: OfficerDecision
    officer_id: str
    reason: str
    override_reason: str = ""


class SystemNotice(BaseModel):
    code: str
    message: str
    level: str


class PolicyRequirementsResponse(BaseModel):
    visa_class: str
    policy_version: str
    requirements: list[dict[str, Any]]
