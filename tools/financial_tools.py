from __future__ import annotations

from backend.models.schemas import CasePacket


def calculate_bank_statement_metrics(case: CasePacket, document_id: str) -> dict:
    profile = case.mock_profile
    avg = float(profile.get("average_balance", 2800.0))
    sudden = profile.get("sudden_deposits", [])
    salary = profile.get("salary_deposits", [1200.0, 1200.0, 1200.0])
    patterns = []
    if sudden:
        patterns.append("Sudden large deposits detected.")
    if avg < float(profile.get("minimum_required_funds", 1500.0)):
        patterns.append("Average balance below minimum requirement.")
    return {
        "document_id": document_id,
        "average_balance": avg,
        "ending_balance": float(profile.get("ending_balance", avg + 200)),
        "currency": profile.get("bank_currency", "USD"),
        "sudden_deposits": sudden,
        "salary_deposits": salary,
        "suspicious_patterns": patterns,
    }


def parse_employment_letter(case: CasePacket, document_id: str | None = None) -> dict:
    profile = case.mock_profile
    return {
        "document_id": document_id or "EMPLOYMENT-LETTER",
        "employer_name": profile.get("employer_name", "Example Holdings"),
        "role": profile.get("employment_role", "Analyst"),
        "salary": profile.get("employment_salary", 1200.0),
        "employment_start_date": profile.get("employment_start_date", "2023-02-01"),
        "contact_details": profile.get("employment_contact", "hr@example.com"),
    }
