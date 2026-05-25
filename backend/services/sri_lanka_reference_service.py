from __future__ import annotations

from backend.models.schemas import (
    CasePacket,
    ChannelPublication,
    ChecklistItem,
    ChecklistResponse,
    EffectivePolicyVersion,
    GovernanceRulesResponse,
    NationalityExceptionRule,
    RuleCircular,
    SupervisorQueueSummary,
)


class SriLankaReferenceService:
    workflow_pack = "SRI_LANKA_TOURIST_VISIT"

    def get_tourist_checklist(self) -> ChecklistResponse:
        return ChecklistResponse(
            workflow_pack=self.workflow_pack,
            visa_class="TOURIST",
            checklist=[
                ChecklistItem(
                    code="PASSPORT",
                    title="Valid Passport",
                    description="Provide a passport valid for at least six months from the intended date of arrival in Sri Lanka.",
                    guidance="Use a clear, readable copy. The passport details must match the application data.",
                ),
                ChecklistItem(
                    code="FUNDS",
                    title="Funds and Return Assurance",
                    description="Show evidence of adequate funds and return or onward travel assurance.",
                    guidance="Examples include recent bank statements and onward ticket or itinerary evidence.",
                ),
                ChecklistItem(
                    code="PURPOSE",
                    title="Tourist Visit Purpose",
                    description="Provide travel purpose details consistent with a short tourist visit to Sri Lanka.",
                    guidance="Avoid mixing tourist travel with work or long-stay purposes.",
                ),
                ChecklistItem(
                    code="OFFICIAL_PAYMENT",
                    title="Official Payment Channel",
                    description="Use only the official ETA and immigration payment channels.",
                    guidance="The system should clearly identify the official payment and case reference path to reduce scam risk.",
                ),
            ],
            notes=[
                "ETA is not the same as final port-of-entry clearance.",
                "Some nationalities or special cases may require sponsor-backed or manual handling.",
                "Extension handling may require online steps, appointments, or head-office action.",
            ],
        )

    def get_active_rules(self) -> GovernanceRulesResponse:
        publications = [
            ChannelPublication(
                channel="ETA_PORTAL",
                published_at="2026-05-25",
                reference="https://www.eta.gov.lk/",
                notes="40-country free-of-charge tourist ETA notice visible on ETA site.",
            ),
            ChannelPublication(
                channel="IMMIGRATION_GENERAL_INFO",
                published_at="2025-10-13",
                reference="https://www.immigration.gov.lk/pages_e.php?id=14&os=vb..",
                notes="General information page still references revoked ETA-mandatory announcement wording.",
            ),
        ]
        return GovernanceRulesResponse(
            workflow_pack=self.workflow_pack,
            active_policy_version=EffectivePolicyVersion(
                workflow_pack=self.workflow_pack,
                policy_version="sl-tourist-policy-v1",
                rule_version="sl-rule-pack-2026-05-25",
                effective_date="2026-05-25",
                publication_reference="ETA-40-COUNTRY-SCHEME-2026-05-25",
                notes="Officer workflow should use the active internal rule pack even when public channels lag.",
            ),
            active_circulars=[
                RuleCircular(
                    circular_id="SL-ETA-2026-05-25",
                    title="40-country free-of-charge tourist ETA scheme",
                    effective_date="2026-05-25",
                    status="ACTIVE",
                    legal_owner="Department of Immigration and Emigration",
                    public_summary="Certain nationalities can obtain a 30-day tourist ETA free of charge.",
                    internal_summary="Apply the active 2026 tourist ETA pack and preserve nationality-based exceptions separately.",
                    publications=publications[:1],
                ),
                RuleCircular(
                    circular_id="SL-ETA-2025-10-13-REVOKED",
                    title="ETA mandatory announcement revoked until further notice",
                    effective_date="2025-10-13",
                    status="REVOKED_NOTICE_REMAINS_VISIBLE",
                    legal_owner="Department of Immigration and Emigration",
                    public_summary="Some public pages still show wording about the revocation of the ETA-mandatory notice.",
                    internal_summary="Public channel inconsistency must not override the active internal rule pack.",
                    publications=publications[1:],
                ),
            ],
            nationality_exception_rules=[
                NationalityExceptionRule(
                    rule_id="SL-SPONSOR-001",
                    nationality="AFGHANISTAN",
                    requires_sponsor=True,
                    reason="Tourist or business ETA should be routed through Sri Lankan sponsor and head-office handling.",
                ),
                NationalityExceptionRule(
                    rule_id="SL-SPONSOR-002",
                    nationality="CAMEROON",
                    requires_sponsor=True,
                    reason="Tourist or business ETA should be routed through Sri Lankan sponsor and head-office handling.",
                ),
                NationalityExceptionRule(
                    rule_id="SL-SPONSOR-003",
                    nationality="GHANA",
                    requires_sponsor=True,
                    reason="Tourist or business ETA should be routed through Sri Lankan sponsor and head-office handling.",
                ),
                NationalityExceptionRule(
                    rule_id="SL-SPONSOR-004",
                    nationality="NIGERIA",
                    requires_sponsor=True,
                    reason="Tourist or business ETA should be routed through Sri Lankan sponsor and head-office handling.",
                ),
                NationalityExceptionRule(
                    rule_id="SL-SPONSOR-005",
                    nationality="IVORY COAST",
                    requires_sponsor=True,
                    reason="Tourist or business ETA should be routed through Sri Lankan sponsor and head-office handling.",
                ),
                NationalityExceptionRule(
                    rule_id="SL-SPONSOR-006",
                    nationality="SYRIA",
                    requires_sponsor=True,
                    reason="Tourist or business ETA should be routed through Sri Lankan sponsor and head-office handling.",
                ),
                NationalityExceptionRule(
                    rule_id="SL-SPONSOR-007",
                    nationality="TAIWAN-CHINA",
                    requires_sponsor=True,
                    reason="Tourist or business ETA should be routed through Sri Lankan sponsor and head-office handling.",
                ),
                NationalityExceptionRule(
                    rule_id="SL-SPONSOR-008",
                    nationality="KOSOVO",
                    requires_sponsor=True,
                    reason="Tourist or business ETA should be routed through Sri Lankan sponsor and head-office handling.",
                ),
            ],
        )

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
