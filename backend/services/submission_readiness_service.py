from __future__ import annotations

import os
from pathlib import Path

from backend.models.schemas import SubmissionReadinessItem, SubmissionReadinessResponse


class SubmissionReadinessService:
    def __init__(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[2]

    def status(self) -> SubmissionReadinessResponse:
        readme_text = self._read_text(self.repo_root / "README.md")
        items = [
            SubmissionReadinessItem(
                key="license_file",
                status="PASS" if (self.repo_root / "LICENSE").exists() else "FAIL",
                details="Public open-source submissions need a visible license file in the repository root.",
            ),
            SubmissionReadinessItem(
                key="env_example",
                status="PASS" if (self.repo_root / ".env.example").exists() else "FAIL",
                details="Environment variable examples should exist so judges can run the project safely without leaked secrets.",
            ),
            SubmissionReadinessItem(
                key="readme_hackathon_alignment",
                status="PASS"
                if all(
                    phrase in readme_text
                    for phrase in (
                        "Selected partner track: **Arize**",
                        "Google ADK",
                        "Arize Phoenix",
                        "OpenInference",
                        "Phoenix MCP",
                    )
                )
                else "FAIL",
                details="README should explicitly explain Google, Arize, OpenInference, and MCP usage for judges.",
            ),
            SubmissionReadinessItem(
                key="phoenix_mcp_config",
                status="PASS" if (self.repo_root / "deployment" / "mcp" / "phoenix-mcp.sample.json").exists() else "FAIL",
                details="Phoenix MCP server configuration sample should be present for the Arize track.",
            ),
            SubmissionReadinessItem(
                key="submission_runbook",
                status="PASS"
                if (self.repo_root / "docs" / "runbooks" / "hackathon-submission-checklist.md").exists()
                else "FAIL",
                details="A concrete hosted-deployment and demo-readiness runbook should exist for final hackathon handoff.",
            ),
            SubmissionReadinessItem(
                key="live_gemini_runtime",
                status="PASS" if bool(os.getenv("GOOGLE_API_KEY", "").strip()) else "WARNING",
                required=False,
                details="Live Gemini execution is not configured in this environment. The repo can fall back safely, but the final demo should show live Google AI usage.",
            ),
            SubmissionReadinessItem(
                key="live_phoenix_export",
                status="PASS"
                if all(
                    bool(os.getenv(name, "").strip())
                    for name in ("PHOENIX_API_KEY", "PHOENIX_COLLECTOR_ENDPOINT", "PHOENIX_PROJECT_NAME")
                )
                else "WARNING",
                required=False,
                details="Phoenix export credentials are not fully configured in this environment. Final submission should show real Phoenix traces and evaluations.",
            ),
            SubmissionReadinessItem(
                key="hosted_url",
                status="PASS" if bool(os.getenv("VISAFLOW_HOSTED_URL", "").strip()) else "FAIL",
                details="Hackathon submission requires a hosted project URL for judging and testing.",
            ),
            SubmissionReadinessItem(
                key="public_repo_url",
                status="PASS" if bool(os.getenv("VISAFLOW_PUBLIC_REPO_URL", "").strip()) else "FAIL",
                details="Hackathon submission requires a public repository URL.",
            ),
            SubmissionReadinessItem(
                key="demo_video_url",
                status="PASS" if bool(os.getenv("VISAFLOW_DEMO_VIDEO_URL", "").strip()) else "FAIL",
                details="Hackathon submission requires a public or unlisted demo video URL under three minutes.",
            ),
        ]

        ready = all(item.status == "PASS" for item in items if item.required)
        return SubmissionReadinessResponse(
            project_name="VisaFlow MAS — Multi-Agent Visa Decision Support System",
            partner_track="Arize",
            overall_status="READY" if ready else "ACTION_REQUIRED",
            ready_for_submission=ready,
            items=items,
        )

    @staticmethod
    def _read_text(path: Path) -> str:
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")
