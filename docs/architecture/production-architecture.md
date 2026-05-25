# Production-Ready Architecture

## Design intent

This repository is structured as a modular monolith first, with service boundaries that can later be split into dedicated Cloud Run services without changing the business contracts.

## Layers

### Delivery layer

- `backend/api`
- owns REST endpoints, transport validation, and response shaping

### Application layer

- `backend/services`
- owns case lifecycle logic, audit writing, notification handling, and integration adapters

### Workflow layer

- `backend/workflows`
- owns deterministic routing and orchestration order

### Contract layer

- `backend/models`
- owns Pydantic models, enums, API payloads, and relational persistence records

### Agent/tool contract layer

- `agents`
- `tools`
- owns prompt specs, function interfaces, and guardrails for agent execution

### Knowledge and policy layer

- `rag`
- owns curated policy chunks, refusal templates, document checklists, and officer SOP seed content

### Verification and hardening

- `tests`
- owns contract, workflow, security, and sample-case coverage

## Scalability path

The code is arranged so these slices can later break out cleanly:

- case management API
- document processing service
- policy retrieval service
- security screening adapter
- audit writer
- notification service

## Google Cloud target

- Cloud Run for API/orchestration
- Cloud SQL PostgreSQL for transactional data
- Cloud Storage for documents
- Pub/Sub or Cloud Tasks for asynchronous fan-out
- Vertex AI Agent Builder or Gemini Enterprise Agent Platform for production agent runtime
- Document AI for extraction
- BigQuery for audit analytics
