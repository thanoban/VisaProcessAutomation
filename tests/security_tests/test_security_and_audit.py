def test_security_payload_is_minimal_and_audit_exists(client):
    payload = {
        "case_id": "VISA-2026-SEC-001",
        "applicant": {
            "full_name": "Arjun Mehta",
            "date_of_birth": "1998-04-12",
            "nationality": "Indian",
            "passport_number": "P1234567",
            "contact_email": "arjun@example.com"
        },
        "visa_application": {
            "visa_class": "TOURIST",
            "purpose_of_travel": "Tourism and sightseeing in Sri Lanka",
            "arrival_date": "2026-08-10",
            "departure_date": "2026-08-20",
            "destination_address": "Hotel Example",
            "country_of_application": "India",
            "payment_status": "PAID"
        },
        "documents": [
            {"document_id": "DOC-001", "document_type": "PASSPORT", "file_uri": "gs://x/passport.pdf"},
            {"document_id": "DOC-002", "document_type": "BANK_STATEMENT", "file_uri": "gs://x/bank.pdf"},
            {"document_id": "DOC-003", "document_type": "FLIGHT_ITINERARY", "file_uri": "gs://x/flight.pdf"}
        ],
        "policy_context": {
            "country": "Sri Lanka",
            "policy_version": "sl-tourist-policy-v1",
            "effective_date": "2026-05-25"
        },
        "mock_profile": {
            "security_status": "POSSIBLE_MATCH"
        }
    }
    assert client.post("/applications", json=payload).status_code == 201
    result = client.post(f"/cases/{payload['case_id']}/process")
    assert result.status_code == 200
    body = result.json()
    assert body["recommendation"] == "ENHANCED_REVIEW"
    audit = client.get(f"/cases/{payload['case_id']}/audit").json()
    assert audit
    assert any(item["policy_version"] == "sl-tourist-policy-v1" for item in audit)
    assert any(item["policy_source_uri"].startswith("https://www.immigration.gov.lk/") for item in audit)
    security_outputs = [item["payload"] for item in audit if item.get("agent_name") == "security_background_agent"]
    assert security_outputs
    raw = str(security_outputs[0])
    assert "classified" not in raw.lower()
    assert "watchlist_details" not in raw.lower()


def test_officer_decision_records_override_reason(client):
    payload = {
        "case_id": "VISA-2026-DEC-001",
        "applicant": {
            "full_name": "Arjun Mehta",
            "date_of_birth": "1998-04-12",
            "nationality": "Indian",
            "passport_number": "P1234567",
            "contact_email": "arjun@example.com"
        },
        "visa_application": {
            "visa_class": "TOURIST",
            "purpose_of_travel": "Tourism and sightseeing in Sri Lanka",
            "arrival_date": "2026-08-10",
            "departure_date": "2026-08-20",
            "destination_address": "Hotel Example",
            "country_of_application": "India",
            "payment_status": "PAID"
        },
        "documents": [
            {"document_id": "DOC-001", "document_type": "PASSPORT", "file_uri": "gs://x/passport.pdf"},
            {"document_id": "DOC-002", "document_type": "BANK_STATEMENT", "file_uri": "gs://x/bank.pdf"},
            {"document_id": "DOC-003", "document_type": "FLIGHT_ITINERARY", "file_uri": "gs://x/flight.pdf"}
        ],
        "policy_context": {
            "country": "Sri Lanka",
            "policy_version": "sl-tourist-policy-v1",
            "effective_date": "2026-05-25"
        }
    }
    assert client.post("/applications", json=payload).status_code == 201
    assert client.post(f"/cases/{payload['case_id']}/process").status_code == 200
    decision = client.post(
        f"/cases/{payload['case_id']}/officer-decision",
        json={
            "decision": "REJECT",
            "officer_id": "OFF-1",
            "reason": "Officer reached a different conclusion after manual review.",
            "override_reason": "Conflicting travel history context found during manual inspection."
        },
    )
    assert decision.status_code == 200
    audit = client.get(f"/cases/{payload['case_id']}/audit").json()
    assert any(item["override_reason"] == "Conflicting travel history context found during manual inspection." for item in audit)


