from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from google.adk.runners import InMemoryRunner
from google.genai import types

from backend.models.schemas import CasePacket
from backend.models.schemas import SelfImprovementReviewResponse
from backend.models.schemas import SelfImprovementSuggestion
from backend.services.adk_runtime_service import AdkRuntimeService
from backend.services.audit_service import AuditService
from backend.services.case_service import CaseService
from backend.services.observability_service import ObservabilityService


class SelfImprovementService:
    def __init__(self) -> None:
        self.case_service = CaseService()
        self.audit_service = AuditService()
        self.observability_service = ObservabilityService()
        self.adk_runtime_service = AdkRuntimeService()

    def review_case(self, case_id: str) -> SelfImprovementReviewResponse | None:
        case = self.case_service.get_case(case_id)
        if not case:
            return None

        audit_events = self.case_service.list_audit_events(case_id)
        draft = self._build_deterministic_review(case, audit_events)

        adk_review = self._run_adk_review(case, audit_events, draft)
        trace_metadata = self.observability_service.record_eval_case(
            case,
            scenario_name="self_improvement_review",
            labels=["self_improvement", adk_review.runtime_mode.lower()],
            prompt_version=self.audit_service.prompt_version,
            model_version=self.audit_service.model_version,
        )

        final_review = adk_review.model_copy(
            update={
                "trace_id": trace_metadata.get("trace_id", ""),
                "observation_id": trace_metadata.get("observation_id", ""),
                "observability_export_status": trace_metadata.get("observability_export_status", "DISABLED"),
                "observability_target": trace_metadata.get("observability_target", "LOCAL_ONLY"),
                "evaluation_labels": sorted(
                    set(adk_review.evaluation_labels + trace_metadata.get("evaluation_labels", []))
                ),
            }
        )

        self.audit_service.write_event(
            case_id=case_id,
            event_type="SELF_IMPROVEMENT_REVIEW_RECORDED",
            actor_type="AGENT",
            actor_id="self_improvement_agent",
            agent_name="self_improvement_agent",
            payload=final_review.model_dump(),
            evidence_ids=list(case.agent_outputs.get("supervisor_agent", {}).get("evidence_references", [])),
            policy_ids=[
                item.get("policy_id", "")
                for item in case.agent_outputs.get("supervisor_agent", {}).get("policy_references", [])
                if isinstance(item, dict) and item.get("policy_id")
            ],
            policy_version=case.policy_context.policy_version,
            rule_version_used=case.policy_context.effective_rule_version,
            publication_reference=case.policy_context.publication_reference,
            policy_source_uri=case.policy_context.source_uri,
            recommendation=case.agent_outputs.get("supervisor_agent", {}).get("recommendation", ""),
            trace_id=final_review.trace_id,
            observation_id=final_review.observation_id,
            observability_export_status=final_review.observability_export_status,
            observability_target=final_review.observability_target,
            evaluation_labels=final_review.evaluation_labels,
        )
        return final_review

    def _run_adk_review(
        self,
        case: CasePacket,
        audit_events: list[dict[str, Any]],
        draft: SelfImprovementReviewResponse,
    ) -> SelfImprovementReviewResponse:
        runtime_status = self.adk_runtime_service.status()
        runtime_mode = "GOOGLE_ADK_GEMINI" if runtime_status.configured else "GOOGLE_ADK_MOCK"
        prompt = self._build_prompt(case, audit_events, draft)
        response_payload = {
            "failure_summary": draft.failure_summary,
            "detected_issues": draft.detected_issues,
            "proposed_changes": [item.model_dump() for item in draft.proposed_changes],
            "comparison_questions": draft.comparison_questions,
        }

        try:
            agent = self.adk_runtime_service.create_self_improvement_agent(response_payload)
            runner = InMemoryRunner(agent=agent, app_name="visaflow-self-improvement")
            events = list(
                runner.run(
                    user_id="visaflow-reviewer",
                    session_id=runner.session_service.create_session_sync(
                        app_name=runner.app_name,
                        user_id="visaflow-reviewer",
                    ).id,
                    new_message=types.Content(role="user", parts=[types.Part.from_text(text=prompt)]),
                )
            )
            payload = self._parse_runner_events(events) or response_payload
            return SelfImprovementReviewResponse(
                case_id=case.case_id,
                runtime_mode=runtime_mode,
                review_status="GENERATED",
                human_approval_required=True,
                failure_summary=str(payload.get("failure_summary", draft.failure_summary)),
                detected_issues=[str(item) for item in payload.get("detected_issues", draft.detected_issues)],
                proposed_changes=self._normalize_suggestions(payload.get("proposed_changes", response_payload["proposed_changes"])),
                comparison_questions=[str(item) for item in payload.get("comparison_questions", draft.comparison_questions)],
                source_trace_ids=draft.source_trace_ids,
                evaluation_labels=draft.evaluation_labels,
            )
        except Exception:
            return draft

    def _build_deterministic_review(
        self,
        case: CasePacket,
        audit_events: list[dict[str, Any]],
    ) -> SelfImprovementReviewResponse:
        supervisor = case.agent_outputs.get("supervisor_agent", {})
        policy = case.agent_outputs.get("policy_compliance_agent", {})
        recommendation = str(supervisor.get("recommendation", ""))
        confidence = float(supervisor.get("confidence", 0.0) or 0.0)
        issues: list[str] = []
        suggestions: list[SelfImprovementSuggestion] = []

        if not supervisor.get("policy_references"):
            issues.append("Supervisor output is missing policy citations.")
            suggestions.append(
                SelfImprovementSuggestion(
                    scope="PROMPT",
                    change="Strengthen the supervisor prompt so every recommendation must include policy IDs copied from the policy agent output.",
                    reason="Missing policy citations weakens explainability and makes evaluation failure likely.",
                    risk_level="LOW",
                )
            )
        if not supervisor.get("evidence_references"):
            issues.append("Supervisor output is missing evidence references.")
            suggestions.append(
                SelfImprovementSuggestion(
                    scope="PROMPT",
                    change="Require the supervisor and officer brief agents to include evidence IDs in every non-empty recommendation.",
                    reason="Evidence traceability is required for officer trust and legal defensibility.",
                    risk_level="LOW",
                )
            )
        if supervisor.get("human_decision_required") is not True:
            issues.append("Human decision boundary is missing from the supervisor output.")
            suggestions.append(
                SelfImprovementSuggestion(
                    scope="ROUTING",
                    change="Add a hard post-processing validator that forces human_decision_required=true before supervisor output is persisted.",
                    reason="The legal safety boundary must not depend only on prompt compliance.",
                    risk_level="LOW",
                )
            )
        if policy.get("eligibility_status") == "UNCLEAR":
            issues.append("Policy output is unclear and may benefit from stronger evidence-request routing guidance.")
            suggestions.append(
                SelfImprovementSuggestion(
                    scope="EVALUATION",
                    change="Add a regression evaluation that fails whenever unclear policy reasoning does not route to REQUEST_MORE_INFO.",
                    reason="This keeps evidence loops aligned to the deterministic routing rules.",
                    risk_level="LOW",
                )
            )
        if confidence < 0.75:
            issues.append("Supervisor confidence is weak for a legal-sensitive recommendation.")
            suggestions.append(
                SelfImprovementSuggestion(
                    scope="PROMPT",
                    change="Require the supervisor to justify low confidence with blocking issues and route more aggressively to ENHANCED_REVIEW when confidence stays low.",
                    reason="Low-confidence recommendations should be more conservative and explicit.",
                    risk_level="MEDIUM",
                )
            )

        export_failures = [
            item
            for item in audit_events
            if str(item.get("observability_export_status", "")).upper() == "FAILED"
        ]
        if export_failures:
            issues.append("Some observability exports failed while local audit continued.")
            suggestions.append(
                SelfImprovementSuggestion(
                    scope="OBSERVABILITY",
                    change="Add an evaluation check that alerts on repeated Phoenix export failures and keeps local audit as the source of truth.",
                    reason="Repeated export failures reduce debuggability even when case processing remains safe.",
                    risk_level="LOW",
                )
            )

        overrides = [item for item in audit_events if item.get("event_type") == "OFFICER_DECISION_RECORDED" and item.get("override_reason")]
        if overrides:
            issues.append("A human override was recorded and should be inspected for recurring recommendation drift.")
            suggestions.append(
                SelfImprovementSuggestion(
                    scope="EVALUATION",
                    change="Cluster override reasons and compare them against recommendation types to detect prompt or routing drift.",
                    reason="Override patterns are a strong signal for where the system needs improvement.",
                    risk_level="MEDIUM",
                )
            )

        if not issues:
            issues.append("No blocking failure was detected in the current case trace, but the review still highlights improvement opportunities.")
            suggestions.append(
                SelfImprovementSuggestion(
                    scope="EVALUATION",
                    change="Keep replaying this case in the regression suite after prompt or rule-pack changes.",
                    reason="Stable low-risk cases are useful guardrails for future changes.",
                    risk_level="LOW",
                )
            )

        summary = (
            f"Case {case.case_id} reviewed under recommendation {recommendation or 'UNKNOWN'} with "
            f"{len(issues)} improvement signal(s) detected."
        )
        source_trace_ids = sorted(
            {
                str(item.get("trace_id", "")).strip()
                for item in audit_events
                if str(item.get("trace_id", "")).strip()
            }
        )
        evaluation_labels = sorted(
            {
                str(label)
                for item in audit_events
                for label in item.get("evaluation_labels", []) or []
                if str(label).strip()
            }
        )
        return SelfImprovementReviewResponse(
            case_id=case.case_id,
            runtime_mode="DETERMINISTIC_FALLBACK",
            review_status="FALLBACK",
            human_approval_required=True,
            failure_summary=summary,
            detected_issues=issues,
            proposed_changes=suggestions,
            comparison_questions=[
                "Does the proposed change preserve deterministic routing and human_decision_required=true?",
                "Would the change improve citation completeness without increasing hallucination risk?",
                "Should this case be added to the mandatory regression suite before rollout?",
            ],
            source_trace_ids=source_trace_ids,
            evaluation_labels=evaluation_labels,
        )

    @staticmethod
    def _normalize_suggestions(items: list[dict[str, Any]] | list[SelfImprovementSuggestion]) -> list[SelfImprovementSuggestion]:
        normalized: list[SelfImprovementSuggestion] = []
        for item in items:
            if isinstance(item, SelfImprovementSuggestion):
                normalized.append(item)
                continue
            scope = str(item.get("scope", "PROMPT")).upper()
            if scope not in {"PROMPT", "ROUTING", "EVALUATION", "OBSERVABILITY"}:
                scope = "PROMPT"
            risk_level = str(item.get("risk_level", "LOW")).upper()
            if risk_level not in {"LOW", "MEDIUM", "HIGH"}:
                risk_level = "LOW"
            normalized.append(
                SelfImprovementSuggestion(
                    scope=scope,
                    change=str(item.get("change", "")),
                    reason=str(item.get("reason", "")),
                    risk_level=risk_level,
                )
            )
        return normalized

    @staticmethod
    def _build_prompt(case: CasePacket, audit_events: list[dict[str, Any]], draft: SelfImprovementReviewResponse) -> str:
        supervisor = case.agent_outputs.get("supervisor_agent", {})
        payload = {
            "case_id": case.case_id,
            "recommendation": supervisor.get("recommendation", ""),
            "confidence": supervisor.get("confidence", 0.0),
            "human_decision_required": supervisor.get("human_decision_required", True),
            "evaluation_labels": draft.evaluation_labels,
            "detected_issues": draft.detected_issues,
            "audit_event_types": [item.get("event_type", "") for item in audit_events],
            "source_trace_ids": draft.source_trace_ids,
        }
        return (
            "Review this visa-case trace and propose safe human-approved improvements.\n"
            "Return JSON only.\n\n"
            f"{json.dumps(payload, indent=2, sort_keys=True)}"
        )

    @staticmethod
    def _parse_runner_events(events: list[Any]) -> dict[str, Any] | None:
        for event in reversed(events):
            content = getattr(event, "content", None)
            parts = getattr(content, "parts", None) or []
            for part in parts:
                text = getattr(part, "text", None)
                if text:
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        continue
        return None
