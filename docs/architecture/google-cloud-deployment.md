# Google Cloud Deployment Detail

## Objective

Keep the PoC runnable locally while shaping it for a Google Cloud production path that can support a Sri Lanka Immigration-scale service model, strong audit requirements, and controlled AI integration.

## Sri Lanka-first deployment concerns

- public service reliability for ETA and status traffic
- operational visibility for manual referrals and extension queues
- separation of public applicant traffic from internal officer tooling
- strong rule and circular version control
- auditability suitable for ministry, parliamentary, and integrity review

## Target component map

### Cloud Run

Hosts API and orchestration services. Over time, these may split into:

- public intake API
- officer and supervisor API
- workflow orchestration service
- governance and rule service

### Cloud SQL PostgreSQL

Stores transactional case, timeline, brief, and audit metadata.

### Cloud Storage

Stores uploaded documents, transformed artifacts, and generated evidence bundles.

### Pub/Sub or Cloud Tasks

Supports asynchronous orchestration for:

- document processing
- notifications
- queue recovery
- extension and appointment workflows

### Vertex AI Agent Builder / Gemini Enterprise Agent Platform

Future managed runtime for agent execution once the PoC stabilizes.

### Document AI

Future production OCR and document extraction service.

### BigQuery

Stores audit analytics, queue metrics, and operational reporting aggregates.

### Secret Manager and Cloud KMS

Protect system credentials, encryption keys, and service-to-service trust material.

## Deployment principles

- keep the Sri Lanka domain model platform-neutral
- isolate cloud integrations behind adapters
- separate public, officer, and governance responsibilities clearly
- preserve portability for sovereign or private-cloud variants if required later
