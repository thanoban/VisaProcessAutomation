# Deployment Plan

## Goal

Deploy VisaFlow MAS as a web application that satisfies the Google Cloud Partner hackathon architecture expectations while preserving a clean path to a more secure production topology.

## Current target stack

- FastAPI backend
- lightweight web frontend served by FastAPI
- Google ADK runtime path for Gemini-powered agents
- Arize Phoenix for observability and evaluation
- SQLite locally
- PostgreSQL direction for production

## Preferred Google Cloud topology

- **Cloud Run** for the public API and web runtime
- **Cloud SQL PostgreSQL** for transactional case and audit storage
- **Cloud Storage** for uploaded documents and generated artifacts
- **Cloud Tasks** or **Pub/Sub** for async orchestration
- **Secret Manager** for secrets
- **Cloud KMS** for encryption key management
- **Cloud Logging** and **Cloud Monitoring**
- **BigQuery** for audit analytics and queue reporting
- **Cloud Armor** and **VPC Service Controls**
- **Security Command Center**

## Gemini and ADK alignment

The intended agent stack is:

- Google ADK as the code-owned runtime
- Gemini model access through Google Cloud compatible configuration
- OpenInference instrumentation for ADK and Gemini calls
- Arize Phoenix as the trace and evaluation sink

Current implementation notes:

- visa routing remains deterministic in the workflow layer
- the ADK runtime currently powers the self-improvement review lane
- the runtime can operate in mock-safe local mode when `GOOGLE_API_KEY` is absent

## Arize track notes

See:

- [deployment/arize_phoenix_setup.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/deployment/arize_phoenix_setup.md)
- [deployment/mcp/phoenix-mcp.sample.json](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/deployment/mcp/phoenix-mcp.sample.json)

## Portability

All external integrations are isolated behind Python service adapters so the PoC can later move to sovereign cloud or private infrastructure without rewriting the Sri Lanka workflow model.