def test_officer_override_requires_reason_when_decision_differs_from_recommendation(client):
    payload = {
        "case_id": "VISA-2026-DEC-REQ-001",
        "applicant": {
            "full_name": "Arjun Mehta",
            "date_of_birth": "1998-04-12",
            "nationality": "Indian",
            "passport_number": "P1234567",
            "contact_email": "arjun@example.com"
        },
        "visa_application": {
            "visa_class": "TOURIST",
            "purpose_of_travel": "Tourism and sightseeing in Sri Lanka",
            "arrival_date": "2026-08-10",
            "departure_date": "2026-08-20",
            "destination_address": "Hotel Example",
            "country_of_application": "India",
            "payment_status": "PAID"
        },
        "documents": [
            {"document_id": "DOC-001", "document_type": "PASSPORT", "file_uri": "gs://x/passport.pdf"},
            {"document_id": "DOC-002", "document_type": "BANK_STATEMENT", "file_uri": "gs://x/bank.pdf"},
            {"document_id": "DOC-003", "document_type": "FLIGHT_ITINERARY", "file_uri": "gs://x/flight.pdf"}
        ],
        "policy_context": {
            "country": "Sri Lanka",
            "policy_version": "sl-tourist-policy-v1",
            "effective_date": "2026-05-25"
        }
    }
    assert client.post("/applications", json=payload).status_code == 201
    assert client.post(f"/cases/{payload['case_id']}/process").status_code == 200

    decision = client.post(
        f"/cases/{payload['case_id']}/officer-decision",
        json={
            "decision": "REJECT",
            "officer_id": "OFF-1",
            "reason": "Officer reached a different conclusion after manual review.",
            "override_reason": ""
        },
    )
    assert decision.status_code == 400
    assert "override_reason is required" in decision.json()["detail"]


def test_enhanced_review_allows_final_decision_without_override_reason(client):
    payload = {
        "case_id": "VISA-2026-DEC-ENH-001",
        "applicant": {
            "full_name": "Arjun Mehta",
            "date_of_birth": "1998-04-12",
            "nationality": "Indian",
            "passport_number": "P1234567",
            "contact_email": "arjun@example.com"
        },
        "visa_application": {
            "visa_class": "TOURIST",
            "purpose_of_travel": "Tourism and sightseeing in Sri Lanka",
            "arrival_date": "2026-08-10",
            "departure_date": "2026-08-20",
            "destination_address": "Hotel Example",
            "country_of_application": "India",
            "payment_status": "PAID"
        },
        "documents": [
            {"document_id": "DOC-001", "document_type": "PASSPORT", "file_uri": "gs://x/passport.pdf"},
            {"document_id": "DOC-002", "document_type": "BANK_STATEMENT", "file_uri": "gs://x/bank.pdf"},
            {"document_id": "DOC-003", "document_type": "FLIGHT_ITINERARY", "file_uri": "gs://x/flight.pdf"}
        ],
        "policy_context": {
            "country": "Sri Lanka",
            "policy_version": "sl-tourist-policy-v1",
            "effective_date": "2026-05-25"
        },
        "mock_profile": {
            "security_status": "SYSTEM_UNAVAILABLE"
        }
    }
    assert client.post("/applications", json=payload).status_code == 201
    process = client.post(f"/cases/{payload['case_id']}/process")
    assert process.status_code == 200
    assert process.json()["recommendation"] == "ENHANCED_REVIEW"

    decision = client.post(
        f"/cases/{payload['case_id']}/officer-decision",
        json={
            "decision": "REJECT",
            "officer_id": "OFF-1",
            "reason": "Officer completed enhanced review and recorded a final refusal.",
            "override_reason": ""
        },
    )
    assert decision.status_code == 200


