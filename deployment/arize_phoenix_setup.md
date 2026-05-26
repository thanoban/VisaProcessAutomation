# Arize Phoenix Setup

## Why Phoenix is in this project

VisaFlow MAS uses Arize Phoenix as the primary partner-track observability and evaluation layer for:

- agent-run tracing
- workflow-outcome tracing
- human decision tracing
- evaluation metadata for legal-sensitive scenarios
- self-improvement analysis through Phoenix MCP

Local audit storage remains the source of truth. Phoenix is the redacted observability and evaluation plane.

## Backend environment

Set these environment variables on the code-owned runtime:

```powershell
$env:VISAFLOW_OBSERVABILITY_ENABLED="1"
$env:VISAFLOW_OBSERVABILITY_TARGET="PHOENIX"
$env:PHOENIX_PROJECT_NAME="visaflow-mas"
$env:PHOENIX_COLLECTOR_ENDPOINT="<your phoenix collector endpoint>"
$env:PHOENIX_API_KEY="<your phoenix api key>"
```

Optional OpenInference instrumentors:

```powershell
$env:VISAFLOW_ENABLE_GOOGLE_ADK_INSTRUMENTATION="1"
$env:VISAFLOW_ENABLE_GOOGLE_GENAI_INSTRUMENTATION="1"
```

## Python dependencies

The repo is aligned around these packages:

- `google-adk`
- `google-genai`
- `arize-phoenix-otel`
- `arize-phoenix-client`
- `arize-phoenix-evals`
- `openinference-instrumentation-google-adk`
- `openinference-instrumentation-google-genai`

## What the app exports

The backend exports redacted observability metadata for:

- agent runs
- supervisor workflow outcomes
- officer decisions
- extension workflow events
- evaluation runs

Exported records are designed to include:

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

## Redaction policy

The observability export path must not send unnecessary PII or sensitive security content. The current redaction rules cover fields such as:

- full name
- date of birth
- passport number
- contact email
- phone
- file URI
- destination address
- supporting note
- raw security or watchlist payloads

## Governance API

Use this internal endpoint to inspect the current observability posture:

```text
GET /governance/observability/status
```

## Phoenix MCP server

The Phoenix MCP server lives in the MCP client configuration, not inside the FastAPI backend.

See the sample file:

- [deployment/mcp/phoenix-mcp.sample.json](/D:/PROJECTS/Startup/VisaAgent/VisaProcessAutomation/deployment/mcp/phoenix-mcp.sample.json)

The intended MCP questions include:

- show last failed traces
- summarize latest evaluation failures
- compare two runs of the same visa case
- find cases where policy citation was missing
- list traces with officer override
- summarize weak confidence cases

## Self-improvement loop

The intended human-approved loop is:

1. process a case
2. export observability data to Phoenix
3. run evaluations
4. inspect a weak or failed trace with Phoenix MCP
5. have the Self-Improvement Agent suggest a safer prompt or routing improvement
6. require human approval before applying any change
7. rerun and compare the outcome
