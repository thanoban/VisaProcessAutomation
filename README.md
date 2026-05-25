# VisaFlow MAS

VisaFlow MAS is a Sri Lanka-centered, government-grade visa decision support PoC. It is designed around the **current Sri Lanka inbound short-visit process** and benchmarked against stronger operational patterns seen in Canada, the UK, Australia, and the United States.

The goal is not to replace immigration officers. The goal is to automate repetitive manual work, reduce applicant confusion, improve consistency, and produce structured recommendations and operational case tracking while preserving a strict human legal decision boundary.

## Core mission

VisaFlow MAS should help Sri Lanka Immigration process short-visit cases more cleanly across:

- ETA intake and pre-check
- document and file quality review
- nationality and sponsor exceptions
- officer-facing case preparation
- port-of-entry clearance tracking
- extension handling
- rule and circular version control
- audit, supervision, and backlog visibility

## Why this repo is Sri Lanka-first

The current official Sri Lanka process already exposes a mixed operating model:

- ETA is an electronic authorization for short visits, but port-of-entry immigration still performs the final entry clearance.
- Short visits are split across Tourist, Business, and Transit categories.
- Extension handling is split between online services, appointments, and head-office/manual handling.
- Public official channels can show rule-publication mismatches, so policy version governance matters operationally, not just legally.

This repo therefore treats **Sri Lanka Tourist Visit** as the first real workflow pack, while using foreign systems as benchmarks for product quality, not as the legal rules source.

## Foreign benchmark patterns being borrowed

- **Canada IRCC**: personalized checklist, post-submit document loops, biometrics instruction flow, clearer status tracking
- **UK GOV.UK**: document guidance, appointment-centered processing, translation expectations, clearer timing expectations
- **Australia Home Affairs**: appointment and exception handling, biometrics logistics, closure and delay contingencies
- **U.S. State**: strong intake discipline, structured mandatory fields, interview-driven post-specific handling, passport return awareness

## Scope in the repository

- Sri Lanka-centered architecture and runbooks
- FastAPI starter backend
- typed models and JSON schemas
- deterministic case workflow starter
- audit and officer-brief contracts
- local policy and checklist seed materials
- deployment direction for Google Cloud

## Documentation map

- [PLAN.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/PLAN.md)
- [docs/architecture/sri-lanka-current-process.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/docs/architecture/sri-lanka-current-process.md)
- [docs/architecture/government-process-benchmark.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/docs/architecture/government-process-benchmark.md)
- [docs/architecture/current-method-comparison.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/docs/architecture/current-method-comparison.md)
- [docs/architecture/policy-publication-governance.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/docs/architecture/policy-publication-governance.md)
- [docs/architecture/production-architecture.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/docs/architecture/production-architecture.md)
- [docs/runbooks/pilot-discovery-plan.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/docs/runbooks/pilot-discovery-plan.md)
- [docs/runbooks/security-checklist.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/docs/runbooks/security-checklist.md)
- [docs/runbooks/testing-checklist.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/docs/runbooks/testing-checklist.md)

## Local run

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload --app-dir .
pytest
```

The app still defaults to SQLite for local development. The target production direction remains Cloud SQL PostgreSQL and Google Cloud-hosted services behind clearly isolated adapters.

## Safety boundary

- the system never auto-approves or auto-rejects a visa
- every recommendation requires human review
- policy and circular governance must be versioned and auditable
- security outputs stay minimal and compartmentalized
- applicant-facing messages must stay procedural and non-legal until human action is recorded
