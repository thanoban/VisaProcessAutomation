from backend.models.schemas import AuditInfo, CaseTimelineEvent, DecisionNotice
from backend.services.utils import utc_now, utc_now_datetime


def test_utc_helpers_and_schema_defaults_emit_explicit_utc_values():
    assert utc_now().endswith("Z")
    assert utc_now_datetime().tzinfo is not None

    timeline_event = CaseTimelineEvent(state="UNDER_PRECHECK", actor="SYSTEM")
    audit_info = AuditInfo()
    notice = DecisionNotice(message_type="STATUS_UPDATE", subject="Case update", summary="Under review")

    assert timeline_event.timestamp.endswith("Z")
    assert audit_info.created_at.endswith("Z")
    assert audit_info.updated_at.endswith("Z")
    assert notice.issued_at.endswith("Z")
