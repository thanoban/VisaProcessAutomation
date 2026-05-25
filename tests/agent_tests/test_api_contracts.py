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
    assert status_response.status_code == 200
    assert brief_response.status_code == 200
    assert timeline_response.status_code == 200
    assert auth_response.status_code == 200
    assert policy_response.status_code == 200
    assert checklist_response.status_code == 200
    assert governance_response.status_code == 200
    assert queue_response.status_code == 200
    body = brief_response.json()
    status_body = status_response.json()
    auth_body = auth_response.json()
    policy_body = policy_response.json()
    checklist_body = checklist_response.json()
    governance_body = governance_response.json()
    assert "recommendation_panel" in body
    assert "evidence_viewer" in body
    assert body["human_decision_required"] is True
    assert status_body["current_holder"] == "OFFICER"
    assert status_body["authorization_status"]["rule_version_used"] == "sl-rule-pack-2026-05-25"
    assert auth_body["workflow_pack"] == "SRI_LANKA_TOURIST_VISIT"
    assert auth_body["policy_version"] == "sl-tourist-policy-v1"
    assert auth_body["source_uri"].startswith("https://www.immigration.gov.lk/")
    assert policy_body["policy_version"] == "sl-tourist-policy-v1"
    assert policy_body["official_sources"]
    assert checklist_body["country"] == "Sri Lanka"
    assert governance_body["verified_at"] == "2026-05-25"


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
