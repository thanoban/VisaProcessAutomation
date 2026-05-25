# Project Structure

## Why the repository is organized this way

The repository is intentionally shaped as a modular monolith. That keeps the PoC fast to iterate on while preserving clear future split points for service decomposition.

## Top-level layout

### `agents/`

Prompt and policy behavior specifications for each specialized agent.

### `backend/`

Runnable backend application code.

#### `backend/api/`

Transport layer, FastAPI routes, and request/response binding.

#### `backend/workflows/`

Deterministic orchestration and routing logic.

#### `backend/services/`

Application services and adapter-like behaviors such as case persistence, audit writing, notifications, and policy loading.

#### `backend/models/`

Typed contracts and relational record definitions.

#### `backend/database/`

Connection and database bootstrap.

### `tools/`

Explicit tool functions that model what agents are allowed to call.

### `schemas/`

JSON schema definitions aligned with typed runtime models.

### `rag/`

Policy corpus, document checklists, refusal templates, and officer SOP seed content.

### `tests/`

Workflow, security, and contract verification.

### `deployment/`

Cloud deployment notes and target platform configuration placeholders.

### `docs/`

Architecture, process analysis, roadmap, security, and testing explanation.

## Scalability path

If the PoC grows, the cleanest future splits are:

- `case-api`
- `orchestration-service`
- `document-service`
- `policy-service`
- `security-screening-adapter`
- `audit-service`
- `notification-service`
