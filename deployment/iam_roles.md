# IAM Roles

- Applicant frontend service account: upload to scoped document bucket only
- Officer dashboard service account: read case, brief, and audit APIs
- Supervisor/admin service account: queue and backlog visibility
- Audit exporter service account: append-only audit sink access
- Security screening service account: isolated access to restricted screening adapter
- Deployment service account: Cloud Run, Cloud SQL, Secret Manager, KMS, Logging, Pub/Sub
