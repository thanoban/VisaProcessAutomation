# Production-Ready Architecture

## Design intent

VisaFlow MAS should evolve as a modular monolith first, then split cleanly if needed. The architecture must satisfy two things at once:

1. the real operational lifecycle of a Sri Lanka tourist visa case
2. the hackathon requirement for a code-owned Gemini and Arize observability stack

## Layered structure

### Delivery layer

- `backend/api`
- owns REST endpoints, request validation, role-sensitive response shaping, and integration-safe external contracts

### Agent runtime layer

- Google ADK runtime and agent definitions
- owns Gemini agent composition, structured outputs, tool registration, and runtime-level tracing hooks

### Application layer

- `backend/services`
- owns case lifecycle logic, policy governance, audit persistence, notifications, observability export, and evaluation helpers

### Workflow layer

- `backend/workflows`
- owns deterministic routing, lifecycle transitions, extension handling, and officer-decision orchestration

### Contract and persistence layer

- `backend/models`
- owns typed schemas, workflow entities, audit contracts, and database records

### Knowledge and governance layer

- `rag`
- owns policy chunks, circular references, checklists, refusal templates, and officer SOP content

### Verification layer

- `tests`
- owns workflow, security, observability, and API validation

## Required operational modules

- checklist and intake service
- document QA and validation service
- policy comparison service
- risk and fraud signal service
- officer brief service
- audit service
- observability service
- evaluation runner
- self-improvement analysis service
- extension and appointment service

## Required hackathon modules

- Google ADK root supervisor agent
- Gemini-backed sub-agents or task agents
- OpenInference instrumentation for ADK and Gemini
- Arize Phoenix tracing export
- Phoenix MCP configuration for self-introspection
- evaluation path for weak and failed runs

## Scalability path

The cleanest future service boundaries are:

- public intake API
- officer and supervisor API
- ADK agent runtime service
- document processing service
- policy and circular governance service
- extension and appointment service
- audit and observability service
- analytics and reporting service

## Google Cloud target

- Cloud Run for the web and API runtime
- Cloud SQL PostgreSQL for transactional records
- Cloud Storage for documents and artifacts
- Pub/Sub or Cloud Tasks for asynchronous orchestration
- Gemini through Google Cloud compatible configuration
- Document AI for future production OCR
- BigQuery for audit and evaluation analytics

## Portability rule

Sri Lanka-first business logic, policy governance, and workflow transitions remain platform-neutral. Cloud products, Phoenix exporters, and ADK runtime adapters should remain replaceable around the core domain model.
