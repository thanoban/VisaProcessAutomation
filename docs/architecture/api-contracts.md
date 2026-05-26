# API Contracts

## Core case APIs

### `POST /applications`

Creates a Sri Lanka Tourist Visit case with applicant data, ETA-related facts, and optional initial documents.

### `POST /cases/{case_id}/documents`

Attaches or replaces uploaded documents for the case.

### `POST /cases/{case_id}/process`

Runs the deterministic Sri Lanka case workflow and returns the current supervisor output.

### `GET /cases/{case_id}`

Returns the full case packet.

## Applicant-facing operational APIs

### `GET /cases/{case_id}/status`

Returns the applicant-facing status view:

- current operational state
- latest message
- required actions
- uploaded-document summary
- next deadline
- action owner
- status timeline

### `GET /cases/{case_id}/timeline`

Returns timeline events for applicant and operational tracking.

### `GET /checklists/tourist-visit`

Returns the Sri Lanka Tourist Visit checklist starter.

### `GET /cases/{case_id}/authorization-status`

Returns ETA or authorization state and manual-referral status.

### `POST /cases/{case_id}/extension-request`

Creates an extension request for an existing case.

### `GET /cases/{case_id}/extension-status`

Returns extension workflow state, latest message, and appointment information.

### `POST /cases/{case_id}/extension-appointment`

Records appointment details for the extension workflow.

### `POST /cases/{case_id}/extension-decision`

Records the extension outcome from a human officer or extension desk user.

## Officer and supervisor APIs

### `GET /cases/{case_id}/officer-brief`

Returns the officer dashboard payload with:

- case summary
- recommendation panel
- agent cards
- evidence viewer
- rule and policy references
- risk and manual-referral flags
- audit timeline

### `POST /cases/{case_id}/officer-decision`

Stores the final human action and optional override reason.

### `GET /cases/{case_id}/audit`

Returns audit events for the case.

Audit events now also carry observability metadata such as:

- trace ID
- observation ID
- observability export status
- observability target
- evaluation labels

### `GET /supervisor/queues`

Returns queue visibility such as pending ETA cases, manual referrals, deadline urgency, and extension bottlenecks.

### `GET /supervisor/cases`

Returns supervisor case summaries with state, holder, urgency, and policy metadata.

## Governance APIs

### `GET /policies/{visa_class}/requirements`

Returns policy requirements for the given visa class.

### `GET /system/notices`

Returns system-wide public service notices and operational banners.

### `GET /governance/rules/active`

Returns the active circular and effective policy version.

### `GET /governance/observability/status`

Returns the current Phoenix observability status for the deployment target.

The observability status payload is intended to expose:

- enabled or disabled state
- provider name
- target name
- project name
- ADK or Gemini instrumentation posture
- Phoenix MCP expectation

### `GET /governance/agent-runtime/status`

Returns the current Google ADK and Gemini runtime posture for the deployment target.

The payload exposes:

- runtime and provider
- configured versus mock-only state
- model name
- ADK and GenAI instrumentation posture
- Phoenix MCP config presence
- configured agent names

### `POST /cases/{case_id}/self-improvement/review`

Runs the Self-Improvement Agent against the selected case using Google ADK.

The response includes:

- runtime mode
- failure summary
- detected issues
- proposed safer changes
- comparison questions
- human approval requirement
- observability metadata
