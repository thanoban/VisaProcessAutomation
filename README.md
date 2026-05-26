# VisaFlow MAS — Multi-Agent Visa Decision Support System

VisaFlow MAS is a Sri Lanka-centered, Gemini-powered, multi-agent visa decision-support web application built for the Google Cloud Partner hackathon.

Selected partner track: **Arize**

The system helps immigration officers review tourist visa applications faster by automating repetitive intake, document validation, policy comparison, risk screening, officer-brief generation, and audit/trace capture. It does **not** make the final legal decision. A human officer must always approve, reject, request more information, or escalate.

## What the project proves

VisaFlow MAS is designed to prove that a Google Cloud and Gemini stack can support a government-grade review workflow with:

- Gemini-powered agents
- Google ADK as the code-owned agent runtime
- FastAPI as the web backend
- Arize Phoenix tracing and evaluation
- OpenInference instrumentation
- Phoenix MCP server support for self-introspection
- deterministic routing and human-in-the-loop safety

## Why the project is Sri Lanka-first

The first workflow pack models the real current Sri Lanka short-visit process:

- ETA is an electronic pre-travel authorization, but final clearance still happens with a human immigration officer at the port of entry.
- Tourist, Business, and Transit short visits have distinct handling paths.
- Extension handling can involve online requests, appointment-based steps, and manual or head-office intervention.
- Official public channels can show publication timing mismatches, so active policy-pack and circular governance must be explicit.

Foreign systems from Canada, the UK, Australia, and the U.S. are used as product benchmarks for better checklisting, status tracking, evidence loops, appointments, and post-decision communication. They are not the legal rule source.

## Core workflow

The current PoC centers on **Sri Lanka Tourist Visit** processing and includes:

- applicant checklist generation
- applicant submission and document upload
- intake completeness review
- document validation
- policy comparison against versioned rule packs
- evidence-based risk and fraud analysis
- officer-ready case brief generation
- extension workflow handling
- supervisor backlog visibility
- audit plus observability capture

Allowed AI recommendation states are:

- `APPROVE_READY`
- `REQUEST_MORE_INFO`
- `ENHANCED_REVIEW`
- `REFUSAL_DRAFT_READY`

Forbidden outputs include final legal decision language such as:

- `FINAL_APPROVED`
- `FINAL_REJECTED`
- `VISA_GRANTED`
- `VISA_DENIED`

## Agent set

VisaFlow MAS is structured around these agents:

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

The Supervisor Agent uses deterministic routing and never makes the final legal decision.

## Google Cloud and Gemini usage

The project is aligned to a Google Cloud deployment path:

- **Google ADK** is the intended code-owned agent runtime.
- **Gemini** is the only planned LLM family for agent execution and evaluation.
- **FastAPI** provides the web API and serves the lightweight frontend surfaces.
- **Cloud Run** is the preferred deployment target.
- **Cloud SQL PostgreSQL** is the production storage direction, while SQLite is used locally for the MVP.
- **Cloud Storage**, **Cloud Tasks / Pub/Sub**, **Secret Manager**, and **Cloud KMS** are the preferred production adapters.

## How Arize Phoenix is used

Arize Phoenix is the selected observability and evaluation layer.

The current codebase is being shaped so that every agent run can carry:

- `trace_id`
- `case_id`
- `agent_name`
- `prompt_version`
- `model_version`
- `workflow_state`
- `tool_calls`
- `retrieved_policy_ids`
- `evidence_ids`
- `recommendation`
- `confidence`
- `human_decision_required`
- `final_human_action`
- `officer_override`

Local audit storage remains the source of truth. Phoenix is the redacted observability and evaluation plane.

## How Phoenix MCP is used

Phoenix MCP is part of the self-improvement story. The intended loop is:

1. run a visa case
2. send trace metadata to Phoenix
3. run evaluations
4. identify a failed or weak run
5. inspect the failure through Phoenix MCP
6. have the Self-Improvement Agent suggest a safer prompt or routing change
7. require human approval before any production rule or prompt change
8. rerun and compare outcomes

The MCP configuration sample is documented in [deployment/mcp/phoenix-mcp.sample.json](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/deployment/mcp/phoenix-mcp.sample.json) and explained in [deployment/arize_phoenix_setup.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/deployment/arize_phoenix_setup.md).

