# Project Structure

## Why the repository is organized this way

The repository is intentionally shaped as a modular monolith so we can move quickly while still preserving clean boundaries for a future Sri Lanka production deployment. The structure is meant to support both:

- the legal decision-support layer
- the operational lifecycle around ETA, manual referral, extension, and timeline tracking

## Top-level layout

### `agents/`

Prompt and behavior specifications for the specialized agents that prepare analysis and summaries.

### `backend/`

Runnable backend application code.

#### `backend/api/`

Transport layer, FastAPI routes, and response shaping for applicant, officer, and supervisor use cases.

#### `backend/workflows/`

Deterministic lifecycle and routing logic for Sri Lanka workflow packs.

#### `backend/services/`

Application services and adapters such as case persistence, audit writing, notifications, policy loading, and future circular governance.

#### `backend/models/`

Typed contracts, workflow entities, and relational record definitions.

#### `backend/database/`

Connection and database bootstrap.

### `tools/`

Explicit tool functions that model what agents are allowed to call.

### `schemas/`

JSON schema definitions aligned with typed runtime models.

### `rag/`

Policy corpus, circular references, document checklists, refusal templates, and officer SOP seed content.

### `tests/`

Workflow, security, contract, and status-clarity verification.

### `deployment/`

Cloud deployment notes and target platform configuration placeholders.

### `docs/`

Architecture, process analysis, benchmark comparison, roadmap, security, and testing explanation.

## Scalability path

If the PoC grows, the cleanest future split points are:

- `case-api`
- `eta-intake-service`
- `orchestration-service`
- `policy-governance-service`
- `document-service`
- `extension-appointment-service`
- `audit-service`
- `notification-service`
