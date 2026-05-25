# Workflow and Routing

## End-to-end flow

1. Applicant submits the case.
2. System creates a case record and initial timeline event.
3. Supervisor starts processing.
4. Intake checks completeness and payment state.
5. If incomplete, applicant message is created and the case waits for documents.
6. If complete, document, financial, policy, security, and risk analysis execute.
7. Supervisor applies deterministic routing precedence.
8. Officer Liaison produces the officer brief.
9. Audit records the processing outputs.
10. Case moves to officer review.
11. Officer takes the final legal action.
12. Final human action and override reason are audited.

## Routing precedence

### 1. Missing evidence comes first

If required documents are missing, request more information before deeper eligibility decisions.

### 2. Security or restricted-system uncertainty outranks approval readiness

Any `POSSIBLE_MATCH`, `CONFIRMED_HIT`, or `SYSTEM_UNAVAILABLE` result routes to enhanced review.

### 3. Identity and document integrity matter early

Invalid or questionable passport/document outputs route to enhanced review.

### 4. High-risk anomalies escalate

High or critical fraud/risk outcomes route to enhanced review.

### 5. Policy non-compliance can prepare a refusal draft

If policy requirements are clearly not met, the system prepares a refusal-ready recommendation for officer review.

### 6. Policy uncertainty requests more evidence

If policy evaluation is unclear or missing evidence, the system asks for more information rather than forcing a legal conclusion.

### 7. Weak finances request more information

If funds are below threshold or insufficiently supported, the system can request more evidence before final officer action.

## Why deterministic routing matters

The final recommendation category must be reproducible and explainable. It should not vary because a language model “felt” more cautious on one run than another.