def test_officer_approval_moves_case_to_port_clearance_follow_up(client):
    payload = {
        "case_id": "VISA-2026-PORT-001",
        "applicant": {
            "full_name": "Arjun Mehta",
            "date_of_birth": "1998-04-12",
            "nationality": "Indian",
            "passport_number": "P1234567",
            "contact_email": "arjun@example.com"
        },
        "visa_application": {
            "visa_class": "TOURIST",
            "purpose_of_travel": "Tourism and sightseeing in Sri Lanka",
            "arrival_date": "2026-08-10",
            "departure_date": "2026-08-20",
            "destination_address": "Hotel Example",
            "country_of_application": "India",
            "payment_status": "PAID"
        },
        "documents": [
            {"document_id": "DOC-001", "document_type": "PASSPORT", "file_uri": "gs://x/passport.pdf"},
            {"document_id": "DOC-002", "document_type": "BANK_STATEMENT", "file_uri": "gs://x/bank.pdf"},
            {"document_id": "DOC-003", "document_type": "FLIGHT_ITINERARY", "file_uri": "gs://x/flight.pdf"}
        ],
        "policy_context": {
            "country": "Sri Lanka",
            "policy_version": "sl-tourist-policy-v1",
            "effective_date": "2026-05-25"
        }
    }
    assert client.post("/applications", json=payload).status_code == 201
    assert client.post(f"/cases/{payload['case_id']}/process").status_code == 200
    decision = client.post(
        f"/cases/{payload['case_id']}/officer-decision",
        json={
            "decision": "APPROVE",
            "officer_id": "OFF-1",
            "reason": "Officer confirmed the case is ready for authorization issuance."
        },
    )
    assert decision.status_code == 200
    status = client.get(f"/cases/{payload['case_id']}/status").json()
    auth = client.get(f"/cases/{payload['case_id']}/authorization-status").json()
    assert status["status"] == "POST_DECISION_FULFILLMENT"
    assert status["current_holder"] == "PORT_OF_ENTRY"
    assert auth["eta_status"] == "ETA_ISSUED"
    assert auth["port_clearance_state"] == "PENDING_PORT_CLEARANCE"


def test_extension_audit_events_exist_and_keep_human_decision_boundary(client):
    payload = {
        "case_id": "VISA-2026-SEC-EXT-001",
        "applicant": {
            "full_name": "Nadeesha Silva",
            "date_of_birth": "1994-02-18",
            "nationality": "Indian",
            "passport_number": "P5551234",
            "contact_email": "nadeesha@example.com",
        },
        "visa_application": {
            "visa_class": "TOURIST",
            "purpose_of_travel": "Tourism and family visit in Sri Lanka",
            "arrival_date": "2026-08-10",
            "departure_date": "2026-08-20",
            "destination_address": "Colombo",
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
        "mock_profile": {
            "extension_requires_appointment": True,
        },
    }
    assert client.post("/applications", json=payload).status_code == 201
    assert (
        client.post(
            f"/cases/{payload['case_id']}/extension-request",
            json={
                "reason": "Need additional stay time for family visit.",
                "requested_new_departure_date": "2026-09-20",
                "supporting_note": "Prepared for extension appointment.",
            },
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/cases/{payload['case_id']}/extension-appointment",
            json={
                "status": "COMPLETED",
                "location": "Battaramulla extension desk",
                "scheduled_for": "2026-08-29T10:00:00Z",
                "instructions": "Bring passport and travel evidence.",
            },
        ).status_code
        == 200
    )
    decision = client.post(
        f"/cases/{payload['case_id']}/extension-decision",
        json={
            "decision": "APPROVE",
            "officer_id": "OFF-EXT-002",
            "reason": "Extension approved after appointment review.",
        },
    )
    assert decision.status_code == 200
    assert decision.json()["human_decision_required"] is True

    audit = client.get(f"/cases/{payload['case_id']}/audit").json()
    assert any(item["event_type"] == "EXTENSION_REQUEST_CREATED" for item in audit)
    assert any(item["event_type"] == "EXTENSION_APPOINTMENT_RECORDED" for item in audit)
    assert any(item["event_type"] == "EXTENSION_DECISION_RECORDED" for item in audit)
