# Security Checklist

- RBAC roles defined for applicant, officer, supervisor, admin, auditor, security-reviewer, and governance-owner
- ABAC hook available for sensitive, restricted-nationality, or security-linked cases
- no raw security payload returned to normal workflow components
- applicant-uploaded text never directly controls privileged tool calls
- PII redacted from general logs
- audit records include prompt version, model version, policy version, and rule/circular version where relevant
- override reasons recorded for officer deviations
- manual-referral reasons recorded for exception routes
- encryption-at-rest and in-transit documented in deployment direction
- malware scanning placeholder present on upload path
- retention class available at case level
- official payment-channel guidance must be explicit to reduce scam exposure
- publication mismatch handling must not silently affect officer-facing rule application
