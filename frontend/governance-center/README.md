# Governance Center

The governance center exposes the active Sri Lanka tourist-visit rule pack, official source references, circulars, nationality exception handling, and observability posture in a single operational view.

Current scope:

- active policy version summary
- tourist policy requirement list
- circular and publication visibility
- nationality exception rule visibility
- Arize Phoenix observability status visibility
- Google ADK and Gemini runtime posture visibility
- Phoenix readiness checklist visibility
- observability redaction guardrail visibility
- evaluation rubric catalog visibility
- one-case evaluation runner visibility
- case-driven self-improvement review visibility
- case-aware review deep links that land directly on the self-improvement panel

Frontend priorities:

- make policy versioning explicit for officers and supervisors
- surface publication mismatches instead of burying them in backend payloads
- make the Phoenix observability posture visible for demo and governance review
- let governance users run the deterministic safety rubric against one processed case before approving prompt or routing changes
- show whether the self-improvement lane is in live Gemini mode or mock-safe fallback mode
- let applicant, officer, supervisor, and launchpad surfaces hand off a case directly into governance review
- Tailwind-based MVP UI without a separate frontend build step yet
