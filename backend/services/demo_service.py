from __future__ import annotations

from backend.models.schemas import (
    Applicant,
    ApplicationCreateRequest,
    DemoCaseSummary,
    DemoSeedResponse,
    DocumentItem,
    PolicyContext,
    VisaApplication,
)
from backend.services.case_service import CaseService
from backend.workflows.tourist_visa_workflow import TouristVisaWorkflow


class DemoService:
    def __init__(self) -> None:
        self.case_service = CaseService()
        self.workflow = TouristVisaWorkflow()

    def seed_showcase_cases(self) -> DemoSeedResponse:
        scenarios = [
            {
                "case_id": "VISA-DEMO-LOW-RISK-001",
                "scenario_name": "complete_low_risk_tourist_case",
                "expected_recommendation": "APPROVE_READY",
                "applicant": Applicant(
                    full_name="Arjun Mehta",
                    date_of_birth="1998-04-12",
                    nationality="Indian",
                    passport_number="P1234567",
                    contact_email="arjun@example.com",
                ),
                "visa_application": VisaApplication(
                    visa_class="TOURIST",
                    purpose_of_travel="Tourism and sightseeing in Sri Lanka",
                    arrival_date="2026-08-10",
                    departure_date="2026-08-20",
                    destination_address="Hotel Example, Colombo",
                    country_of_application="India",
                    payment_status="PAID",
                ),
                "documents": self._documents(include_bank=True),
                "mock_profile": {},
            },
            {
                "case_id": "VISA-DEMO-MISSING-BANK-001",
                "scenario_name": "missing_bank_statement",
                "expected_recommendation": "REQUEST_MORE_INFO",
                "applicant": Applicant(
                    full_name="Maya Fernando",
                    date_of_birth="1995-01-22",
                    nationality="Singaporean",
                    passport_number="S7654321",
                    contact_email="maya@example.com",
                ),
                "visa_application": VisaApplication(
                    visa_class="TOURIST",
                    purpose_of_travel="Short holiday visit in Sri Lanka",
                    arrival_date="2026-07-15",
                    departure_date="2026-07-23",
                    destination_address="Galle hotel booking",
                    country_of_application="Singapore",
                    payment_status="PAID",
                ),
                "documents": self._documents(include_bank=False),
                "mock_profile": {},
            },
            {
                "case_id": "VISA-DEMO-SECURITY-001",
                "scenario_name": "security_unavailable",
                "expected_recommendation": "ENHANCED_REVIEW",
                "applicant": Applicant(
                    full_name="Rafiq Hasan",
                    date_of_birth="1989-06-03",
                    nationality="Bangladeshi",
                    passport_number="B3456789",
                    contact_email="rafiq@example.com",
                ),
                "visa_application": VisaApplication(
                    visa_class="TOURIST",
                    purpose_of_travel="Tourism and family sightseeing trip",
                    arrival_date="2026-09-02",
                    departure_date="2026-09-11",
                    destination_address="Negombo hotel",
                    country_of_application="Bangladesh",
                    payment_status="PAID",
                ),
                "documents": self._documents(include_bank=True),
                "mock_profile": {"security_status": "SYSTEM_UNAVAILABLE"},
            },
            {
                "case_id": "VISA-DEMO-HIGH-RISK-001",
                "scenario_name": "sudden_suspicious_deposit",
                "expected_recommendation": "ENHANCED_REVIEW",
                "applicant": Applicant(
                    full_name="Fatima Noor",
                    date_of_birth="1993-10-18",
                    nationality="Pakistani",
                    passport_number="PK9988776",
                    contact_email="fatima@example.com",
                ),
                "visa_application": VisaApplication(
                    visa_class="TOURIST",
                    purpose_of_travel="Tourism and shopping trip",
                    arrival_date="2026-10-05",
                    departure_date="2026-10-12",
                    destination_address="Colombo guest house",
                    country_of_application="Pakistan",
                    payment_status="PAID",
                ),
                "documents": self._documents(include_bank=True),
                "mock_profile": {
                    "risk_band": "HIGH",
                    "sudden_deposits": True,
                    "fraud_indicators": ["SUDDEN_DEPOSITS"],
                    "risk_reasons": ["Bank statement shows a large unexplained deposit immediately before travel."],
                },
            },
            {
                "case_id": "VISA-DEMO-MANUAL-001",
                "scenario_name": "manual_referral",
                "expected_recommendation": "ENHANCED_REVIEW",
                "applicant": Applicant(
                    full_name="Amina Yusuf",
                    date_of_birth="1992-11-22",
                    nationality="Nigeria",
                    passport_number="N9988776",
                    contact_email="amina@example.com",
                ),
                "visa_application": VisaApplication(
                    visa_class="TOURIST",
                    purpose_of_travel="Tourism with local sponsor support",
                    arrival_date="2026-09-14",
                    departure_date="2026-09-24",
                    destination_address="Colombo guest house",
                    country_of_application="Nigeria",
                    payment_status="PAID",
                ),
                "documents": self._documents(include_bank=True),
                "mock_profile": {},
            },
        ]

        seeded: list[DemoCaseSummary] = []
        for scenario in scenarios:
            payload = ApplicationCreateRequest(
                case_id=scenario["case_id"],
                applicant=scenario["applicant"],
                visa_application=scenario["visa_application"],
                documents=scenario["documents"],
                policy_context=PolicyContext(
                    country="Sri Lanka",
                    policy_version="sl-tourist-policy-v1",
                    effective_date="2026-05-25",
                ),
                mock_profile=scenario["mock_profile"],
            )
            self.case_service.create_case(payload)
            result = self.workflow.process_case(payload.case_id)
            case = self.case_service.get_case(payload.case_id)
            if not result or not case:
                continue
            seeded.append(
                DemoCaseSummary(
                    case_id=payload.case_id,
                    scenario_name=scenario["scenario_name"],
                    expected_recommendation=scenario["expected_recommendation"],
                    actual_recommendation=result["recommendation"],
                    current_state=case.workflow.current_state,
                    current_holder=case.workflow.current_holder,
                    next_action=case.workflow.next_action,
                )
            )

        return DemoSeedResponse(
            workflow_pack="SRI_LANKA_TOURIST_VISIT",
            seeded_count=len(seeded),
            cases=seeded,
            notes=[
                "These demo cases use mock applicant data only.",
                "The seeded set is designed to cover a judge-friendly spread of recommendation states and routing paths.",
                "Use the governance evaluation runner and self-improvement panel on seeded cases to demonstrate Arize-track workflow safety.",
            ],
        )

    @staticmethod
    def _documents(*, include_bank: bool) -> list[DocumentItem]:
        documents = [
            DocumentItem(document_id="DOC-001", document_type="PASSPORT", file_uri="gs://demo/passport.pdf"),
            DocumentItem(document_id="DOC-003", document_type="FLIGHT_ITINERARY", file_uri="gs://demo/flight.pdf"),
        ]
        if include_bank:
            documents.insert(
                1,
                DocumentItem(document_id="DOC-002", document_type="BANK_STATEMENT", file_uri="gs://demo/bank.pdf"),
            )
        return documents
