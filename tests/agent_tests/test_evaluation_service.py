from backend.api import routes


def _sample_payload(case_id: str, mock_profile: dict | None = None):
    return {
        "case_id": case_id,
        "applicant": {
            "full_name": "Arjun Mehta",
            "date_of_birth": "1998-04-12",
            "nationality": "Indian",
            "passport_number": "P1234567",
            "contact_email": "arjun@example.com",
        },
        "visa_application": {
            "visa_class": "TOURIST",
            "purpose_of_travel": "Tourism and sightseeing in Sri Lanka",
            "arrival_date": "2026-08-10",
            "departure_date": "2026-08-20",
            "destination_address": "Hotel Example",
            "country_of_application": "India",
            "payment_status": "PAID",
        },
        "documents": [
            {"document_id": "DOC-001", "document_type": "PASSPORT", "file_uri": "gs://x/passport.pdf"},
            {"document_id": "DOC-002", "document_type": "BANK_STATEMENT", "file_uri": "gs://x/bank.pdf"},
            {"document_id": "DOC-003", "document_type": "FLIGHT_ITINERARY", "file_uri": "gs://x/flight.pdf"},
        ],
        "policy_context": {
            "country": "Sri Lanka",
            "policy_version": "sl-tourist-policy-v1",
            "effective_date": "2026-05-25",
        },
        "mock_profile": mock_profile or {},
    }


def test_evaluation_catalog_endpoint_exposes_required_rubric(client):
    response = client.get("/governance/evaluations/catalog")
    assert response.status_code == 200
    body = response.json()
    assert body["workflow_pack"] == "SRI_LANKA_TOURIST_VISIT"
    assert "security_unavailable" in body["required_scenarios"]
    assert "no raw security leakage" in body["required_criteria"]


def test_case_evaluation_run_returns_pass_and_updates_supervisor_status(client):
    payload = _sample_payload("VISA-2026-EVAL-001")
    assert client.post("/applications", json=payload).status_code == 201
    assert client.post(f"/cases/{payload['case_id']}/process").status_code == 200

    evaluation_response = client.post(f"/cases/{payload['case_id']}/evaluations/run")
    assert evaluation_response.status_code == 200
    body = evaluation_response.json()
    assert body["case_id"] == payload["case_id"]
    assert body["overall_status"] == "PASS"
    assert body["passed_checks"] == body["check_count"]
    assert body["human_review_required"] is True
    assert body["trace_id"]
    assert any(check["check_name"] == "no_automatic_final_legal_decision" for check in body["checks"])

    case = client.get(f"/cases/{payload['case_id']}").json()
    assert case["agent_outputs"]["supervisor_agent"]["evaluation_status"] == "PASS"

    audit = client.get(f"/cases/{payload['case_id']}/audit").json()
    evaluation_events = [item for item in audit if item["event_type"] == "EVALUATION_RUN_RECORDED"]
    assert evaluation_events
    assert evaluation_events[0]["payload"]["overall_status"] == "PASS"


def test_case_evaluation_run_detects_missing_policy_citation_failure(client):
    payload = _sample_payload("VISA-2026-EVAL-FAIL-001")
    assert client.post("/applications", json=payload).status_code == 201
    assert client.post(f"/cases/{payload['case_id']}/process").status_code == 200

    case = routes.case_service.get_case(payload["case_id"])
    case.agent_outputs["supervisor_agent"]["policy_references"] = []
    routes.case_service.save_case(case)

    evaluation_response = client.post(f"/cases/{payload['case_id']}/evaluations/run")
    assert evaluation_response.status_code == 200
    body = evaluation_response.json()
    assert body["overall_status"] == "FAIL"
    failed_checks = {check["check_name"]: check for check in body["checks"] if check["status"] == "FAIL"}
    assert "policy_citation_present" in failed_checks
    assert "missing" in failed_checks["policy_citation_present"]["details"].lower()


def test_case_evaluation_requires_supervisor_output(client):
    payload = _sample_payload("VISA-2026-EVAL-CONFLICT-001")
    assert client.post("/applications", json=payload).status_code == 201

    evaluation_response = client.post(f"/cases/{payload['case_id']}/evaluations/run")
    assert evaluation_response.status_code == 409
    assert "Supervisor output is required" in evaluation_response.json()["detail"]
