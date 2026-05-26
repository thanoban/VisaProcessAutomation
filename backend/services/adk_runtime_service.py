from __future__ import annotations

import json
import os
from pathlib import Path
import threading
from typing import Any
from typing import AsyncGenerator

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from pydantic import BaseModel

from backend.models.schemas import AgentRuntimeStatusResponse


class _StructuredReviewOutput(BaseModel):
    failure_summary: str
    detected_issues: list[str]
    proposed_changes: list[dict[str, str]]
    comparison_questions: list[str]


class AdkRuntimeService:
    _instrumentation_lock = threading.Lock()
    _instrumentation_ready = False
    _instrumentation_error = ""

    def __init__(self) -> None:
        self.runtime = "GOOGLE_ADK"
        self.provider = "Gemini"
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.project_name = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "")
        self.google_api_key_present = bool(os.getenv("GOOGLE_API_KEY", "").strip())
        self.google_adk_instrumentation_enabled = os.getenv("VISAFLOW_ENABLE_GOOGLE_ADK_INSTRUMENTATION", "0") == "1"
        self.google_genai_instrumentation_enabled = (
            os.getenv("VISAFLOW_ENABLE_GOOGLE_GENAI_INSTRUMENTATION", "0") == "1"
        )

    def status(self) -> AgentRuntimeStatusResponse:
        installed = self._adk_installed()
        configured = installed and self.google_api_key_present and bool(self.model_name.strip())
        if installed and (
            self.google_adk_instrumentation_enabled or self.google_genai_instrumentation_enabled
        ) and not self._instrumentation_ready and not self._instrumentation_error:
            self._ensure_instrumentation()

        notes: list[str] = []
        if not installed:
            notes.append("google-adk is not installed in the current runtime.")
        elif configured:
            notes.append("Gemini runtime configuration is present and the ADK self-improvement agent can use the live model.")
        else:
            notes.append("Google ADK is installed, but GOOGLE_API_KEY is not configured, so the self-improvement agent will run in mock mode.")

        if self._instrumentation_error:
            notes.append(f"Instrumentation warning: {self._instrumentation_error}")

        status = "READY" if configured else "MOCK_ONLY"
        if not installed:
            status = "DEGRADED"

        return AgentRuntimeStatusResponse(
            runtime=self.runtime,
            provider=self.provider,
            status=status,
            configured=configured,
            live_model_available=configured,
            google_adk_installed=installed,
            google_adk_instrumentation_enabled=self.google_adk_instrumentation_enabled and self._instrumentation_ready,
            google_genai_instrumentation_enabled=self.google_genai_instrumentation_enabled and self._instrumentation_ready,
            model_name=self.model_name,
            project_name=self.project_name,
            location=self.location,
            phoenix_mcp_config_present=self._phoenix_mcp_config_present(),
            agent_names=self.agent_names(),
            notes=notes,
        )

    def agent_names(self) -> list[str]:
        return [
            "supervisor_agent",
            "intake_completeness_agent",
            "document_validator_agent",
            "financial_employment_agent",
            "policy_compliance_agent",
            "security_background_agent",
            "risk_fraud_agent",
            "officer_liaison_agent",
            "audit_compliance_agent",
            "self_improvement_agent",
        ]

    def create_self_improvement_agent(self, response_payload: dict[str, Any]):
        from google.adk.agents import Agent

        instruction = self._self_improvement_instruction()
        model = self._build_model(response_payload)
        return Agent(
            name="self_improvement_agent",
            description="Inspects weak visa-agent traces and proposes safer human-approved improvements.",
            instruction=instruction,
            output_schema=_StructuredReviewOutput,
            model=model,
            mode="chat",
        )

    def _build_model(self, response_payload: dict[str, Any]):
        if self.status().configured:
            return self.model_name
        return _MockStructuredLlm.create(response_payload)

    def _self_improvement_instruction(self) -> str:
        agent_path = Path(__file__).resolve().parents[2] / "agents" / "self_improvement_agent.md"
        base_instruction = agent_path.read_text(encoding="utf-8").strip()
        return (
            f"{base_instruction}\n\n"
            "Return valid JSON only with keys: "
            "failure_summary, detected_issues, proposed_changes, comparison_questions. "
            "Each proposed change must include scope, change, reason, and risk_level."
        )

    def _ensure_instrumentation(self) -> None:
        if self._instrumentation_ready:
            return
        with self._instrumentation_lock:
            if self._instrumentation_ready:
                return
            try:
                if self.google_adk_instrumentation_enabled:
                    from openinference.instrumentation.google_adk import GoogleADKInstrumentor

                    GoogleADKInstrumentor().instrument()
                if self.google_genai_instrumentation_enabled:
                    from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor

                    GoogleGenAIInstrumentor().instrument()
                self._instrumentation_ready = True
                self._instrumentation_error = ""
            except Exception as exc:  # pragma: no cover - environment specific
                self._instrumentation_ready = False
                self._instrumentation_error = str(exc)

    @staticmethod
    def _adk_installed() -> bool:
        try:
            import google.adk  # noqa: F401

            return True
        except Exception:
            return False

    @staticmethod
    def _phoenix_mcp_config_present() -> bool:
        config_path = Path(__file__).resolve().parents[2] / "deployment" / "mcp" / "phoenix-mcp.sample.json"
        return config_path.exists()


class _MockStructuredLlm(BaseLlm):
    model: str = "visaflow-adk-mock"
    responses: list[LlmResponse] = []
    response_index: int = -1

    @classmethod
    def supported_models(cls) -> list[str]:
        return [cls.model]

    @classmethod
    def create(cls, response_payload: dict[str, Any]):
        response = LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(text=json.dumps(response_payload, sort_keys=True))],
            )
        )
        return cls(responses=[response])

    async def generate_content_async(self, llm_request, stream: bool = False) -> AsyncGenerator[Any, None]:
        self.response_index += 1
        yield self.responses[self.response_index]
