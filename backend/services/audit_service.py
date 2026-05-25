from __future__ import annotations

import uuid

from sqlalchemy import insert

from backend.database.session import SessionLocal
from backend.models.db import AuditEventRecord, AgentOutputRecord, AgentRunRecord
from backend.models.schemas import AuditEvent
from backend.services.utils import stable_hash, utc_now


class AuditService:
    prompt_version = "visaflow-prompts-v1"
    model_version = "gemini-mock-poc-v1"

    @staticmethod
    def _normalize_ids(values: list | None, key: str) -> list[str]:
        normalized: list[str] = []
        for value in values or []:
            if isinstance(value, str):
                normalized.append(value)
            elif isinstance(value, dict) and key in value and isinstance(value[key], str):
                normalized.append(value[key])
        return normalized

    @staticmethod
    def _policy_value(payload: dict, *keys: str) -> str:
        for key in keys:
            value = payload.get(key, "")
            if isinstance(value, str):
                return value
        return ""

    def write_event(
        self,
        *,
        case_id: str,
        event_type: str,
        actor_type: str,
        actor_id: str,
        payload: dict,
        agent_name: str | None = None,
        tool_calls: list[dict] | None = None,
        evidence_ids: list[str] | None = None,
        policy_ids: list[str] | None = None,
        policy_version: str = "",
        rule_version_used: str = "",
        publication_reference: str = "",
        policy_source_uri: str = "",
        recommendation: str = "",
        human_action: str = "",
        override_reason: str = "",
    ) -> dict:
        resolved_policy_version = policy_version or self._policy_value(payload, "policy_version")
        resolved_rule_version = rule_version_used or self._policy_value(payload, "rule_version_used")
        resolved_publication_reference = publication_reference or self._policy_value(payload, "publication_reference")
        resolved_policy_source_uri = policy_source_uri or self._policy_value(payload, "policy_source_uri", "source_uri")
        event = AuditEvent(
            audit_id=f"AUD-{uuid.uuid4()}",
            case_id=case_id,
            timestamp=utc_now(),
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            agent_name=agent_name,
            prompt_version=self.prompt_version if agent_name else "",
            model_version=self.model_version if agent_name else "",
            tool_calls=tool_calls or [],
            input_hash=stable_hash({"case_id": case_id, "event_type": event_type, "agent_name": agent_name}),
            output_hash=stable_hash(payload),
            evidence_ids=self._normalize_ids(evidence_ids, "evidence_id"),
            policy_ids=self._normalize_ids(policy_ids, "policy_id"),
            policy_version=resolved_policy_version,
            rule_version_used=resolved_rule_version,
            publication_reference=resolved_publication_reference,
            policy_source_uri=resolved_policy_source_uri,
            recommendation=recommendation,
            human_action=human_action,
            override_reason=override_reason,
            payload=payload,
        )
        with SessionLocal() as session:
            session.execute(
                insert(AuditEventRecord).values(
                    audit_id=event.audit_id,
                    case_id=event.case_id,
                    timestamp=event.timestamp,
                    event_type=event.event_type,
                    actor_type=event.actor_type,
                    actor_id=event.actor_id,
                    agent_name=event.agent_name,
                    prompt_version=event.prompt_version,
                    model_version=event.model_version,
                    tool_calls=event.tool_calls,
                    input_hash=event.input_hash,
                    output_hash=event.output_hash,
                    evidence_ids=event.evidence_ids,
                    policy_ids=event.policy_ids,
                    policy_version=event.policy_version,
                    rule_version_used=event.rule_version_used,
                    publication_reference=event.publication_reference,
                    policy_source_uri=event.policy_source_uri,
                    recommendation=event.recommendation,
                    human_action=event.human_action,
                    override_reason=event.override_reason,
                    ip_address=event.ip_address,
                    session_id=event.session_id,
                    payload=event.model_dump(),
                )
            )
            session.commit()
        return event.model_dump()

    def write_agent_output(self, case_id: str, output: dict) -> None:
        with SessionLocal() as session:
            session.add(AgentOutputRecord(case_id=case_id, agent_name=output["agent_name"], payload=output))
            session.add(
                AgentRunRecord(
                    case_id=case_id,
                    agent_name=output["agent_name"],
                    prompt_version=self.prompt_version,
                    model_version=self.model_version,
                    input_hash=stable_hash({"case_id": case_id, "agent_name": output["agent_name"]}),
                    output_hash=stable_hash(output),
                    tool_calls=output.get("tool_calls", []),
                    evidence_ids=self._normalize_ids(
                        output.get("evidence_ids", output.get("evidence_references", [])),
                        "evidence_id",
                    ),
                    policy_ids=self._normalize_ids(
                        output.get("policy_ids", output.get("policy_references", [])),
                        "policy_id",
                    ),
                    policy_version=self._policy_value(output, "policy_version"),
                    rule_version_used=self._policy_value(output, "rule_version_used"),
                    publication_reference=self._policy_value(output, "publication_reference"),
                    policy_source_uri=self._policy_value(output, "policy_source_uri", "source_uri"),
                    output_json=output,
                )
            )
            session.commit()
