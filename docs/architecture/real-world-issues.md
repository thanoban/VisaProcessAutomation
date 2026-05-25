# Real-World Visa Processing Issues and Automation Response

## 1. Incomplete applications flood the queue

### Real issue

Officers spend time opening cases that are missing core documents, unreadable scans, payment confirmation, or basic form details.

### System response

- Intake Agent blocks the case before officer review
- applicant gets a structured missing-items request
- case is moved to `WAITING_FOR_DOCUMENTS`

## 2. Identity and travel-document checking is repetitive

### Real issue

Passport details, expiry, name matching, and document quality are checked manually again and again across simple cases.

### System response

- Document Validator extracts fields early
- passport validity and name matching are normalized into one output
- unresolved identity issues route to enhanced review

## 3. Financial evidence is slow to assess manually

### Real issue

Bank statements take time to review, especially when salary patterns or sudden deposits matter.

### System response

- Financial Agent calculates average balance and suspicious deposit patterns
- summary is exposed directly in officer brief payload
- weak or unclear funds evidence is routed before final officer action

## 4. Policy application becomes inconsistent across teams

### Real issue

Rules change, local teams interpret them differently, and old habits override updated policy.

### System response

- Policy Agent retrieves active sections from a managed policy corpus
- every requirement is evaluated into `SATISFIED`, `NOT_SATISFIED`, `MISSING_EVIDENCE`, or `UNCLEAR`
- officer can see policy ID and evidence citation together

## 5. Security and overstay checks are fragmented

### Real issue

Officers often need to rely on separate systems or hidden teams to confirm background signals.

### System response

- Security Adapter is isolated
- general workflow receives only minimal result codes
- any possible hit or outage forces enhanced review

## 6. Fraud signals are hard to triage consistently

### Real issue

Suspicious sponsor patterns, story conflicts, duplicate contacts, and unusual deposits can be missed or over-weighted.

### System response

- Risk Agent records only evidence-based indicators
- protected attributes are excluded
- high-risk patterns trigger enhanced review rather than automatic refusal

## 7. Audit trails are too weak for appeals and oversight

### Real issue

When decisions are challenged, it is often difficult to reconstruct what the system suggested, what the officer saw, and why the final action changed.

### System response

- every agent output is audited
- prompt, model, policy, evidence, and tool references are stored
- officer overrides must include a reason

## 8. Applicants do not know what is happening

### Real issue

Status inquiries increase because the applicant cannot tell whether the case is waiting for documents, under review, or awaiting a human officer.

### System response

- applicant status endpoint exposes current state, latest message, required actions, and deadline context
- applicant communication never states legal outcomes before human action
