# VisaFlow MAS

VisaFlow MAS is a backend-first, government-grade visa decision support PoC for Tourist visa processing. It is built to automate slow manual checks, prepare officer-facing case briefs, reduce backlog on low-risk repetitive work, and preserve full human legal control over the final decision.

## Real processing problems this PoC targets

- incomplete or poor-quality applications arriving at officers too early
- officers manually checking the same document basics across large queues
- disconnected policy, document, fraud, and watchlist workflows
- weak traceability between recommendation, policy section, and evidence item
- slow applicant follow-up cycles when more information is needed
- inconsistent reasoning quality across officers and locations
- poor auditability of overrides, tool use, and model behavior

## Scope in this repository

- deterministic case workflow for Tourist visa cases
- typed agent and tool contracts
- FastAPI service for case submission, processing, review, status, and audit
- local policy retrieval starter for policy-grounded decisions
- officer brief payload for a future dashboard
- append-only audit event recording
- deployment and IAM notes for a Google Cloud target architecture

## Project structure

- [PLAN.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/PLAN.md)
- [docs/architecture/production-architecture.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/docs/architecture/production-architecture.md)
- [docs/architecture/real-world-issues.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/docs/architecture/real-world-issues.md)
- [docs/runbooks/security-checklist.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/docs/runbooks/security-checklist.md)
- [docs/runbooks/testing-checklist.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/docs/runbooks/testing-checklist.md)

## Local run

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload --app-dir .
pytest
```

The app defaults to SQLite for local development. The data model and deployment plan target Cloud SQL PostgreSQL for the intended production-style Google Cloud setup.

## Safety boundary

- the system never auto-approves or auto-rejects a visa
- every recommendation requires human officer review
- policy analysis must use retrieved policy content only
- security screening is minimal-code output only
- audit records capture prompt version, model version, policy version, hashes, tool calls, and override reasons
