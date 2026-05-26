# VisaFlow MAS Delivery Plan

## 1. Competition alignment

### Project name

VisaFlow MAS — Multi-Agent Visa Decision Support System

### Selected partner track

Arize

### Required product story

Build a Sri Lanka-centered, Gemini-powered, multi-agent visa decision-support web application that helps immigration officers process tourist visa applications faster while preserving a strict human legal decision boundary.

The project must meaningfully use:

- Google ADK
- Gemini through Google Cloud compatible tooling
- FastAPI
- Arize Phoenix
- OpenInference instrumentation
- Phoenix MCP server
- evaluation and self-improvement workflows

## 2. Mission

Automate the repetitive and error-prone parts of the Sri Lanka tourist visa review lifecycle while keeping the final legal decision with a human officer.

The system is not a legal decision engine. It is an orchestration, validation, recommendation, audit, and observability layer.

## 3. Base jurisdiction and benchmark model

### Base jurisdiction

Phase 1 centers on **Sri Lanka inbound Tourist Visit processing**.

### Future Sri Lanka expansion

The architecture is prepared for:

- Business short visits
- Transit short visits
- extension handling
- sponsor and nationality exception routing

### Foreign benchmark role

Canada, UK, Australia, and U.S. systems are benchmark references for:

- document checklist quality
- applicant status tracking
- appointment and exception handling
- post-submit evidence loops
- decision communication

They are not the legal rule source for Sri Lanka.

## 4. What success means

The project is successful only if it proves:

1. a Gemini-powered multi-agent workflow can help officers review tourist visa cases
2. the AI never makes the final legal decision
3. every meaningful agent step is traceable in Arize Phoenix
4. evaluations can detect unsafe or weak behavior
5. Phoenix MCP supports trace and evaluation introspection
6. a self-improvement loop can suggest safer changes without automatically changing production rules
7. applicant, officer, supervisor, and governance surfaces remain usable

## 5. Scope of the executable PoC

### Applicant-facing

- checklist generation
- case creation
- document upload
- status tracking
- evidence-request responses
- extension request flow

### Officer-facing

- officer brief
- evidence summary
- policy references
- risk flags
- final human decision capture
- override reason capture

### Supervisor and governance

- queue visibility
- urgency signals
- manual referral visibility
- extension workload visibility
- rule-governance visibility
- observability status visibility

## 6. Agent design

The system includes these agents:

1. Supervisor Agent
2. Intake Agent
3. Document Validator Agent
4. Financial & Employment Evaluator Agent
5. Policy & Compliance Agent
6. Security & Background Auditor Agent
7. Risk & Fraud Agent
8. Officer Brief Agent
9. Applicant Communication Agent
10. Audit & Observability Agent
11. Self-Improvement Agent

Every agent must return valid JSON only.

## 7. Routing and legal safety

Allowed AI recommendation states:

- `APPROVE_READY`
- `REQUEST_MORE_INFO`
- `ENHANCED_REVIEW`
- `REFUSAL_DRAFT_READY`

Always true:

- `human_decision_required = true`

Never allowed:

- final approval or refusal by AI
- hidden rule invention
- raw security disclosure
- prompt-controlled privileged tool execution from applicant content

## 8. Core operational issues to solve

1. Stop incomplete or unreadable cases before they waste officer time.
2. Join ETA, document review, policy matching, and officer review into one case record.
3. Surface manual referral triggers early.
4. Keep extension handling visible and auditable.
5. Handle rule-publication mismatches explicitly.
6. Reduce applicant confusion about next action and current case owner.
7. Make recommendation reasoning traceable to evidence and policy.
8. Detect unsafe behavior through evaluations before rollout.
9. Give supervisors backlog and override visibility.
10. Keep the system expandable for later Sri Lanka visa classes.

## 9. Observability and evaluation plan

Arize Phoenix is the first-class observability and evaluation plane.

Each meaningful workflow step should carry:

- trace ID
- case ID
- agent name
- prompt version
- model version
- workflow state
- tool calls
- retrieved policy IDs
- evidence IDs
- recommendation
- confidence
- human decision required flag
- final human action when available

Evaluation coverage must include:

- low-risk valid case
- missing document case
- expired passport
- low funds
- suspicious deposits
- name mismatch
- security unavailable
- missing policy citation
- attempted final-decision language
- extension workflow edge cases

## 10. Self-improvement loop

The Self-Improvement Agent must:

1. inspect failed traces or weak evaluations
2. summarize the failure
3. propose safer prompt or routing improvements
4. require human approval before changes are adopted
5. support rerun comparison

It must not auto-edit production rules.

## 11. Architecture direction

The repo remains a modular monolith with future split points:

- FastAPI delivery layer
- Google ADK agent runtime layer
- deterministic workflow layer
- case and audit persistence layer
- observability and evaluation adapter layer
- frontend surfaces for applicant, officer, supervisor, and governance roles

## 12. Delivery sequence

### Step 1

Align the repo to the Sri Lanka-first domain model and hackathon rules.

### Step 2

Implement and verify the tourism workflow, extension path, and supervisor visibility.

### Step 3

Add Arize tracing, evaluation metadata, governance visibility, and MCP configuration.

### Step 4

Add Google ADK and Gemini runtime scaffolding plus self-improvement support.

### Step 5

Finish submission hardening:

- README
- license
- `.env.example`
- hosted deployment plan
- demo readiness

## 13. Non-negotiables

- no automatic legal approval or refusal
- active policy version must be explicit
- publication mismatches must not silently affect officer decisions
- security outputs must stay minimal
- protected attributes must not drive risk scoring unfairly
- every meaningful automated or human action must be auditable
- no real personal visa data may be used
