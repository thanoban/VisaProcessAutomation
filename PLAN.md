# VisaFlow MAS Delivery Plan

## Goal

Build a production-shaped Tourist Visa decision support PoC that automates repetitive manual processing work, routes difficult cases correctly, and produces officer-ready outputs with full auditability.

## Exact operational issues to solve

1. Stop incomplete applications from entering the officer queue.
2. Extract and normalize passport and financial evidence early.
3. Apply policy requirements consistently using retrieved official policy text.
4. Separate low-risk repetitive checks from cases requiring enhanced review.
5. Keep applicant communication structured, fast, and non-legal.
6. Preserve a complete evidence trail for audits, appeals, and anti-corruption review.
7. Record every officer override and tie it back to recommendation history.

## Delivery steps

### Step 1 - Professional repository foundation

- establish scalable folder structure
- add architecture, issue analysis, testing, and security markdown
- define agent contracts, schemas, deployment notes, and operational runbooks

### Step 2 - Core backend implementation

- case intake APIs
- document, financial, policy, security, and risk adapters
- deterministic supervisor workflow
- applicant status and officer brief payloads
- append-only audit event service

### Step 3 - Validation and hardening

- workflow tests for required scenarios
- audit and security boundary tests
- manual API sanity checks
- publish each stable step to GitHub

## Architecture direction

The codebase should remain easy to split later into separate deployable services. Current boundaries are:

- `backend/api` for delivery layer
- `backend/workflows` for orchestration logic
- `backend/services` for application services and adapters
- `backend/models` for typed contracts and database records
- `tools` for explicit agent-callable functions

## Non-negotiables

- no automatic legal approval or refusal
- policy-grounded reasoning only
- minimal disclosure from security systems
- audit event for every meaningful automated or human action
