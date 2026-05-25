# VisaFlow MAS Delivery Plan

## 1. Mission

Build a production-shaped Tourist Visa decision support PoC that automates repetitive manual processing work, reduces officer queue pressure, routes difficult cases correctly, and produces officer-ready outputs with full auditability and explainability.

The system is not a legal decision engine. It is an automation and recommendation layer that sits before the human decision maker.

## 2. What must be true when this PoC is successful

### Applicant experience

- applicant can submit a Tourist visa case
- applicant can upload evidence
- applicant receives structured next-step messages
- applicant can see meaningful status states instead of a generic pending state

### Officer experience

- officer receives a brief with document findings, financial summary, policy references, and risk flags
- officer sees what evidence and policy sections drove the recommendation
- officer can still approve, reject, request more information, or escalate
- officer overrides are recorded cleanly

### Governance and compliance

- every automated step is auditable
- policy use is traceable to retrieved sections
- model and prompt versions are recorded
- security results are restricted to minimal codes
- the system cannot silently make a final legal decision

## 3. Exact operational issues to solve

1. Stop incomplete applications from entering the officer queue.
2. Extract and normalize passport and financial evidence early.
3. Apply policy requirements consistently using retrieved official policy text.
4. Separate low-risk repetitive checks from cases requiring enhanced review.
5. Keep applicant communication structured, fast, and non-legal.
6. Preserve a complete evidence trail for audits, appeals, and anti-corruption review.
7. Record every officer override and tie it back to recommendation history.
8. Reduce context switching between document review, policy lookup, and queue handling.
9. Improve consistency across officers, locations, and missions.
10. Create an architecture that can grow from Tourist to Student, Work, and Family visas later.

## 4. Operating assumptions

- Tourist visa is the first supported class
- security, fraud, and previous-history checks are mocked in this phase but shaped as production adapters
- policy corpus is local in this phase but structured for later Vertex AI RAG or Vector Search migration
- local development uses SQLite, while the production target remains Cloud SQL PostgreSQL
- frontend remains API-first in this phase while officer/applicant UIs are stabilized through contracts

## 5. Delivery steps

### Step 1 - Professional repository foundation

- establish scalable folder structure
- add architecture, issue analysis, testing, and security markdown
- define agent contracts, schemas, deployment notes, and operational runbooks
- document the government-process problem, not just the code structure

### Step 2 - Core backend implementation

- case intake APIs
- document, financial, policy, security, and risk adapters
- deterministic supervisor workflow
- applicant status and officer brief payloads
- append-only audit event service
- policy retrieval starter and dashboard-shaped response models

### Step 3 - Validation and hardening

- workflow tests for required scenarios
- audit and security boundary tests
- manual API sanity checks
- recommendation precedence verification
- publish each stable step to GitHub

## 6. Architecture direction

The codebase should remain easy to split later into separate deployable services. Current boundaries are:

- `backend/api` for delivery layer
- `backend/workflows` for orchestration logic
- `backend/services` for application services and adapters
- `backend/models` for typed contracts and database records
- `tools` for explicit agent-callable functions
- `rag` for policy, refusal, SOP, and checklist knowledge assets
- `tests` for workflow, security, and contract verification

## 7. Non-negotiables

- no automatic legal approval or refusal
- policy-grounded reasoning only
- minimal disclosure from security systems
- audit event for every meaningful automated or human action
- no protected attributes in risk scoring
- clear human accountability for the final action
