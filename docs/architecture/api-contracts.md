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

Planned endpoint for ETA or authorization state and manual-referral status.

### `POST /cases/{case_id}/additional-evidence-request`

Planned endpoint for creating and tracking additional-document loops.

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

### `GET /supervisor/queues`

Planned endpoint for queue visibility such as pending ETA cases, manual referrals, and extension bottlenecks.

## Governance APIs

### `GET /policies/{visa_class}/requirements`

Returns policy requirements for the given visa class.

### `GET /system/notices`

Returns system-wide public service notices and operational banners.

### `GET /governance/rules/active`

Planned endpoint for the active circular and effective policy version.
