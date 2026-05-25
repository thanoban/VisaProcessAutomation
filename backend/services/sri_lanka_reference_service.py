from __future__ import annotations

from backend.models.schemas import (
    CasePacket,
    ChecklistResponse,
    GovernanceRulesResponse,
    NationalityExceptionRule,
    SupervisorCaseListResponse,
    SupervisorCaseSummary,
    SupervisorQueueSummary,
)
from backend.services.policy_service import load_reference_json


class SriLankaReferenceService:
    workflow_pack = "SRI_LANKA_TOURIST_VISIT"

    def get_tourist_checklist(self) -> ChecklistResponse:
        return ChecklistResponse.model_validate(load_reference_json("sri_lanka_tourist_visit_checklist.json"))

    def get_active_rules(self) -> GovernanceRulesResponse:
        return GovernanceRulesResponse.model_validate(load_reference_json("sri_lanka_active_rules.json"))

    def find_exception_rule(self, case: CasePacket) -> NationalityExceptionRule | None:
        if case.mock_profile.get("requires_manual_referral"):
            return NationalityExceptionRule(
                rule_id="SL-MOCK-REFERRAL",
                nationality=case.applicant.nationality.upper(),
                requires_sponsor=bool(case.mock_profile.get("requires_sponsor", False)),
                reason=case.mock_profile.get(
                    "manual_referral_reason",
                    "Mock manual referral was triggered for this Sri Lanka workflow scenario.",
                ),
            )
        nationality = case.applicant.nationality.strip().upper()
        for rule in self.get_active_rules().nationality_exception_rules:
            if nationality == rule.nationality:
                return rule
        return None

    def build_queue_summary(self, cases: list[CasePacket]) -> SupervisorQueueSummary:
        counts_by_state: dict[str, int] = {}
        manual_referrals = 0
        waiting_for_documents = 0
        ready_for_officer_review = 0
        for case in cases:
            state = case.workflow.current_state
            counts_by_state[state] = counts_by_state.get(state, 0) + 1
            if state == "REFERRED_TO_MANUAL_REVIEW":
                manual_referrals += 1
            if state == "WAITING_FOR_DOCUMENTS":
                waiting_for_documents += 1
            if state == "READY_FOR_OFFICER_REVIEW":
                ready_for_officer_review += 1
        return SupervisorQueueSummary(
            workflow_pack=self.workflow_pack,
            counts_by_state=counts_by_state,
            manual_referrals=manual_referrals,
            waiting_for_documents=waiting_for_documents,
            ready_for_officer_review=ready_for_officer_review,
        )

    def build_supervisor_case_list(
        self,
        cases: list[CasePacket],
        *,
        state_filter: str = "",
        holder_filter: str = "",
    ) -> SupervisorCaseListResponse:
        normalized_state = state_filter.strip().upper()
        normalized_holder = holder_filter.strip().upper()

        filtered_cases = []
        for case in cases:
            if normalized_state and case.workflow.current_state != normalized_state:
                continue
            if normalized_holder and case.workflow.current_holder != normalized_holder:
                continue
            filtered_cases.append(case)

        summaries = [
            SupervisorCaseSummary(
                case_id=case.case_id,
                applicant_name=case.applicant.full_name,
                nationality=case.applicant.nationality,
                visa_class=case.visa_application.visa_class,
                current_state=case.workflow.current_state,
                current_holder=case.workflow.current_holder,
                next_action=case.workflow.next_action,
                action_required_from=case.workflow.action_required_from,
                eta_status=case.workflow.eta_status,
                manual_referral_reason=case.workflow.manual_referral_reason,
                policy_version=case.policy_context.policy_version,
                rule_version_used=case.policy_context.effective_rule_version,
                publication_reference=case.policy_context.publication_reference,
                decision_due_at=case.decision_due_at,
                updated_at=case.audit.updated_at,
            )
            for case in sorted(
                filtered_cases,
                key=lambda item: (item.audit.updated_at or "", item.case_id),
                reverse=True,
            )
        ]

        return SupervisorCaseListResponse(
            workflow_pack=self.workflow_pack,
            total_cases=len(cases),
            filtered_count=len(filtered_cases),
            state_filter=normalized_state,
            holder_filter=normalized_holder,
            cases=summaries,
        )
