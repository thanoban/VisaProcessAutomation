# VisaFlow MAS Delivery Plan

## 1. Mission

Build a Sri Lanka-centered short-visit visa decision support PoC that automates repetitive manual processing work, reduces queue pressure, improves applicant guidance, strengthens auditability, and gives officers a cleaner operational case record before they make the legal decision.

The system is not a legal decision engine. It is an automation, orchestration, and recommendation layer that supports the human immigration officer.

## 2. Base jurisdiction and benchmark model

### Base jurisdiction

Phase 1 is centered on **Sri Lanka inbound Tourist Visit processing**.

### Future Sri Lanka expansion

The architecture must also be prepared for Sri Lanka:

- Business short visits
- Transit handling
- visit visa extensions
- nationality exception and sponsor handling

### Foreign benchmark role

Canada, UK, Australia, and U.S. official systems are benchmark references for stronger workflow design:

- better checklisting
- better status tracking
- better document guidance
- better appointment and exception handling
- better post-decision communication

They are not the legal rules source for Sri Lanka.

## 3. What must be true when this PoC is successful

### Applicant experience

- applicant can see whether they are at ETA stage, document stage, manual-review stage, extension stage, or officer-review stage
- applicant sees next action, deadline, and who currently holds the case
- applicant is protected from confusing status gaps and unclear re-upload loops

### Officer experience

- officer sees one case timeline that joins ETA, document handling, policy checks, manual referral reasons, and decision preparation
- officer sees structured evidence summaries and policy references
- officer can record the final action and any override reason clearly

### Supervisor and operations experience

- supervisors can see queue bottlenecks, exception categories, and rule-change fallout
- staff can identify unreadable uploads, sponsor-required referrals, and extension delays quickly
- audit bodies can reconstruct every meaningful system and officer action

## 4. Exact operational issues to solve

1. Stop incomplete or unreadable cases from progressing silently.
2. Normalize ETA, manual referral, and officer review into one case record.
3. Surface nationality/sponsor/manual exception handling early.
4. Track port-of-entry clearance as part of the case lifecycle where relevant.
5. Make extension workflows and appointment dependencies visible.
6. Handle policy or circular publication mismatches explicitly.
7. Reduce applicant confusion around ETA status, approval proof, and next steps.
8. Improve auditability of rule version, recommendation, and override history.
9. Provide supervisor visibility over backlog and operational friction points.
10. Keep the architecture expandable to Business and Transit flows.

## 5. Operating assumptions

- Sri Lanka Tourist Visit is the first executable workflow pack.
- Business and Transit are architecture-defined but not phase-1 runtime flows.
- public forum pain points are treated as discovery hypotheses, not policy truth
- official Sri Lanka government sources remain the source of current-process truth
- foreign benchmark sources guide product quality and workflow design only
- local development continues to use SQLite while production direction remains PostgreSQL

## 6. Delivery steps

### Step 1 - Sri Lanka-centered documentation and architecture correction

- rewrite repo docs around the Sri Lanka process
- add current-method comparison and rule-governance docs
- document ETA, extension, appointment, and port-clearance states
- define discovery track and pilot pain hypotheses

### Step 2 - Sri Lanka workflow pack implementation

- model Sri Lanka lifecycle states
- add timeline and exception entities
- extend APIs for status, extension, and manual referral
- support rule circular and effective-policy version handling

### Step 3 - Validation and hardening

- test Sri Lanka workflow scenarios
- test circular/version conflict handling
- test applicant status clarity and audit completeness
- publish stable steps to GitHub

## 7. Architecture direction

The codebase remains a modular monolith with future split points:

- case management API
- orchestration service
- ETA and intake service
- document processing service
- policy and circular governance service
- extension and appointment service
- audit service
- notification service

## 8. Non-negotiables

- no automatic legal approval or refusal
- active policy version must be explicit
- publication mismatches must not silently leak into officer decisions
- security outputs must remain minimal
- protected attributes must not drive risk assessment
- every meaningful automated or human action must be auditable
