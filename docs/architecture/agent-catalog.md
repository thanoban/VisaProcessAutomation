# Agent Catalog

## Runtime model

VisaFlow MAS is being shaped around Google ADK as the code-owned runtime. Each agent is expected to emit JSON-only output and to preserve the human-in-the-loop legal boundary.

## Supervisor Agent

### Purpose

Own workflow coordination, lifecycle transitions, and recommendation routing for the Sri Lanka tourist workflow pack.

### Must do

- call the right agents in the right order
- enforce deterministic routing rules
- preserve operational states separately from legal recommendation categories
- always require human decision for the legal outcome

### Must not do

- make the final legal decision
- invent facts, policy, or circular status

## Intake & Completeness Agent

### Purpose

Stop incomplete, unreadable, or misrouted cases before deeper analysis or officer review.

### Checks

- required fields
- required uploads
- payment state
- duplicate uploads
- unreadable files
- obvious exception triggers

## Document Validator Agent

### Purpose

Normalize identity and travel-document evidence into a structured format.

### Checks

- passport fields
- expiry
- MRZ consistency
- name match
- basic tampering indicators
- file-openability and replacement need

## Financial & Employment Evaluator Agent

### Purpose

Convert financial evidence into a fast officer-readable summary and detect concern patterns.

### Checks

- average balance
- suspicious deposits
- employment or sponsor consistency
- home-country tie signals where relevant

## Policy & Compliance Agent

### Purpose

Map case facts against the active official rule pack and policy references.

### Key rule

Must cite policy IDs and must not hallucinate policy.

## Security & Background Auditor Agent

### Purpose

Represent restricted system checks without leaking raw sensitive data.

### Output style

Minimal result codes only:

- `CLEAR`
- `POSSIBLE_MATCH`
- `CONFIRMED_HIT`
- `SYSTEM_UNAVAILABLE`

## Risk & Fraud Assessment Agent

### Purpose

Detect evidence-based anomaly signals without unfair use of protected attributes.

### Key rule

High risk triggers enhanced human review, not hidden refusal.

## Officer Brief Agent

### Purpose

Package the case for fast officer review.

### Output

- case summary
- recommendation
- policy references
- risk flags
- evidence list
- unresolved questions
- operational timeline summary

## Applicant Communication Agent

### Purpose

Turn workflow state into respectful, simple next-step messages.

### Restrictions

- no legal conclusion before human action
- no security disclosure
- no confusing wording about ETA versus final clearance

## Audit & Observability Agent

### Purpose

Write local audit records and coordinate Arize Phoenix trace metadata.

### Responsibilities

- preserve local audit as source of truth
- attach prompt, model, and policy versions
- attach trace and observation IDs
- support evaluation labels
- avoid exporting unnecessary PII

## Self-Improvement Agent

### Purpose

Inspect failed traces and weak evaluations through Phoenix MCP, then propose safer prompt or routing improvements.

### Hard boundary

The Self-Improvement Agent may recommend a change, but a human must approve it before production behavior changes.
