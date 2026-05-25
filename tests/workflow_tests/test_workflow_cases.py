import json
from pathlib import Path

import pytest


def create_case(client, payload):
    response = client.post("/applications", json=payload)
    assert response.status_code == 201
    return response.json()


def process_case(client, case_id):
    response = client.post(f"/cases/{case_id}/process")
    assert response.status_code == 200
    return response.json()


def sample_payload():
    path = Path(__file__).resolve().parents[1] / "sample_cases" / "sample_case.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("case_id", "mock_profile", "expected_recommendation"),
    [
        ("VISA-2026-LOWRISK", {}, "APPROVE_READY"),
        ("VISA-2026-EXPIRED", {"passport_expiry": "2026-01-01"}, "ENHANCED_REVIEW"),
        ("VISA-2026-MISSINGBANK", {}, "REQUEST_MORE_INFO"),
        ("VISA-2026-LOWFUNDS", {"average_balance": 300.0}, "REQUEST_MORE_INFO"),
        ("VISA-2026-UNREADABLE", {"force_invalid_upload": True}, "REQUEST_MORE_INFO"),
        ("VISA-2026-NAMEMISMATCH", {"passport_name": "Kamal P."}, "ENHANCED_REVIEW"),
        ("VISA-2026-SUDDENDEPOSIT", {"sudden_deposits": [5000.0]}, "REQUEST_MORE_INFO"),
        ("VISA-2026-POLICYFAIL", {"policy_failures": ["TOURIST-20-C"]}, "REFUSAL_DRAFT_READY"),
        ("VISA-2026-HIGHRISK", {"risk_band": "HIGH", "fraud_indicators": ["DUPLICATE_CONTACT"]}, "ENHANCED_REVIEW"),
        ("VISA-2026-SECURITYDOWN", {"security_status": "SYSTEM_UNAVAILABLE"}, "ENHANCED_REVIEW"),
        ("VISA-2026-MANUAL", {"requires_manual_referral": True}, "ENHANCED_REVIEW"),
        ("VISA-2026-CONFLICT", {"conflicting_publication": True}, "REQUEST_MORE_INFO"),
        ("VISA-2026-OVERRIDE", {}, "APPROVE_READY"),
    ],
)
def test_workflow_recommendations(client, case_id, mock_profile, expected_recommendation):
    payload = sample_payload()
    payload["case_id"] = case_id
    payload["mock_profile"] = mock_profile
    if case_id == "VISA-2026-MISSINGBANK":
        payload["documents"] = [doc for doc in payload["documents"] if doc["document_type"] != "BANK_STATEMENT"]
    create_case(client, payload)
    result = process_case(client, case_id)
    assert result["recommendation"] == expected_recommendation
    assert result["human_decision_required"] is True


def test_sample_output_shape(client):
    payload = sample_payload()
    create_case(client, payload)
    result = process_case(client, payload["case_id"])
    assert result["case_id"] == "VISA-2026-0001"
    assert result["recommendation"] == "APPROVE_READY"
    assert "DOC-001" in result["evidence_references"]
    assert result["next_action"] == "HUMAN_OFFICER_FINAL_REVIEW"
    assert result["workflow_pack"] == "SRI_LANKA_TOURIST_VISIT"
    assert result["rule_version_used"] == "sl-rule-pack-2026-05-25"
