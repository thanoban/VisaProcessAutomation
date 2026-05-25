# Production-Ready Architecture

## Design intent

This repository should evolve as a modular monolith first, then split cleanly into dedicated services if the Sri Lanka deployment matures. The architecture now needs to support not just analysis agents but the actual operational lifecycle of a Sri Lanka short-visit case.

## Layered structure

### Delivery layer

- `backend/api`
- owns REST endpoints, transport validation, external contract stability, and role-sensitive response shaping

### Application layer

- `backend/services`
- owns case lifecycle logic, policy/circular governance, notifications, audit writing, and operational adapters

### Workflow layer

- `backend/workflows`
- owns deterministic lifecycle transitions, routing precedence, manual referral branching, and extension handling

### Contract and persistence layer

- `backend/models`
- owns typed schemas, case entities, timeline events, rule entities, and storage records

### Agent and tool layer

- `agents`
- `tools`
- owns explicit agent responsibilities and callable functions under controlled boundaries

### Knowledge and governance layer

- `rag`
- owns policy chunks, circular references, document checklists, refusal templates, and officer SOP content

### Verification layer

- `tests`
- owns workflow, security, status-tracker, and rule-governance validation

## Operational modules the architecture now needs

- intake and checklist service
- ETA and authorization state service
- document QA and replacement-request service
- manual referral and exception service
- rule publication and circular governance service
- officer brief and recommendation service
- extension and appointment service
- audit and timeline service
- supervisor queue analytics service

## Scalability path

The cleanest future service boundaries are:

- case management API
- ETA/intake service
- document processing service
- policy and circular governance service
- extension and appointment service
- audit service
- notification service
- analytics and supervisor reporting service

## Google Cloud target

- Cloud Run for API and orchestration slices
- Cloud SQL PostgreSQL for transactional records
- Cloud Storage for documents and artifacts
- Pub/Sub or Cloud Tasks for asynchronous orchestration
- Vertex AI Agent Builder or Gemini Enterprise Agent Platform for future managed agent runtime
- Document AI for production extraction
- BigQuery for audit and queue analytics

## Portability rule

Sri Lanka-first business logic, policy governance, and workflow transitions should remain platform-neutral. Cloud products are adapters, not the core of the domain model.
