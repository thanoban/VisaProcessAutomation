from __future__ import annotations

from backend.services.policy_service import load_policy_manifest


def retrieve_policy_sections(visa_class: str, country: str, date: str) -> dict:
    manifest = load_policy_manifest()
    sections = [
        section
        for section in manifest["sections"]
        if section["visa_class"] == visa_class.upper() and section["effective_date"] <= date
    ]
    return {
        "visa_class": visa_class.upper(),
        "country": country,
        "policy_version": manifest["policy_version"],
        "sections": sections,
    }
