from __future__ import annotations

from datetime import date

from backend.models.schemas import CasePacket


def _find_doc(case: CasePacket, document_id: str) -> dict:
    return next((doc.model_dump() for doc in case.documents if doc.document_id == document_id), {})


def extract_document_fields(case: CasePacket, document_id: str) -> dict:
    profile = case.mock_profile
    doc = _find_doc(case, document_id)
    if doc.get("document_type") == "PASSPORT":
        return {
            "document_id": document_id,
            "document_type": "PASSPORT",
            "passport_number": profile.get("passport_number", case.applicant.passport_number),
            "full_name": profile.get("passport_name", case.applicant.full_name),
            "date_of_birth": profile.get("passport_dob", case.applicant.date_of_birth),
            "nationality": profile.get("passport_nationality", case.applicant.nationality),
            "expiry_date": profile.get("passport_expiry", "2028-12-31"),
            "mrz_consistent": profile.get("mrz_consistent", True),
            "tampering_indicators": profile.get("tampering_indicators", []),
        }
    if doc.get("document_type") == "BANK_STATEMENT":
        return {
            "document_id": document_id,
            "document_type": "BANK_STATEMENT",
            "account_holder": profile.get("bank_account_holder", case.applicant.full_name),
            "currency": profile.get("bank_currency", "USD"),
            "ending_balance": profile.get("ending_balance", 2800.0),
        }
    return {"document_id": document_id, "document_type": doc.get("document_type", "UNKNOWN"), "text_ok": True}


def validate_passport(passport_data: dict, application_name: str) -> dict:
    expiry = date.fromisoformat(passport_data["expiry_date"])
    valid_months = (expiry - date.today()).days / 30
    name_match = passport_data["full_name"].strip().lower() == application_name.strip().lower()
    findings = []
    if valid_months < 6:
        findings.append("Passport validity is below 6 months.")
    if not passport_data.get("mrz_consistent", False):
        findings.append("MRZ consistency check failed.")
    if passport_data.get("tampering_indicators"):
        findings.append("Possible tampering indicators detected.")
    return {
        "valid": valid_months >= 6 and name_match and passport_data.get("mrz_consistent", False) and not passport_data.get("tampering_indicators"),
        "months_valid": round(valid_months, 1),
        "name_match": name_match,
        "findings": findings,
    }


def check_photo_quality(case: CasePacket, document_id: str) -> dict:
    profile = case.mock_profile
    return {
        "document_id": document_id,
        "photo_quality": profile.get("photo_quality", "PASS"),
        "face_visible": profile.get("face_visible", True),
        "size_ok": profile.get("photo_size_ok", True),
    }
