def test_demo_showcase_seed_endpoint_creates_judge_ready_cases(client):
    response = client.post("/demo/showcase/seed")
    assert response.status_code == 200

    body = response.json()
    assert body["workflow_pack"] == "SRI_LANKA_TOURIST_VISIT"
    assert body["seeded_count"] == 5
    assert len(body["cases"]) == 5

    case_map = {item["case_id"]: item for item in body["cases"]}
    assert case_map["VISA-DEMO-LOW-RISK-001"]["actual_recommendation"] == "APPROVE_READY"
    assert case_map["VISA-DEMO-MISSING-BANK-001"]["actual_recommendation"] == "REQUEST_MORE_INFO"
    assert case_map["VISA-DEMO-SECURITY-001"]["actual_recommendation"] == "ENHANCED_REVIEW"
    assert case_map["VISA-DEMO-MANUAL-001"]["current_holder"] == "MISSION_OR_HEAD_OFFICE"

    low_risk_case = client.get("/cases/VISA-DEMO-LOW-RISK-001")
    assert low_risk_case.status_code == 200
    assert low_risk_case.json()["workflow"]["current_state"] == "READY_FOR_OFFICER_REVIEW"
