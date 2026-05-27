def test_demo_showcase_seed_endpoint_creates_repeatable_case_set(client):
    response = client.post("/demo/showcase/seed")
    assert response.status_code == 200
    body = response.json()
    assert body["workflow_pack"] == "SRI_LANKA_TOURIST_VISIT"
    assert body["seeded_count"] == 5

    case_map = {item["case_id"]: item for item in body["cases"]}
    assert case_map["VISA-DEMO-LOW-RISK-001"]["actual_recommendation"] == "APPROVE_READY"
    assert case_map["VISA-DEMO-MISSING-BANK-001"]["actual_recommendation"] == "REQUEST_MORE_INFO"
    assert case_map["VISA-DEMO-SECURITY-001"]["actual_recommendation"] == "ENHANCED_REVIEW"
    assert case_map["VISA-DEMO-HIGH-RISK-001"]["actual_recommendation"] == "ENHANCED_REVIEW"
    assert case_map["VISA-DEMO-MANUAL-001"]["current_state"] == "REFERRED_TO_MANUAL_REVIEW"

    queue_response = client.get("/supervisor/cases")
    assert queue_response.status_code == 200
    queue_body = queue_response.json()
    returned_ids = {item["case_id"] for item in queue_body["cases"]}
    assert "VISA-DEMO-LOW-RISK-001" in returned_ids
    assert "VISA-DEMO-MANUAL-001" in returned_ids
