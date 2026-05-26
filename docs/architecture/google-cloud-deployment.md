# Google Cloud Deployment Detail

## Objective

Keep the PoC runnable locally while shaping it for a Google Cloud deployment that satisfies the hackathon rules:

- Gemini-powered agents
- Google ADK code-owned runtime
- FastAPI web app
- Cloud Run deployment path
- Arize Phoenix observability and evaluation

## Sri Lanka-first deployment concerns

- public ETA and status traffic reliability
- manual-referral and extension visibility
- role separation between applicant, officer, supervisor, and governance users
- rule and circular version traceability
- safe AI adoption for a legal-sensitive domain

## Target component map

### Cloud Run

Hosts:

- FastAPI backend
- served frontend surfaces
- Google ADK runtime integration

Possible future split:

- public intake API
- officer and supervisor API
- governance API
- dedicated agent runtime service

### Cloud SQL PostgreSQL

Stores transactional case, timeline, brief, observability metadata, and audit records.

### Cloud Storage

Stores uploaded documents and generated case artifacts.

### Cloud Tasks or Pub/Sub

Supports asynchronous workflows for:

- document processing
- notification delivery
- queue recovery
- extension and appointment handling
- evaluation jobs

### Gemini and Google ADK

The intended runtime path is:

- Google ADK as the primary agent framework
- Gemini model access through Google Cloud compatible configuration
- structured JSON outputs for all agents

### Arize Phoenix

Provides:

- trace collection
- evaluation support
- run comparison
- weak-run inspection
- self-improvement visibility via Phoenix MCP

### Document AI

Future production OCR and document extraction service.

### BigQuery

Future sink for audit analytics, evaluation summaries, and queue metrics.

### Secret Manager and Cloud KMS

Protect credentials, collector keys, and service-to-service trust materials.

## Deployment principles

- keep the Sri Lanka domain model platform-neutral
- isolate Google Cloud and Phoenix integrations behind adapters
- keep human-in-the-loop safety non-bypassable
- never leak raw security data into observability or applicant-facing channels
- preserve portability for sovereign or private-cloud variants later
