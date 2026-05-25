# Agent Catalog

## Supervisor Agent

### Purpose

Own workflow coordination and recommendation routing.

### Must do

- call the right agents in the right order
- enforce deterministic routing rules
- always require human decision

### Must not do

- make the final legal decision
- invent facts or policy

## Intake & Completeness Agent

### Purpose

Stop incomplete or obviously invalid cases before they reach deeper analysis or officer review.

### Checks

- required fields
- required uploads
- payment state
- duplicate uploads
- basic invalid or unreadable input conditions

## Document Validator Agent

### Purpose

Normalize identity and travel-document evidence into a consistent structure.

### Checks

- passport fields
- expiry
- MRZ consistency
- name match
- basic tampering indicators

## Financial & Employment Evaluator Agent

### Purpose

Convert financial evidence into a fast officer-readable summary and detect obvious concern patterns.

### Checks

- average balance
- suspicious deposits
- salary consistency
- employment tie strength
- home-country tie strength

## Policy & Compliance Agent

### Purpose

Map case facts against retrieved official visa policy requirements.

### Output style

Requirement-by-requirement matrix with status, evidence IDs, and reasons.

## Security & Background Auditor Agent

### Purpose

Represent restricted system checks without leaking raw sensitive data.

### Output style

Minimal codes only.

## Risk & Fraud Assessment Agent

### Purpose

Detect non-protected, evidence-based fraud or anomaly signals.

### Key rule

High risk triggers enhanced human review, not hidden auto-refusal.

## Officer Liaison Agent

### Purpose

Package the case for fast officer review.

### Output

- case summary
- recommendation
- policy references
- risk flags
- questions for officer
- evidence viewer payload

## Applicant Communication Agent

### Purpose

Turn workflow state into respectful, simple next-step messages.

### Restrictions

- no legal conclusion before human action
- no security disclosure

## Audit & Compliance Agent

### Purpose

Create the history needed for governance, appeal review, and internal integrity monitoring.
