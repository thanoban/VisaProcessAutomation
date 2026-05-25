# System Context

## Purpose

VisaFlow MAS sits between Sri Lanka’s applicant-facing short-visit intake surfaces and the human immigration officer. It absorbs repetitive verification work, keeps ETA and case operations joined, and preserves a defensible record of what happened at every stage.

## Primary stakeholders

### Applicants

- submit ETA and supporting information
- upload supporting evidence
- receive requests for more information
- track ETA, case, and extension-related status

### Immigration officers

- inspect AI-prepared briefs
- verify policy and evidence alignment
- handle manual referrals and complex cases
- record the final human action

### Port and border officers

- perform final entry clearance where relevant
- need visibility into ETA and case status without relying on fragmented channels

### Supervisors and operations managers

- monitor pending ETA cases
- monitor extension bottlenecks
- review rule-change fallout and manual-referral load
- inspect override patterns and stuck-state queues

### Policy owners and ministry stakeholders

- publish rules, circulars, and temporary schemes
- need confidence that active officer workflow is using the correct version

### Audit and integrity bodies

- review history, overrides, rule versions, and case handling consistency

## External systems represented in the PoC

- ETA authorization channel
- document storage and upload handling
- policy and circular knowledge base
- security and previous-history adapters
- notification and messaging channel
- appointment or extension handling channel

## Trust boundaries

### General processing boundary

Runs intake, analysis, recommendation preparation, and timeline management.

### Restricted security boundary

Queries sensitive systems and returns minimal codes only.

### Human legal decision boundary

Only an authenticated officer can record the legal outcome.

### Policy governance boundary

Controls which rule version, circular, or publication is active for internal workflow use.
