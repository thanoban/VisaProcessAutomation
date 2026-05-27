def _sample_payload(case_id: str):
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
    }


def test_agent_runtime_status_endpoint_reports_mock_or_ready_state(client):
    response = client.get("/governance/agent-runtime/status")
    assert response.status_code == 200
    body = response.json()
    assert body["runtime"] == "GOOGLE_ADK"
    assert body["provider"] == "Gemini"
    assert body["status"] in {"READY", "MOCK_ONLY", "DEGRADED"}
    assert "self_improvement_agent" in body["agent_names"]


def test_self_improvement_review_endpoint_returns_human_approved_suggestions(client):
    payload = _sample_payload("VISA-2026-IMPROVE-001")
    assert client.post("/applications", json=payload).status_code == 201
    assert client.post(f"/cases/{payload['case_id']}/process").status_code == 200

    review_response = client.post(f"/cases/{payload['case_id']}/self-improvement/review")
    assert review_response.status_code == 200
    body = review_response.json()
    assert body["case_id"] == payload["case_id"]
    assert body["runtime_mode"] in {"GOOGLE_ADK_GEMINI", "GOOGLE_ADK_MOCK"}
    assert body["human_approval_required"] is True
    assert body["proposed_changes"]
    assert body["comparison_questions"]
    assert body["trace_id"]
    assert body["observability_export_status"] in {"DISABLED", "PENDING", "EXPORTED", "UNAVAILABLE", "FAILED"}

    audit = client.get(f"/cases/{payload['case_id']}/audit").json()
    improvement_events = [item for item in audit if item["event_type"] == "SELF_IMPROVEMENT_REVIEW_RECORDED"]
    assert improvement_events
    assert improvement_events[0]["payload"]["human_approval_required"] is True
