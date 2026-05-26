from backend.api import routes
from backend.models.schemas import Applicant, CasePacket, DocumentItem, PolicyContext, VisaApplication
from backend.services.observability_service import ObservabilityService


def test_observability_status_endpoint_defaults_to_disabled(client):
    response = client.get("/governance/observability/status")
    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is False
    assert body["status"] == "DISABLED"
    assert body["phoenix_mcp_expected"] is True


def test_observability_service_redacts_pii_and_security_fields():
    service = ObservabilityService()
    case = CasePacket(
        case_id="VISA-2026-OBS-001",
        applicant=Applicant(
            full_name="Kamal Perera",
            date_of_birth="1998-04-12",
            nationality="Sri Lankan",
            passport_number="N1234567",
            contact_email="kamal@example.com",
            phone="+94 771112233",
        ),
        visa_application=VisaApplication(
            visa_class="TOURIST",
            purpose_of_travel="Tourism",
            arrival_date="2026-08-10",
            departure_date="2026-08-20",
            destination_address="Hotel Example",
            country_of_application="Sri Lanka",
            payment_status="PAID",
        ),
        documents=[
            DocumentItem(
                document_id="DOC-001",
                document_type="PASSPORT",
                file_uri="gs://visa-docs/passport.pdf",
            )
        ],
        policy_context=PolicyContext(),
    )
    payload = {
        "full_name": "Kamal Perera",
        "contact_email": "kamal@example.com",
        "nested": {
            "passport_number": "N1234567",
            "file_uri": "gs://visa-docs/passport.pdf",
            "watchlist_details": "classified watchlist record",
            "supporting_note": "private travel detail",
        },
    }

    prepared = service.prepare_export_payload(case, payload, "agent_run")
    assert prepared["payload"]["full_name"] == "[REDACTED]"
    assert prepared["payload"]["contact_email"] == "[REDACTED]"
    assert prepared["payload"]["nested"]["passport_number"] == "[REDACTED]"
    assert prepared["payload"]["nested"]["file_uri"] == "[REDACTED]"
    assert prepared["payload"]["nested"]["watchlist_details"] == "[REDACTED]"
    assert prepared["payload"]["nested"]["supporting_note"] == "[REDACTED]"


def test_observability_failure_does_not_block_case_processing(client, monkeypatch):
    monkeypatch.setattr(routes.workflow.observability_service, "enabled", True)

    def boom():
        raise RuntimeError("phoenix unavailable")

    monkeypatch.setattr(routes.workflow.observability_service, "_get_tracer", boom)

    payload = {
        "case_id": "VISA-2026-OBS-FAIL-001",
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
    assert process_response.json()["human_decision_required"] is True

    audit = client.get(f"/cases/{payload['case_id']}/audit").json()
    assert any(item["observability_export_status"] == "FAILED" for item in audit)


def test_audit_events_include_trace_ids_and_evaluation_labels(client):
    payload = {
        "case_id": "VISA-2026-OBS-AUDIT-001",
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

    audit = client.get(f"/cases/{payload['case_id']}/audit").json()
    agent_audit = [item for item in audit if item["event_type"] == "AGENT_OUTPUT_RECORDED"]
    assert agent_audit
    assert all(item["trace_id"] for item in agent_audit)
    assert all(item["observation_id"] for item in agent_audit)
    assert any("workflow_pack:SRI_LANKA_TOURIST_VISIT" in item["evaluation_labels"] for item in agent_audit)
