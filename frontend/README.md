# Frontend Preview Guide

The frontend is a simple web shell served directly by FastAPI. It exists to demonstrate the applicant, officer, supervisor, and governance flows required by the hackathon submission.

## Surfaces

- `/frontend/` : internal launchpad and API target control
- `/frontend/applicant-portal/` : applicant intake, upload, status, and extension flow
- `/frontend/officer-dashboard/` : officer review and final human decision workspace
- `/frontend/supervisor-dashboard/` : queue oversight, urgency, and extension backlog view
- `/frontend/governance-center/` : policy, circular, and observability posture view

## Navigation model

The frontend now distinguishes between:

- role-scoped navigation for production-style usage
- workspace preview mode for internal development and demo switching

Cross-surface navigation should only appear in workspace preview mode.

Case-aware deep links now support jumping straight into:

- officer extension handling via `#extension-operations-panel`
- governance self-improvement review via `#self-improvement-panel`
- governance evaluation runner via `#evaluation-panel`

## Local preview

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start FastAPI from the repo root:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

3. Open the served frontend:

- [http://127.0.0.1:8000/frontend/](http://127.0.0.1:8000/frontend/)

4. Use the API target control if you want the frontend to point at another backend port or host. The chosen value is stored under `visaFlowApiBaseUrl`.

## Demo relevance

For the hackathon demo, the frontend should visibly prove:

- applicant submission and status flow
- officer recommendation and human decision flow
- supervisor queue visibility
- extension backlog visibility from the launchpad and supervisor surface
- governance and Arize observability posture visibility
- governance evaluation rubric visibility and one-case evaluation runs
- governance submission-readiness visibility for repo URL, hosted URL, demo video, and live-runtime gaps
- Phoenix readiness and redaction guardrail visibility
- case-driven self-improvement review visibility inside governance
- case-aware governance review jumps from applicant, officer, supervisor, and recent-case surfaces
- launchpad-level observability summary before entering internal surfaces

## Verification steps

### Frontend syntax

```bash
node --check frontend/index.js
node --check frontend/shared/app.js
node --check frontend/applicant-portal/app.js
node --check frontend/officer-dashboard/app.js
node --check frontend/supervisor-dashboard/app.js
node --check frontend/governance-center/app.js
```

### Backend contract checks

```bash
pytest tests/agent_tests/test_api_contracts.py -q
pytest tests/agent_tests/test_evaluation_service.py -q
pytest tests/agent_tests/test_submission_readiness.py -q
pytest tests/agent_tests/test_observability_service.py -q
pytest tests/workflow_tests/test_workflow_cases.py -q
```

### Route smoke checks

```bash
curl http://127.0.0.1:8000/frontend/
curl http://127.0.0.1:8000/frontend/applicant-portal/
curl http://127.0.0.1:8000/frontend/officer-dashboard/
curl http://127.0.0.1:8000/frontend/supervisor-dashboard/
curl http://127.0.0.1:8000/frontend/governance-center/
```
