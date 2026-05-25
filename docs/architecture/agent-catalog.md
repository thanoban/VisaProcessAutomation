# Agent Catalog

## Supervisor Agent

### Purpose

Own workflow coordination, lifecycle transitions, and recommendation routing for the Sri Lanka workflow pack.

### Must do

- call the right agents in the right order
- enforce deterministic routing rules
- preserve operational states separately from legal recommendation categories
- always require human decision for legal outcome

### Must not do

- make the final legal decision
- invent facts, policy, or circular status

## Intake & Completeness Agent

### Purpose

Stop incomplete, unreadable, or obviously misrouted cases before they reach deeper analysis or officer review.

### Checks

- required fields
- required uploads
- payment state
- duplicate uploads
- unreadable or invalid files
- obvious nationality or sponsor exception triggers

## Document Validator Agent

### Purpose

Normalize identity and travel-document evidence into a consistent structure.

### Checks

- passport fields
- expiry
- MRZ consistency
- name match
- basic tampering indicators
- file-openability and replacement need

## Financial & Employment Evaluator Agent

### Purpose

Convert financial evidence into a fast officer-readable summary and detect obvious concern patterns.

### Checks

- average balance
- suspicious deposits
- employment and sponsor consistency
- home-country ties where relevant

## Policy & Compliance Agent

### Purpose

Map case facts against the active official policy version for the Sri Lanka workflow pack.

### Output style

Requirement-by-requirement matrix with status, evidence IDs, reasons, and rule version context.

## Security & Background Auditor Agent

### Purpose

Represent restricted system checks without leaking raw sensitive data.

### Output style

Minimal codes only, suitable for routing and officer awareness.

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
- manual-referral context
- operational timeline summary
- questions for officer

## Applicant Communication Agent

### Purpose

Turn workflow state into respectful, simple next-step messages for ETA, re-upload, referral, extension, and decision-notice stages.

### Restrictions

- no legal conclusion before human action
- no security disclosure
- no ambiguous wording about ETA versus final clearance

## Audit & Compliance Agent

### Purpose

Create the history needed for governance, appeal review, operational oversight, and circular/version traceability.
