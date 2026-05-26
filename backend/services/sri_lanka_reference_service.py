from __future__ import annotations

from datetime import datetime, timezone

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
from backend.services.utils import decision_urgency, parse_utcish_datetime


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
        extension_requested = 0
        extension_appointment_required = 0
        under_extension_review = 0
        overdue_cases = 0
        due_within_48h = 0
        due_dates: list[datetime] = []
        now = datetime.now(timezone.utc)
        for case in cases:
            state = case.workflow.current_state
            counts_by_state[state] = counts_by_state.get(state, 0) + 1
            if state == "REFERRED_TO_MANUAL_REVIEW":
                manual_referrals += 1
            if state == "WAITING_FOR_DOCUMENTS":
                waiting_for_documents += 1
            if state == "READY_FOR_OFFICER_REVIEW":
                ready_for_officer_review += 1
            if case.workflow.extension_state == "EXTENSION_REQUESTED":
                extension_requested += 1
            if case.workflow.extension_state == "EXTENSION_APPOINTMENT_REQUIRED":
                extension_appointment_required += 1
            if case.workflow.extension_state == "UNDER_EXTENSION_REVIEW":
                under_extension_review += 1
            due_at = self._parse_iso_datetime(case.decision_due_at)
            if due_at:
                due_dates.append(due_at)
                urgency = decision_urgency(case.decision_due_at, now=now)
                if urgency == "OVERDUE":
                    overdue_cases += 1
                elif urgency == "DUE_WITHIN_48H":
                    due_within_48h += 1
        return SupervisorQueueSummary(
            workflow_pack=self.workflow_pack,
            counts_by_state=counts_by_state,
            manual_referrals=manual_referrals,
            waiting_for_documents=waiting_for_documents,
            ready_for_officer_review=ready_for_officer_review,
            extension_requested=extension_requested,
            extension_appointment_required=extension_appointment_required,
            under_extension_review=under_extension_review,
            overdue_cases=overdue_cases,
            due_within_48h=due_within_48h,
            oldest_due_at=min(due_dates).isoformat().replace("+00:00", "Z") if due_dates else None,
        )

    def build_supervisor_case_list(
        self,
        cases: list[CasePacket],
        *,
        state_filter: str = "",
        holder_filter: str = "",
        urgency_filter: str = "",
    ) -> SupervisorCaseListResponse:
        normalized_state = state_filter.strip().upper()
        normalized_holder = holder_filter.strip().upper()
        normalized_urgency = urgency_filter.strip().upper()

        filtered_cases = []
        for case in cases:
            if normalized_state and case.workflow.current_state != normalized_state:
                continue
            if normalized_holder and case.workflow.current_holder != normalized_holder:
                continue
            if normalized_urgency and self._case_urgency(case) != normalized_urgency:
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
                extension_state=case.workflow.extension_state,
                manual_referral_reason=case.workflow.manual_referral_reason,
                policy_version=case.policy_context.policy_version,
                rule_version_used=case.policy_context.effective_rule_version,
                publication_reference=case.policy_context.publication_reference,
                decision_due_at=case.decision_due_at,
                urgency_level=self._case_urgency(case),
                updated_at=case.audit.updated_at,
            )
            for case in sorted(filtered_cases, key=self._supervisor_sort_key)
        ]

        return SupervisorCaseListResponse(
            workflow_pack=self.workflow_pack,
            total_cases=len(cases),
            filtered_count=len(filtered_cases),
            state_filter=normalized_state,
            holder_filter=normalized_holder,
            urgency_filter=normalized_urgency,
            cases=summaries,
        )

    def _supervisor_sort_key(self, case: CasePacket) -> tuple[int, datetime, str, str]:
        urgency = self._case_urgency(case)
        due_at = self._parse_iso_datetime(case.decision_due_at) or datetime.max.replace(tzinfo=timezone.utc)
        urgency_priority = {
            "OVERDUE": 0,
            "DUE_WITHIN_48H": 1,
            "ON_TRACK": 2,
            "UNSCHEDULED": 3,
        }
        updated_at = self._parse_iso_datetime(case.audit.updated_at) or datetime.min.replace(tzinfo=timezone.utc)
        return (
            urgency_priority.get(urgency, 4),
            due_at,
            -int(updated_at.timestamp()) if updated_at != datetime.min.replace(tzinfo=timezone.utc) else 0,
            case.case_id,
        )

    def _case_urgency(self, case: CasePacket) -> str:
        return decision_urgency(case.decision_due_at)

    def _parse_iso_datetime(self, value: str | None) -> datetime | None:
        return parse_utcish_datetime(value)
