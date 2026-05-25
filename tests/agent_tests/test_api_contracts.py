def test_case_status_and_brief_contract(client):
    payload = {
        "case_id": "VISA-2026-API-001",
        "applicant": {
            "full_name": "Kamal Perera",
            "date_of_birth": "1998-04-12",
            "nationality": "Sri Lankan",
            "passport_number": "N1234567",
            "contact_email": "kamal@example.com"
        },
        "visa_application": {
            "visa_class": "TOURIST",
            "purpose_of_travel": "Tourism and sightseeing",
            "arrival_date": "2026-08-10",
            "departure_date": "2026-08-20",
            "destination_address": "Hotel Example",
            "country_of_application": "Sri Lanka",
            "payment_status": "PAID"
        },
        "documents": [
            {"document_id": "DOC-001", "document_type": "PASSPORT", "file_uri": "gs://x/passport.pdf"},
            {"document_id": "DOC-002", "document_type": "BANK_STATEMENT", "file_uri": "gs://x/bank.pdf"},
            {"document_id": "DOC-003", "document_type": "FLIGHT_ITINERARY", "file_uri": "gs://x/flight.pdf"}
        ],
        "policy_context": {
            "country": "Sri Lanka",
            "policy_version": "tourist-policy-v1",
            "effective_date": "2026-05-25"
        }
    }
    assert client.post("/applications", json=payload).status_code == 201
    assert client.post(f"/cases/{payload['case_id']}/process").status_code == 200
    status_response = client.get(f"/cases/{payload['case_id']}/status")
    brief_response = client.get(f"/cases/{payload['case_id']}/officer-brief")
    assert status_response.status_code == 200
    assert brief_response.status_code == 200
    body = brief_response.json()
    assert "recommendation_panel" in body
    assert "evidence_viewer" in body
    assert body["human_decision_required"] is True