Current implementation status:

- the repo now includes a Google ADK runtime status service
- the repo now includes a self-improvement review endpoint backed by Google ADK with a mock-safe local fallback
- when `GOOGLE_API_KEY` is absent, the self-improvement lane runs in `GOOGLE_ADK_MOCK` mode instead of failing the workflow

## How evaluations work

The repository uses scenario-based evaluation expectations for:

- complete low-risk tourist case
- missing passport
- expired passport
- missing bank statement
- low funds
- suspicious sudden deposit
- name mismatch
- security unavailable
- missing policy citation
- attempts to make a final legal decision

Evaluation checks focus on:

- correct routing recommendation
- evidence and policy citations
- no hallucinated policy
- no raw security leakage
- `human_decision_required: true`
- officer-brief clarity
- evidence-based risk reasoning

## Human-in-the-loop safety

These are non-negotiable:

- the system never automatically grants or denies a visa
- every recommendation includes `human_decision_required: true`
- a human officer always records the final legal action
- override reasons are captured when the officer diverges from the system recommendation
- sensitive data is redacted before observability export
- raw security or watchlist detail is never exposed to applicants

## Repository guide

- [PLAN.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/PLAN.md)
- [docs/architecture/production-architecture.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/docs/architecture/production-architecture.md)
- [docs/architecture/google-cloud-deployment.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/docs/architecture/google-cloud-deployment.md)
- [docs/architecture/agent-catalog.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/docs/architecture/agent-catalog.md)
- [docs/architecture/api-contracts.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/docs/architecture/api-contracts.md)
- [frontend/README.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/frontend/README.md)
- [deployment/README.md](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/deployment/README.md)

## Environment variables

Use `.env.example` as the template. The required values are:

```env
GOOGLE_API_KEY=
GOOGLE_CLOUD_PROJECT=
GOOGLE_CLOUD_LOCATION=
GEMINI_MODEL=
PHOENIX_API_KEY=
PHOENIX_COLLECTOR_ENDPOINT=
PHOENIX_PROJECT_NAME=
DATABASE_URL=
```

Never commit a real `.env` file, API key, service-account key, token, or password.

## Run locally

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload --app-dir .
```

Open the web surfaces through FastAPI:

- [http://127.0.0.1:8000/frontend/](http://127.0.0.1:8000/frontend/)
- [http://127.0.0.1:8000/frontend/applicant-portal/](http://127.0.0.1:8000/frontend/applicant-portal/)
- [http://127.0.0.1:8000/frontend/officer-dashboard/](http://127.0.0.1:8000/frontend/officer-dashboard/)
- [http://127.0.0.1:8000/frontend/supervisor-dashboard/](http://127.0.0.1:8000/frontend/supervisor-dashboard/)
- [http://127.0.0.1:8000/frontend/governance-center/](http://127.0.0.1:8000/frontend/governance-center/)

## Run tests and evaluations

```bash
pytest -q
```

Recommended focused checks:

```bash
pytest tests/agent_tests/test_observability_service.py -q
pytest tests/agent_tests/test_adk_runtime_and_self_improvement.py -q
pytest tests/workflow_tests/test_workflow_cases.py -q
pytest tests/workflow_tests/test_end_to_end_case_journey.py -q
```

## Screenshots and demo media

This README is prepared for screenshots or a short demo GIF, but media is not yet embedded in the repository. The final submission should show:

- applicant submission flow
- officer dashboard recommendation flow
- supervisor backlog view
- governance or observability view
- Phoenix traces and evaluations
- Phoenix MCP self-introspection flow

## Data sources used

- mock tourist visa cases in the repository
- Sri Lanka official visa and immigration references represented through local rule packs and reference documents
- benchmark process notes derived from official public government sources for Canada, the UK, Australia, and the U.S.

## Limitations

- current data is mock only and must remain mock only
- the local MVP uses deterministic and mock-backed document and security flows
- Phoenix MCP usage is configured and documented, but a live Phoenix environment is still required for full runtime introspection
- Cloud Run hosting, public repo URL, hosted URL, and demo video still need to be finalized at submission time

## License

See [LICENSE](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/LICENSE).
