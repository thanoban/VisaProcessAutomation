# Deployment Plan

## Target Google Cloud topology

- Cloud Run for API and orchestration
- Cloud SQL PostgreSQL for transactional data
- Cloud Storage for document storage
- Pub/Sub or Cloud Tasks for async processing
- Secret Manager for secrets
- Cloud KMS for keys
- Cloud Logging and Monitoring
- BigQuery for audit analytics
- Cloud Armor and VPC Service Controls for perimeter protection
- Security Command Center for monitoring

## Portability

All external integrations are behind Python service adapters so the PoC can move to sovereign cloud or private infrastructure later.
