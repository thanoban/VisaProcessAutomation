# Frontend Preview Guide

This frontend is served directly by FastAPI from `frontend/` and is designed for local workflow testing against the Sri Lanka tourist-visit PoC backend.

## Surfaces

- `/frontend/` : frontend home and API target control
- `/frontend/applicant-portal/` : applicant intake, status, and document-response view
- `/frontend/officer-dashboard/` : officer review and decision workspace
- `/frontend/supervisor-dashboard/` : queue oversight and drill-down view
- `/frontend/governance-center/` : policy, circular, and source-traceability view

## Local Preview

1. Install backend dependencies if needed:

```bash
pip install -r requirements.txt
```

2. Start FastAPI from the repo root:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

3. Open the frontend home:

- [frontend home](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/frontend/index.html)
- served route: [http://127.0.0.1:8000/frontend/](http://127.0.0.1:8000/frontend/)

4. Use the API target control on the frontend home if you want the surfaces to point at a different backend port or host. The selected target is saved in browser local storage under `visaFlowApiBaseUrl`.

## Case Navigation

- Applicant and officer views accept `?case=<CASE_ID>` for direct case loading when the live API is reachable.
- Supervisor drill-down cards link directly into applicant and officer case views.
- Recent live applicant and officer cases are remembered locally on the frontend home.

## Verification Steps

### Frontend syntax

Run targeted syntax checks after frontend edits:

```bash
node --check frontend/index.js
node --check frontend/shared/app.js
node --check frontend/applicant-portal/app.js
node --check frontend/officer-dashboard/app.js
node --check frontend/supervisor-dashboard/app.js
node --check frontend/governance-center/app.js
```

### Contract and workflow coverage

Run the backend-backed tests that currently cover the frontend-facing flows:

```bash
pytest tests/agent_tests/test_api_contracts.py -q
pytest tests/workflow_tests/test_workflow_cases.py -q
```

### Route smoke checks

After starting FastAPI, confirm the served surfaces return `200`:

```bash
curl http://127.0.0.1:8000/frontend/
curl http://127.0.0.1:8000/frontend/applicant-portal/
curl http://127.0.0.1:8000/frontend/officer-dashboard/
curl http://127.0.0.1:8000/frontend/supervisor-dashboard/
curl http://127.0.0.1:8000/frontend/governance-center/
```

### Current known local-worktree caveats

- Direct file upload support depends on the backend `/cases/{case_id}/document-files` route being available on the selected API target.
- If that route is missing, the applicant portal falls back cleanly to URI-backed document submission when URIs are provided.
- The current repo may contain unrelated local backend or test worktree changes during active development. Keep frontend slices scoped and stage files intentionally.
