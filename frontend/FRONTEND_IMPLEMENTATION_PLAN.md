# Frontend Implementation Plan

## 1. Purpose

This frontend plan turns the backend-first PoC into a professional two-surface product experience that aligns with [PLAN.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/PLAN.md).

The frontend must make the Sri Lanka tourist-visit workflow understandable for:

- applicants who need clarity, next actions, deadlines, and document guidance
- officers who need structured evidence, policy context, audit visibility, and a safe decision workflow
- supervisors who need queue signals and operational friction visibility in later phases

## 2. Product Surfaces

### Applicant portal

Primary goals:

- explain where the case is in plain language
- show current holder, next action, and due dates
- help applicants upload the right evidence with less confusion
- surface service notices and ETA/manual-review status clearly

Initial modules:

- landing and trust header
- new application intake form
- checklist and document preparation panel
- case status lookup view
- status timeline and notices

### Officer dashboard

Primary goals:

- provide a single operational case view
- summarize recommendation, risk, policy references, and missing items
- separate system recommendation from human legal action
- keep auditability visible before final action

Initial modules:

- queue and case overview shell
- officer brief panel
- evidence and missing-items panel
- policy and governance reference panel
- audit timeline
- final decision action panel

## 3. Experience Principles

- professional government-grade visual language, not startup novelty UI
- strong information hierarchy with calm, high-trust styling
- responsive layouts for laptop-first use with tablet-safe fallbacks
- explicit human-review boundary on all recommendation surfaces
- plain-language messaging for applicant-facing states
- accessibility-first semantics, keyboard support, and color contrast

## 4. Frontend Architecture

- keep frontend assets inside `frontend/`
- use a shared design foundation for typography, spacing, cards, status badges, buttons, forms, and timelines
- keep applicant and officer surfaces separate, but reuse shared tokens and utility behavior
- consume the current FastAPI contract directly with small fetch wrappers and mock-safe fallbacks
- start with static HTML, CSS, and JavaScript for fast PoC delivery, then upgrade to a component framework only if the interaction surface outgrows the static architecture

## 5. Visual Direction

- colors: deep navy, slate, warm white, muted teal, amber, and controlled red for risk states
- typography: editorial serif accent for headings plus a clean sans-serif for operational content
- layout: generous spacing, clear panel framing, and dashboard density tuned for scanning
- motion: minimal fade and lift transitions for state changes, no decorative animation

## 6. Delivery Phases

### Phase 1: foundation

- create shared design tokens and core layout styles
- define reusable status chips, cards, sections, tables, timeline styles, and form controls
- document local preview and verification steps

### Phase 2: applicant portal MVP

- build intake page
- build checklist and status views
- wire application creation, case retrieval, and status retrieval
- show notices, deadlines, action owner, and timeline clearly

### Phase 3: officer dashboard MVP

- build case overview shell
- wire officer brief, audit, and decision APIs
- show recommendation, missing items, risk flags, and final action boundary

### Phase 4: hardening

- empty-state, loading-state, and error-state polish
- accessibility pass
- terminology consistency pass against Sri Lanka workflow docs
- integration path into FastAPI static serving or a future dedicated frontend build pipeline

## 7. Verification Standard

Each frontend slice is only considered finished when:

- the relevant HTML renders locally without broken asset references
- the JavaScript initializes without console syntax errors
- the surface handles loading, success, and error states
- the copy matches the safety boundary in `README.md` and `PLAN.md`
- the slice is committed separately so progress stays reviewable

## 8. Immediate Build Order

1. shared frontend foundation
2. applicant portal landing, intake, and status shell
3. officer dashboard overview and brief shell
4. API wiring refinement and UI hardening
