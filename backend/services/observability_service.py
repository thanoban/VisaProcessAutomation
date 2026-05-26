from __future__ import annotations

import json
import os
import threading
from typing import Any

from backend.models.schemas import CasePacket, ObservabilityStatusResponse
from backend.services.utils import stable_hash


class ObservabilityService:
    _runtime_lock = threading.Lock()
    _runtime_ready = False
    _runtime_error = ""
    _instrumentation_ready = False

    def __init__(self) -> None:
        self.enabled = os.getenv("VISAFLOW_OBSERVABILITY_ENABLED", "0") == "1"
        self.target = os.getenv("VISAFLOW_OBSERVABILITY_TARGET", "LOCAL_ONLY").strip().upper() or "LOCAL_ONLY"
        self.project_name = os.getenv("PHOENIX_PROJECT_NAME", "visaflow-mas")
        self.provider = "Phoenix"
        self.google_genai_instrumentation_enabled = (
            os.getenv("VISAFLOW_ENABLE_GOOGLE_GENAI_INSTRUMENTATION", "0") == "1"
        )

    def status(self) -> ObservabilityStatusResponse:
        if not self.enabled:
            return ObservabilityStatusResponse(
                enabled=False,
                target=self.target,
                project_name=self.project_name,
                provider=self.provider,
                google_genai_instrumentation_enabled=self.google_genai_instrumentation_enabled,
                status="DISABLED",
            )
        if not self._runtime_ready and not self._runtime_error:
            self._ensure_runtime()
        if self._runtime_ready:
            return ObservabilityStatusResponse(
                enabled=True,
                target=self.target,
                project_name=self.project_name,
                provider=self.provider,
                google_genai_instrumentation_enabled=self.google_genai_instrumentation_enabled,
                status="READY",
            )
        if self._runtime_error:
            return ObservabilityStatusResponse(
                enabled=True,
                target=self.target,
                project_name=self.project_name,
                provider=self.provider,
                google_genai_instrumentation_enabled=self.google_genai_instrumentation_enabled,
                status="DEGRADED",
            )
        return ObservabilityStatusResponse(
            enabled=True,
            target=self.target,
            project_name=self.project_name,
            provider=self.provider,
            google_genai_instrumentation_enabled=self.google_genai_instrumentation_enabled,
            status="PENDING",
        )

    def record_agent_run(
        self,
        case: CasePacket,
        output: dict[str, Any],
        *,
        prompt_version: str,
        model_version: str,
    ) -> dict[str, Any]:
        return self._record_span(
            span_name=f"visaflow.agent.{output.get('agent_name', 'unknown')}",
            case=case,
            payload=output,
            prompt_version=prompt_version,
            model_version=model_version,
            record_type="agent_run",
            recommendation=str(output.get("recommendation", "")),
            human_action="",
        )

    def record_workflow_outcome(
        self,
        case: CasePacket,
        payload: dict[str, Any],
        *,
        prompt_version: str,
        model_version: str,
    ) -> dict[str, Any]:
        return self._record_span(
            span_name="visaflow.workflow.outcome",
            case=case,
            payload=payload,
            prompt_version=prompt_version,
            model_version=model_version,
            record_type="workflow_outcome",
            recommendation=str(payload.get("recommendation", "")),
            human_action="",
        )

    def record_human_decision(
        self,
        case: CasePacket,
        payload: dict[str, Any],
        *,
        recommendation: str,
        prompt_version: str,
        model_version: str,
    ) -> dict[str, Any]:
        return self._record_span(
            span_name="visaflow.human.decision",
            case=case,
            payload=payload,
            prompt_version=prompt_version,
            model_version=model_version,
            record_type="human_decision",
            recommendation=recommendation,
            human_action=str(payload.get("decision", "")),
        )

    def record_eval_case(
        self,
        case: CasePacket,
        *,
        scenario_name: str,
        labels: list[str] | None = None,
        prompt_version: str,
        model_version: str,
    ) -> dict[str, Any]:
        return self._record_span(
            span_name="visaflow.eval.case",
            case=case,
            payload={"scenario_name": scenario_name},
            prompt_version=prompt_version,
            model_version=model_version,
            record_type="eval_case",
            recommendation="",
            human_action="",
            extra_labels=labels or [],
        )

    def prepare_export_payload(self, case: CasePacket, payload: dict[str, Any], record_type: str) -> dict[str, Any]:
        redacted_payload = self._redact_payload(payload)
        return {
            "case_id": case.case_id,
            "workflow_pack": case.workflow.workflow_pack,
            "current_state": case.workflow.current_state,
            "current_holder": case.workflow.current_holder,
            "policy_version": case.policy_context.policy_version,
            "rule_version_used": case.policy_context.effective_rule_version,
            "publication_reference": case.policy_context.publication_reference,
            "record_type": record_type,
            "payload": redacted_payload,
        }

    def _record_span(
        self,
        *,
        span_name: str,
        case: CasePacket,
        payload: dict[str, Any],
        prompt_version: str,
        model_version: str,
        record_type: str,
        recommendation: str,
        human_action: str,
        extra_labels: list[str] | None = None,
    ) -> dict[str, Any]:
        export_payload = self.prepare_export_payload(case, payload, record_type)
        evaluation_labels = self._build_evaluation_labels(
            case=case,
            payload=payload,
            recommendation=recommendation,
            human_action=human_action,
            extra_labels=extra_labels or [],
        )
        local_trace_seed = stable_hash(
            {
                "case_id": case.case_id,
                "record_type": record_type,
                "span_name": span_name,
                "payload": export_payload,
                "recommendation": recommendation,
                "human_action": human_action,
            }
        )
        metadata = {
            "trace_id": local_trace_seed[:32],
            "observation_id": local_trace_seed[:16],
            "observability_export_status": "DISABLED" if not self.enabled else "PENDING",
            "observability_target": self.target,
            "evaluation_labels": evaluation_labels,
            "observability_redaction_applied": True,
            "observability_redacted_fields": self._collect_redacted_fields(payload),
        }

        if not self.enabled:
            return metadata

        try:
            tracer = self._get_tracer()
            if tracer is None:
                metadata["observability_export_status"] = "UNAVAILABLE"
                return metadata

            with tracer.start_as_current_span(span_name) as span:
                span_context = span.get_span_context()
                metadata["trace_id"] = format(span_context.trace_id, "032x")
                metadata["observation_id"] = format(span_context.span_id, "016x")
                span.set_attribute("visaflow.case_id", case.case_id)
                span.set_attribute("visaflow.workflow_pack", case.workflow.workflow_pack)
                span.set_attribute("visaflow.current_state", case.workflow.current_state)
                span.set_attribute("visaflow.current_holder", case.workflow.current_holder)
                span.set_attribute("visaflow.record_type", record_type)
                span.set_attribute("visaflow.prompt_version", prompt_version)
                span.set_attribute("visaflow.model_version", model_version)
                span.set_attribute("visaflow.policy_version", case.policy_context.policy_version)
                span.set_attribute("visaflow.rule_version_used", case.policy_context.effective_rule_version)
                span.set_attribute("visaflow.publication_reference", case.policy_context.publication_reference)
                span.set_attribute("visaflow.recommendation", recommendation or "")
                span.set_attribute("visaflow.human_action", human_action or "")
                span.set_attribute("visaflow.evaluation_labels", json.dumps(evaluation_labels))
                span.set_attribute("visaflow.redacted_fields", json.dumps(metadata["observability_redacted_fields"]))
                span.set_attribute("visaflow.payload_hash", stable_hash(export_payload))
                span.add_event(
                    "visaflow.redacted_payload",
                    {"json": json.dumps(export_payload, sort_keys=True, default=str)[:8000]},
                )
                metadata["observability_export_status"] = "EXPORTED"
        except Exception as exc:  # pragma: no cover - exact exporter failures are environment-specific
            self._runtime_error = str(exc)
            metadata["observability_export_status"] = "FAILED"
        return metadata

    def _get_tracer(self):
        if not self.enabled:
            return None
        self._ensure_runtime()
        if not self._runtime_ready:
            return None
        from opentelemetry import trace

        return trace.get_tracer("visaflow.observability")

    def _ensure_runtime(self) -> None:
        if self._runtime_ready:
            return
        with self._runtime_lock:
            if self._runtime_ready:
                return
            try:
                from phoenix.otel import register

                register(project_name=self.project_name)
                if self.google_genai_instrumentation_enabled and not self._instrumentation_ready:
                    from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor

                    GoogleGenAIInstrumentor().instrument()
                    self._instrumentation_ready = True
                self._runtime_ready = True
                self._runtime_error = ""
            except Exception as exc:  # pragma: no cover - env/package-dependent
                self._runtime_ready = False
                self._runtime_error = str(exc)

    def _build_evaluation_labels(
        self,
        *,
        case: CasePacket,
        payload: dict[str, Any],
        recommendation: str,
        human_action: str,
        extra_labels: list[str],
    ) -> list[str]:
        labels = {
            f"workflow_pack:{case.workflow.workflow_pack}",
            f"state:{case.workflow.current_state}",
        }
        if recommendation:
            labels.add(f"recommendation:{recommendation}")
        if human_action:
            labels.add(f"human_action:{human_action}")
        labels.update(f"scenario:{label}" for label in self._scenario_labels(case, payload))
        labels.update(extra_labels)
        return sorted(labels)

    def _scenario_labels(self, case: CasePacket, payload: dict[str, Any]) -> list[str]:
        labels: list[str] = []
        mock_profile = case.mock_profile or {}
        if mock_profile.get("requires_manual_referral") or case.workflow.manual_referral_reason:
            labels.append("manual_referral")
        if mock_profile.get("force_invalid_upload"):
            labels.append("unreadable_upload")
        if mock_profile.get("unofficial_payment_reference"):
            labels.append("unofficial_payment_reference")
        if mock_profile.get("security_status") == "SYSTEM_UNAVAILABLE":
            labels.append("security_unavailable")
        if case.workflow.extension_state != "NOT_REQUESTED":
            labels.append("extension_workflow")
        if payload.get("missing_items"):
            labels.append("missing_documents")
        if payload.get("identity_mismatches"):
            labels.append("identity_mismatch")
        if payload.get("suspicious_patterns") or payload.get("fraud_indicators"):
            labels.append("fraud_or_financial_anomaly")
        if payload.get("recommendation") == "APPROVE_READY":
            labels.append("low_risk_ready")
        return sorted(set(labels))

    def _collect_redacted_fields(self, payload: Any, prefix: str = "") -> list[str]:
        sensitive_keys = self._sensitive_keys()
        fields: list[str] = []
        if isinstance(payload, dict):
            for key, value in payload.items():
                path = f"{prefix}.{key}" if prefix else str(key)
                if key in sensitive_keys:
                    fields.append(path)
                fields.extend(self._collect_redacted_fields(value, path))
        elif isinstance(payload, list):
            for index, value in enumerate(payload):
                path = f"{prefix}[{index}]"
                fields.extend(self._collect_redacted_fields(value, path))
        return sorted(set(fields))

    def _redact_payload(self, payload: Any) -> Any:
        sensitive_keys = self._sensitive_keys()
        if isinstance(payload, dict):
            return {
                key: ("[REDACTED]" if key in sensitive_keys else self._redact_payload(value))
                for key, value in payload.items()
            }
        if isinstance(payload, list):
            return [self._redact_payload(value) for value in payload]
        return payload

    @staticmethod
    def _sensitive_keys() -> set[str]:
        return {
            "full_name",
            "date_of_birth",
            "passport_number",
            "contact_email",
            "phone",
            "file_uri",
            "destination_address",
            "supporting_note",
            "watchlist_details",
            "classified_data",
            "raw_security_payload",
            "raw_watchlist_payload",
        }
