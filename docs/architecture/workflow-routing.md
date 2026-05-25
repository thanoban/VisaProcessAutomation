# Workflow and Routing

## Sri Lanka phase-1 lifecycle

1. Applicant begins a Tourist Visit case.
2. System generates a Sri Lanka-specific checklist.
3. Applicant submits ETA and supporting details.
4. Intake verifies completeness, readability, and obvious defects.
5. If the case matches a nationality or sponsor exception, it is referred to manual review early.
6. If the case passes intake, it moves through document, policy, financial, security, and risk analysis.
7. Supervisor applies deterministic recommendation routing.
8. Officer Liaison prepares the case brief.
9. Officer reviews and records the legal action when required.
10. If relevant, the case tracks port-of-entry and extension-related operational states.

## Planned operational states

- `DRAFT`
- `CHECKLIST_READY`
- `SUBMITTED`
- `WAITING_FOR_PAYMENT`
- `WAITING_FOR_DOCUMENTS`
- `UNDER_PRECHECK`
- `REFERRED_TO_MANUAL_REVIEW`
- `READY_FOR_PORT_CLEARANCE`
- `ENTERED_SRI_LANKA`
- `EXTENSION_REQUESTED`
- `EXTENSION_APPOINTMENT_REQUIRED`
- `UNDER_ANALYSIS`
- `READY_FOR_OFFICER_REVIEW`
- `DECISION_RECORDED`
- `POST_DECISION_FULFILLMENT`
- `CLOSED`

## Routing precedence for recommendation categories

### 1. Missing or unreadable evidence first

If required information is missing or unusable, request more information before deeper legal preparation.

### 2. Security and restricted handling outrank approval readiness

Any restricted screening issue, system outage, or manual-security condition routes to enhanced review.

### 3. Identity and document integrity come early

Invalid or questionable identity evidence routes to enhanced review.

### 4. High-risk anomaly signals escalate

High or critical risk findings route to enhanced review.

### 5. Policy failure can prepare refusal drafting

If the active policy version clearly shows the case does not meet requirements, the system may prepare a refusal-draft-ready recommendation for officer review.

### 6. Policy uncertainty and operational ambiguity request more information

If policy status is unclear, circular versions conflict, or mission-specific evidence is missing, the system requests more information or manual review instead of forcing legal certainty.

## Why deterministic routing matters

Sri Lanka’s process already contains exceptions, public-rule mismatch risk, and manual handoffs. Deterministic routing is what prevents those realities from turning into inconsistent machine behavior.
