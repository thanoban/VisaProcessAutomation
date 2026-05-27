def test_submission_readiness_endpoint_reports_required_gaps(client):
    response = client.get("/governance/submission-readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["project_name"] == "VisaFlow MAS — Multi-Agent Visa Decision Support System"
    assert body["partner_track"] == "Arize"
    assert body["overall_status"] == "ACTION_REQUIRED"
    item_map = {item["key"]: item for item in body["items"]}
    assert item_map["license_file"]["status"] == "PASS"
    assert item_map["env_example"]["status"] == "PASS"
    assert item_map["phoenix_mcp_config"]["status"] == "PASS"
    assert item_map["submission_runbook"]["status"] == "PASS"
    assert item_map["hosted_url"]["status"] == "FAIL"
    assert item_map["public_repo_url"]["status"] == "FAIL"
    assert item_map["demo_video_url"]["status"] == "FAIL"
