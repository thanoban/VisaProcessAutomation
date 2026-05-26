def test_end_to_end_document_loop_to_port_clearance_journey(client):
    payload = {
        "case_id": "VISA-2026-E2E-001",
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
            {"document_id": "DOC-003", "document_type": "FLIGHT_ITINERARY", "file_uri": "gs://x/flight.pdf"},
        ],
        "policy_context": {
            "country": "Sri Lanka",
            "policy_version": "sl-tourist-policy-v1",
            "effective_date": "2026-05-25",
        },
        "decision_due_at": "2026-06-03T17:00:00Z",
    }

    create_response = client.post("/applications", json=payload)
    assert create_response.status_code == 201

    first_process = client.post(f"/cases/{payload['case_id']}/process")
    assert first_process.status_code == 200
    assert first_process.json()["recommendation"] == "REQUEST_MORE_INFO"

    waiting_status = client.get(f"/cases/{payload['case_id']}/status")
    assert waiting_status.status_code == 200
    waiting_body = waiting_status.json()
    assert waiting_body["status"] == "WAITING_FOR_DOCUMENTS"
    assert waiting_body["current_holder"] == "APPLICANT"
    assert waiting_body["required_actions"]
    assert waiting_body["latest_message"]["subject"]

    queue_waiting = client.get("/supervisor/cases?state=WAITING_FOR_DOCUMENTS&holder=APPLICANT")
    assert queue_waiting.status_code == 200
    queue_waiting_body = queue_waiting.json()
    assert any(item["case_id"] == payload["case_id"] for item in queue_waiting_body["cases"])

    upload_response = client.post(
        f"/cases/{payload['case_id']}/documents",
        json={
            "documents": [
                {
                    "document_id": "DOC-002",
                    "document_type": "BANK_STATEMENT",
                    "file_uri": "gs://x/bank-replacement.pdf",
                    "status": "UPLOADED",
                }
            ]
        },
    )
    assert upload_response.status_code == 200

    second_process = client.post(f"/cases/{payload['case_id']}/process")
    assert second_process.status_code == 200
    assert second_process.json()["recommendation"] == "APPROVE_READY"

    brief_response = client.get(f"/cases/{payload['case_id']}/officer-brief")
    assert brief_response.status_code == 200
    brief_body = brief_response.json()
    assert brief_body["recommendation"] == "APPROVE_READY"
    assert brief_body["human_decision_required"] is True

    decision_response = client.post(
        f"/cases/{payload['case_id']}/officer-decision",
        json={
            "decision": "APPROVE",
            "officer_id": "OFFICER-001",
            "reason": "Officer confirmed the case is ready for authorization issuance.",
        },
    )
    assert decision_response.status_code == 200

    final_status = client.get(f"/cases/{payload['case_id']}/status")
    assert final_status.status_code == 200
    final_body = final_status.json()
    assert final_body["status"] == "POST_DECISION_FULFILLMENT"
    assert final_body["current_holder"] == "PORT_OF_ENTRY"
    assert final_body["authorization_status"]["eta_status"] == "ETA_ISSUED"
    assert final_body["port_clearance_state"] == "PENDING_PORT_CLEARANCE"
    assert "port-of-entry clearance" in final_body["latest_message"]["message"].lower()

    queue_port = client.get("/supervisor/cases?state=POST_DECISION_FULFILLMENT&holder=PORT_OF_ENTRY")
    assert queue_port.status_code == 200
    queue_port_body = queue_port.json()
    assert any(item["case_id"] == payload["case_id"] for item in queue_port_body["cases"])

    audit_response = client.get(f"/cases/{payload['case_id']}/audit")
    assert audit_response.status_code == 200
    audit_body = audit_response.json()
    assert any(item["event_type"] == "OFFICER_DECISION_RECORDED" for item in audit_body)


def test_end_to_end_extension_journey(client):
    payload = {
        "case_id": "VISA-2026-E2E-EXT-001",
        "applicant": {
            "full_name": "Maya Raman",
            "date_of_birth": "1991-07-21",
            "nationality": "Indian",
            "passport_number": "P4321876",
            "contact_email": "maya@example.com",
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

    extension_request = client.post(
        f"/cases/{payload['case_id']}/extension-request",
        json={
            "reason": "Need more time to complete family visit plans.",
            "requested_new_departure_date": "2026-09-20",
            "supporting_note": "Prepared to attend an appointment if required.",
        },
    )
    assert extension_request.status_code == 200
    assert extension_request.json()["extension_state"] == "EXTENSION_APPOINTMENT_REQUIRED"

    appointment = client.post(
        f"/cases/{payload['case_id']}/extension-appointment",
        json={
            "status": "COMPLETED",
            "location": "Battaramulla extension desk",
            "scheduled_for": "2026-08-29T10:00:00Z",
            "instructions": "Bring passport and travel evidence.",
        },
    )
    assert appointment.status_code == 200
    assert appointment.json()["extension_state"] == "UNDER_EXTENSION_REVIEW"

    decision = client.post(
        f"/cases/{payload['case_id']}/extension-decision",
        json={
            "decision": "APPROVE",
            "officer_id": "OFF-EXT-002",
            "reason": "Extension approved after appointment review.",
        },
    )
    assert decision.status_code == 200
    assert decision.json()["extension_state"] == "EXTENSION_DECISION_RECORDED"

    final_status = client.get(f"/cases/{payload['case_id']}/status")
    assert final_status.status_code == 200
    final_body = final_status.json()
    assert final_body["status"] == "EXTENSION_DECISION_RECORDED"
    assert final_body["extension_state"] == "EXTENSION_DECISION_RECORDED"
    assert final_body["latest_message"]["subject"]
    assert final_body["appointments"]

    audit_response = client.get(f"/cases/{payload['case_id']}/audit")
    assert audit_response.status_code == 200
    audit_body = audit_response.json()
    assert any(item["event_type"] == "EXTENSION_REQUEST_CREATED" for item in audit_body)
    assert any(item["event_type"] == "EXTENSION_APPOINTMENT_RECORDED" for item in audit_body)
    assert any(item["event_type"] == "EXTENSION_DECISION_RECORDED" for item in audit_body)
