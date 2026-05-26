from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text

from backend.database.base import Base
from backend.services.utils import utc_now_datetime


class CaseRecord(Base):
    __tablename__ = "cases"

    case_id = Column(String, primary_key=True)
    applicant = Column(JSON, nullable=False)
    visa_application = Column(JSON, nullable=False)
    documents = Column(JSON, nullable=False, default=list)
    policy_context = Column(JSON, nullable=False)
    agent_outputs = Column(JSON, nullable=False, default=dict)
    workflow = Column(JSON, nullable=False)
    audit = Column(JSON, nullable=False)
    submission_channel = Column(String, nullable=False, default="ONLINE_PORTAL")
    status_timeline = Column(JSON, nullable=False, default=list)
    applicant_message_history = Column(JSON, nullable=False, default=list)
    security_handling_code = Column(String, nullable=False, default="STANDARD")
    decision_due_at = Column(String, nullable=True)
    override_required = Column(Boolean, nullable=False, default=False)
    retention_class = Column(String, nullable=False, default="STANDARD_VISA")
    mock_profile = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now_datetime, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now_datetime, onupdate=utc_now_datetime, nullable=False)


class DocumentExtractionRecord(Base):
    __tablename__ = "document_extractions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, nullable=False, index=True)
    document_id = Column(String, nullable=False)
    extraction = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now_datetime, nullable=False)


class AgentRunRecord(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, nullable=False, index=True)
    agent_name = Column(String, nullable=False)
    prompt_version = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    input_hash = Column(String, nullable=False)
    output_hash = Column(String, nullable=False)
    tool_calls = Column(JSON, nullable=False, default=list)
    evidence_ids = Column(JSON, nullable=False, default=list)
    policy_ids = Column(JSON, nullable=False, default=list)
    policy_version = Column(String, nullable=False, default="")
    rule_version_used = Column(String, nullable=False, default="")
    publication_reference = Column(String, nullable=False, default="")
    policy_source_uri = Column(String, nullable=False, default="")
    trace_id = Column(String, nullable=False, default="")
    observation_id = Column(String, nullable=False, default="")
    observability_export_status = Column(String, nullable=False, default="DISABLED")
    observability_target = Column(String, nullable=False, default="LOCAL_ONLY")
    evaluation_labels = Column(JSON, nullable=False, default=list)
    output_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now_datetime, nullable=False)


class AgentOutputRecord(Base):
    __tablename__ = "agent_outputs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, nullable=False, index=True)
    agent_name = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now_datetime, nullable=False)


class OfficerBriefRecord(Base):
    __tablename__ = "officer_briefs"

    case_id = Column(String, primary_key=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now_datetime, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now_datetime, onupdate=utc_now_datetime, nullable=False)


class AuditEventRecord(Base):
    __tablename__ = "audit_events"

    audit_id = Column(String, primary_key=True)
    case_id = Column(String, nullable=False, index=True)
    timestamp = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    actor_type = Column(String, nullable=False)
    actor_id = Column(String, nullable=False)
    agent_name = Column(String, nullable=True)
    prompt_version = Column(String, nullable=False, default="")
    model_version = Column(String, nullable=False, default="")
    tool_calls = Column(JSON, nullable=False, default=list)
    input_hash = Column(String, nullable=False, default="")
    output_hash = Column(String, nullable=False, default="")
    evidence_ids = Column(JSON, nullable=False, default=list)
    policy_ids = Column(JSON, nullable=False, default=list)
    policy_version = Column(String, nullable=False, default="")
    rule_version_used = Column(String, nullable=False, default="")
    publication_reference = Column(String, nullable=False, default="")
    policy_source_uri = Column(String, nullable=False, default="")
    recommendation = Column(String, nullable=False, default="")
    human_action = Column(String, nullable=False, default="")
    override_reason = Column(Text, nullable=False, default="")
    ip_address = Column(String, nullable=False, default="")
    session_id = Column(String, nullable=False, default="")
    trace_id = Column(String, nullable=False, default="")
    observation_id = Column(String, nullable=False, default="")
    observability_export_status = Column(String, nullable=False, default="DISABLED")
    observability_target = Column(String, nullable=False, default="LOCAL_ONLY")
    evaluation_labels = Column(JSON, nullable=False, default=list)
    payload = Column(JSON, nullable=False, default=dict)


class OfficerDecisionRecord(Base):
    __tablename__ = "officer_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, nullable=False, index=True)
    decision = Column(String, nullable=False)
    officer_id = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    override_reason = Column(Text, nullable=False, default="")
    created_at = Column(DateTime(timezone=True), default=utc_now_datetime, nullable=False)


class PolicySnapshotRecord(Base):
    __tablename__ = "policy_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    visa_class = Column(String, nullable=False)
    version = Column(String, nullable=False)
    effective_date = Column(String, nullable=False)
    source_uri = Column(String, nullable=False)
    sections = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now_datetime, nullable=False)


class NotificationRecord(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, nullable=False, index=True)
    channel = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now_datetime, nullable=False)
