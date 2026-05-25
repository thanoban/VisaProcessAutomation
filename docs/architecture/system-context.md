# System Context

## Purpose

VisaFlow MAS is designed to sit between a visa application intake channel and a human immigration officer. It absorbs repetitive verification work, prepares structured recommendations, and preserves a defensible record of how the case was processed.

## Primary stakeholders

### Applicants

- submit applications
- upload supporting evidence
- receive missing-information requests
- track case progress

### Immigration officers

- inspect AI-prepared briefs
- verify evidence and policy alignment
- make the final legal decision
- add notes and override recommendations

### Supervisors

- monitor queues and SLA pressure
- review escalated and sensitive cases
- inspect officer override patterns
- manage operational consistency

### Security and partner agencies

- provide restricted check outcomes
- expose only minimal result codes to general workflow components

### Audit, appeals, and integrity bodies

- review case history, reasoning chain, and override trails
- verify that no hidden auto-decision path exists

## External systems represented in the PoC

- document storage
- policy knowledge base
- security screening service
- previous visa history service
- notification channel
- audit sink

## Trust boundaries

### General processing boundary

Receives case data, runs core document, financial, policy, and risk analysis, and prepares officer-facing outputs.

### Restricted security boundary

Queries sensitive systems and returns only approved codes such as `CLEAR`, `POSSIBLE_MATCH`, `CONFIRMED_HIT`, or `SYSTEM_UNAVAILABLE`.

### Human decision boundary

Only an authenticated officer can submit the final action.
