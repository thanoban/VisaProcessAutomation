# Data Model

## Case record

The case record is the center of the system. It combines:

- applicant identity
- visa application facts
- uploaded documents
- workflow state
- agent outputs
- timeline history
- retention and sensitivity metadata

## Why the model is case-centric

Government review work is fundamentally case-based. Officers, auditors, and appeals bodies all need a coherent view of what happened to one case over time.

## Important fields

### `status_timeline`

Supports applicant transparency, operational reporting, and later SLA analytics.

### `applicant_message_history`

Captures what the applicant was told and when.

### `agent_outputs`

Preserves the structured result of each analysis stage.

### `security_handling_code`

Allows sensitive handling rules without leaking raw security detail.

### `override_required`

Highlights that the officer diverged from the recommendation path.

### `retention_class`

Supports future retention and deletion rules.

## Supporting records

### Document extraction records

Track normalized document extraction results separately from the case summary.

### Agent runs

Track prompt version, model version, hashes, tool calls, evidence IDs, and policy IDs.

### Audit events

Track the compliance-grade timeline of both automated and human actions.

### Officer briefs

Store the exact dashboard-ready payload prepared for the officer.

### Notifications

Track outbound applicant messaging for transparency and troubleshooting.
