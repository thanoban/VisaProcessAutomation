# Hackathon Submission Checklist

## Goal

Ship VisaFlow MAS with a repeatable checklist for the final Google Cloud Partner hackathon submission.

## Required submission artifacts

1. Public repository URL
2. Hosted application URL
3. Demo video URL under three minutes
4. README that explains:
   - Google ADK usage
   - Gemini usage
   - Arize Phoenix usage
   - OpenInference usage
   - Phoenix MCP usage
5. License file
6. `.env.example`

## Hosted deployment plan

1. Build and deploy the FastAPI app to Cloud Run using the repo deployment manifests and environment configuration.
2. Point the public hosted URL at the FastAPI-served frontend so `/frontend/` remains the demo entry point.
3. Confirm the hosted deployment can reach:
   - Google ADK and Gemini runtime credentials
   - Phoenix collector configuration
   - production storage and document adapters
4. Record the final public hosted URL in `VISAFLOW_HOSTED_URL` for submission-readiness checks.

## Demo readiness flow

1. Seed the governance demo showcase from `/frontend/governance-center/`.
2. Walk one low-risk approval-ready case through applicant, officer, and governance surfaces.
3. Walk one document-loop case through applicant status and supervisor visibility.
4. Walk one enhanced-review case through evaluation and self-improvement views.
5. Show submission-readiness status in governance and on the frontend launchpad.
6. Confirm final officer action still requires a human decision.

## Final verification before submission

Run:

```bash
pytest -q
```

Then confirm:

- `/frontend/` loads
- `/frontend/governance-center/` loads
- `/governance/submission-readiness` responds
- `/demo/showcase/seed` responds

## Submission metadata

Populate these before final handoff:

```env
VISAFLOW_PUBLIC_REPO_URL=
VISAFLOW_HOSTED_URL=
VISAFLOW_DEMO_VIDEO_URL=
```
