# Google Cloud Deployment Detail

## Objective

Keep the PoC runnable locally while shaping it for a Google Cloud production path that supports sovereignty, observability, and controlled AI integration.

## Target component map

### Cloud Run

Hosts the API and orchestration service.

### Cloud SQL PostgreSQL

Stores transactional case, brief, and audit metadata.

### Cloud Storage

Stores uploaded documents and processed artifacts.

### Pub/Sub or Cloud Tasks

Used later for asynchronous workload fan-out, retries, and long-running processing.

### Vertex AI Agent Builder / Gemini Enterprise Agent Platform

Future production runtime for managed agent execution.

### Document AI

Future production OCR and document parsing layer.

### BigQuery

Target audit analytics and operational reporting sink.

### Cloud Logging and Monitoring

Operational logs, metrics, alerting, and incident support.

### Secret Manager

Protects service credentials and integration secrets.

### Cloud KMS

Protects encryption keys and supports envelope encryption patterns.

### Cloud Armor and VPC Service Controls

Add external protection and data-perimeter controls.

## Deployment principles

- keep business logic platform-neutral
- isolate cloud integrations behind adapters
- treat security screening as a stronger trust boundary
- separate operational logs from case evidence stores
- preserve portability for sovereign or private-cloud variants
