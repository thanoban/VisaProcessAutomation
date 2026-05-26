import io


def test_case_status_and_brief_contract(client):
    payload = {
        "case_id": "VISA-2026-API-001",
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
    status_response = client.get(f"/cases/{payload['case_id']}/status")
    brief_response = client.get(f"/cases/{payload['case_id']}/officer-brief")
    timeline_response = client.get(f"/cases/{payload['case_id']}/timeline")
    auth_response = client.get(f"/cases/{payload['case_id']}/authorization-status")
    policy_response = client.get("/policies/TOURIST/requirements")
    checklist_response = client.get("/checklists/tourist-visit")
    governance_response = client.get("/governance/rules/active")
    queue_response = client.get("/supervisor/queues")
    queue_cases_response = client.get("/supervisor/cases")
    filtered_queue_cases_response = client.get("/supervisor/cases?state=READY_FOR_OFFICER_REVIEW&holder=OFFICER")
    assert status_response.status_code == 200
    assert brief_response.status_code == 200
    assert timeline_response.status_code == 200
    assert auth_response.status_code == 200
    assert policy_response.status_code == 200
    assert checklist_response.status_code == 200
    assert governance_response.status_code == 200
    assert queue_response.status_code == 200
    assert queue_cases_response.status_code == 200
    assert filtered_queue_cases_response.status_code == 200
    body = brief_response.json()
    status_body = status_response.json()
    auth_body = auth_response.json()
    policy_body = policy_response.json()
    checklist_body = checklist_response.json()
    governance_body = governance_response.json()
    queue_cases_body = queue_cases_response.json()
    filtered_queue_cases_body = filtered_queue_cases_response.json()
    assert "recommendation_panel" in body
    assert "evidence_viewer" in body
    assert body["human_decision_required"] is True
    assert status_body["current_holder"] == "OFFICER"
    assert status_body["authorization_status"]["rule_version_used"] == "sl-rule-pack-2026-05-25"
    assert auth_body["workflow_pack"] == "SRI_LANKA_TOURIST_VISIT"
    assert auth_body["policy_version"] == "sl-tourist-policy-v1"
    assert auth_body["source_uri"].startswith("https://www.immigration.gov.lk/")
    assert policy_body["policy_version"] == "sl-tourist-policy-v1"
    assert policy_body["workflow_pack"] == "SRI_LANKA_TOURIST_VISIT"
    assert policy_body["source_uri"].startswith("https://www.immigration.gov.lk/")
    assert policy_body["official_sources"]
    assert checklist_body["country"] == "Sri Lanka"
    assert governance_body["verified_at"] == "2026-05-25"
    assert governance_body["country"] == "Sri Lanka"
    assert governance_body["active_circulars"]
    assert governance_body["active_circulars"][0]["publications"]
    assert any(rule["nationality"] == "NIGERIA" for rule in governance_body["nationality_exception_rules"])
    assert queue_cases_body["total_cases"] >= 1
    assert queue_cases_body["cases"]
    assert queue_cases_body["cases"][0]["rule_version_used"] == "sl-rule-pack-2026-05-25"
    assert filtered_queue_cases_body["filtered_count"] >= 1
    assert filtered_queue_cases_body["state_filter"] == "READY_FOR_OFFICER_REVIEW"
    assert all(item["current_holder"] == "OFFICER" for item in filtered_queue_cases_body["cases"])


def test_document_response_upload_reprocesses_case(client):
    payload = {
        "case_id": "VISA-2026-API-RESP-001",
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
    }
    assert client.post("/applications", json=payload).status_code == 201
    initial_result = client.post(f"/cases/{payload['case_id']}/process")
    assert initial_result.status_code == 200
    assert initial_result.json()["recommendation"] == "REQUEST_MORE_INFO"

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
    upload_body = upload_response.json()
    assert upload_body["workflow"]["next_action"] == "RECHECK_SUBMITTED_DOCUMENTS"

    rerun = client.post(f"/cases/{payload['case_id']}/process")
    assert rerun.status_code == 200
    assert rerun.json()["recommendation"] == "APPROVE_READY"

    final_case = client.get(f"/cases/{payload['case_id']}").json()
    bank_documents = [doc for doc in final_case["documents"] if doc["document_type"] == "BANK_STATEMENT"]
    assert len(bank_documents) == 1


def test_waiting_case_status_exposes_evidence_request_details(client):
    payload = {
        "case_id": "VISA-2026-API-WAIT-001",
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
    }
    assert client.post("/applications", json=payload).status_code == 201
    assert client.post(f"/cases/{payload['case_id']}/process").status_code == 200

    status_response = client.get(f"/cases/{payload['case_id']}/status")
    assert status_response.status_code == 200
    body = status_response.json()
    assert body["status"] == "WAITING_FOR_DOCUMENTS"
    assert body["required_actions"]
    assert body["additional_evidence_requests"]
    assert body["additional_evidence_requests"][0]["status"] == "OPEN"


def test_reprocessing_waiting_case_does_not_duplicate_open_evidence_requests(client):
    payload = {
        "case_id": "VISA-2026-API-DUPE-001",
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
    }
    assert client.post("/applications", json=payload).status_code == 201
    first = client.post(f"/cases/{payload['case_id']}/process")
    second = client.post(f"/cases/{payload['case_id']}/process")
    assert first.status_code == 200
    assert second.status_code == 200

    case_response = client.get(f"/cases/{payload['case_id']}")
    assert case_response.status_code == 200
    open_requests = [
        request
        for request in case_response.json()["workflow"]["additional_evidence_requests"]
        if request["status"] == "OPEN"
    ]
    assert len(open_requests) == 1
    assert open_requests[0]["requested_items"] == ["BANK_STATEMENT"]


def test_file_upload_endpoint_stores_document_locally(client, monkeypatch, tmp_path):
    monkeypatch.setenv("VISAFLOW_UPLOAD_DIR", str(tmp_path))

    payload = {
        "case_id": "VISA-2026-API-FILE-001",
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
        "documents": [],
        "policy_context": {
            "country": "Sri Lanka",
            "policy_version": "sl-tourist-policy-v1",
            "effective_date": "2026-05-25",
        },
    }
    assert client.post("/applications", json=payload).status_code == 201

    upload_response = client.post(
        f"/cases/{payload['case_id']}/document-files",
        data={"document_type": "PASSPORT"},
        files={"file": ("passport.pdf", io.BytesIO(b"passport-content"), "application/pdf")},
    )
    assert upload_response.status_code == 200
    body = upload_response.json()
    assert len(body["documents"]) == 1
    document = body["documents"][0]
    assert document["document_type"] == "PASSPORT"
    assert document["uploaded_at"]
    assert document["file_uri"].endswith(".pdf")
    assert tmp_path.name in document["file_uri"]


def test_manual_referral_status_exposes_appointments_and_reason(client):
    payload = {
        "case_id": "VISA-2026-API-REFERRAL-001",
        "applicant": {
            "full_name": "Amina Yusuf",
            "date_of_birth": "1992-11-22",
            "nationality": "NIGERIA",
            "passport_number": "N9988776",
            "contact_email": "amina@example.com",
        },
        "visa_application": {
            "visa_class": "TOURIST",
            "purpose_of_travel": "Tourism in Sri Lanka with sponsor support",
            "arrival_date": "2026-09-14",
            "departure_date": "2026-09-24",
            "destination_address": "Colombo guest house",
            "country_of_application": "Nigeria",
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
    assert client.post("/applications", json=payload).status_code == 201
    process_response = client.post(f"/cases/{payload['case_id']}/process")
    assert process_response.status_code == 200
    assert process_response.json()["recommendation"] == "ENHANCED_REVIEW"

    status_response = client.get(f"/cases/{payload['case_id']}/status")
    assert status_response.status_code == 200
    body = status_response.json()
    assert body["status"] == "REFERRED_TO_MANUAL_REVIEW"
    assert body["manual_referral_reason"]
    assert body["appointments"]
    assert body["appointments"][0]["appointment_type"] == "MANUAL_REFERRAL_REVIEW"
    assert any(notice["code"] == "MANUAL_REFERRAL_ACTIVE" for notice in body["service_notices"])


def test_approved_case_status_exposes_decision_notice_and_port_follow_up(client):
    payload = {
        "case_id": "VISA-2026-API-APPROVAL-001",
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
    assert client.post("/applications", json=payload).status_code == 201
    process_response = client.post(f"/cases/{payload['case_id']}/process")
    assert process_response.status_code == 200
    assert process_response.json()["recommendation"] == "APPROVE_READY"

    decision_response = client.post(
        f"/cases/{payload['case_id']}/officer-decision",
        json={
            "decision": "APPROVE",
            "officer_id": "officer-007",
            "reason": "Core tourist requirements satisfied.",
            "override_reason": "",
        },
    )
    assert decision_response.status_code == 200

    status_response = client.get(f"/cases/{payload['case_id']}/status")
    assert status_response.status_code == 200
    body = status_response.json()
    assert body["status"] == "POST_DECISION_FULFILLMENT"
    assert body["decision_notice"]
    assert body["decision_notice"]["subject"]
    assert body["port_clearance_events"]
    assert body["port_clearance_events"][0]["status"] == "PENDING_PORT_CLEARANCE"
    assert any(notice["code"] == "PORT_CLEARANCE_PENDING" for notice in body["service_notices"])
