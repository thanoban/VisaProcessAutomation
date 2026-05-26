from __future__ import annotations

from backend.services.policy_service import load_policy_manifest


def _country_matches(section: dict, country: str) -> bool:
    section_country = str(section.get("country", country)).strip().lower()
    normalized_country = country.strip().lower()
    return section_country in {normalized_country, "global", "*"}


def _latest_effective_sections(sections: list[dict]) -> list[dict]:
    latest_by_policy_id: dict[str, dict] = {}
    policy_order: list[str] = []
    for section in sections:
        policy_id = section["policy_id"]
        if policy_id not in latest_by_policy_id:
            policy_order.append(policy_id)
        current = latest_by_policy_id.get(policy_id)
        if current is None or section["effective_date"] > current["effective_date"]:
            latest_by_policy_id[policy_id] = section
    return [latest_by_policy_id[policy_id] for policy_id in policy_order]


def retrieve_policy_sections(visa_class: str, country: str, date: str) -> dict:
    manifest = load_policy_manifest()
    matched_sections = [
        section
        for section in manifest["sections"]
        if section["visa_class"] == visa_class.upper()
        and section["effective_date"] <= date
        and _country_matches(section, country)
    ]
    sections = _latest_effective_sections(matched_sections)
    return {
        "visa_class": visa_class.upper(),
        "country": country,
        "policy_version": manifest["policy_version"],
        "workflow_pack": manifest.get("workflow_pack", "SRI_LANKA_TOURIST_VISIT"),
        "source_uri": manifest.get("source_uri", ""),
        "sections": sections,
    }
