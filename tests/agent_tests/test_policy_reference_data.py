import json

from backend.services.policy_service import clear_policy_caches, load_reference_json
from backend.services.sri_lanka_reference_service import SriLankaReferenceService
from tools.policy_tools import retrieve_policy_sections


def test_reference_service_loads_file_backed_sri_lanka_data():
    service = SriLankaReferenceService()

    checklist = service.get_tourist_checklist()
    rules = service.get_active_rules()

    assert checklist.workflow_pack == "SRI_LANKA_TOURIST_VISIT"
    assert checklist.checklist[0].code == "PASSPORT"
    assert any("port-of-entry clearance" in note for note in checklist.notes)
    assert rules.active_policy_version.policy_version == "sl-tourist-policy-v1"
    assert rules.active_circulars[0].publications[0].reference == "https://www.eta.gov.lk/"
    assert any(rule.nationality == "NIGERIA" for rule in rules.nationality_exception_rules)


def test_reference_loader_supports_directory_override(monkeypatch, tmp_path):
    reference_dir = tmp_path / "reference_data"
    reference_dir.mkdir()
    payload = {
        "workflow_pack": "TEST_PACK",
        "visa_class": "TOURIST",
        "checklist": [],
        "notes": ["override active"],
    }
    (reference_dir / "override.json").write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setenv("VISAFLOW_REFERENCE_DATA_DIR", str(reference_dir))
    clear_policy_caches()

    loaded = load_reference_json("override.json")

    assert loaded["workflow_pack"] == "TEST_PACK"
    assert loaded["notes"] == ["override active"]

    clear_policy_caches()


def test_retrieve_policy_sections_uses_country_and_latest_effective_date(monkeypatch, tmp_path):
    policy_dir = tmp_path / "policy"
    policy_dir.mkdir()
    manifest = {
        "policy_version": "test-policy-v2",
        "workflow_pack": "SRI_LANKA_TOURIST_VISIT",
        "source_uri": "https://example.gov/policy",
        "sections": [
            {
                "policy_id": "RULE-1",
                "visa_class": "TOURIST",
                "country": "Sri Lanka",
                "effective_date": "2026-01-01",
                "requirement": "Older Sri Lanka rule",
            },
            {
                "policy_id": "RULE-1",
                "visa_class": "TOURIST",
                "country": "Sri Lanka",
                "effective_date": "2026-04-01",
                "requirement": "Latest Sri Lanka rule",
            },
            {
                "policy_id": "RULE-2",
                "visa_class": "TOURIST",
                "country": "Canada",
                "effective_date": "2026-04-01",
                "requirement": "Different country rule",
            },
            {
                "policy_id": "RULE-3",
                "visa_class": "TOURIST",
                "country": "GLOBAL",
                "effective_date": "2026-03-01",
                "requirement": "Global rule",
            },
        ],
    }
    (policy_dir / "tourist_policy_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    monkeypatch.setenv("VISAFLOW_POLICY_DIR", str(policy_dir))
    clear_policy_caches()

    retrieved = retrieve_policy_sections("tourist", "Sri Lanka", "2026-05-25")

    assert retrieved["policy_version"] == "test-policy-v2"
    assert retrieved["workflow_pack"] == "SRI_LANKA_TOURIST_VISIT"
    assert retrieved["source_uri"] == "https://example.gov/policy"
    assert [section["policy_id"] for section in retrieved["sections"]] == ["RULE-1", "RULE-3"]
    assert retrieved["sections"][0]["requirement"] == "Latest Sri Lanka rule"

    clear_policy_caches()
