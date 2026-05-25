# Security Checklist

- RBAC roles defined for applicant, officer, supervisor, admin, auditor, and security-reviewer
- ABAC hook available for sensitive or security-linked cases
- no raw security payload returned to normal workflow components
- applicant-uploaded text never directly controls privileged tool calls
- PII redacted from general logs
- audit records include prompt version, model version, and policy version
- override reasons recorded for officer deviations
- encryption-at-rest and in-transit documented in deployment plan
- malware scanning placeholder present on upload path
- retention class available at case level
