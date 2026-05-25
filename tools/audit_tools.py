from __future__ import annotations

from backend.services.audit_service import AuditService

audit_service = AuditService()


def write_audit_log(case_id: str, agent_name: str, input_hash: str, output_json: dict) -> dict:
    return audit_service.write_event(
        case_id=case_id,
        event_type="AGENT_OUTPUT_RECORDED",
        actor_type="AGENT",
        actor_id=agent_name,
        payload=output_json,
        agent_name=agent_name,
        recommendation=output_json.get("recommendation", ""),
        evidence_ids=output_json.get("evidence_references", output_json.get("evidence_ids", [])),
        policy_ids=output_json.get("policy_references", output_json.get("policy_ids", [])),
    )
