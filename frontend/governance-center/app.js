import {
  buildStatusChip,
  createApiClient,
  formatDate,
  getStoredApiBaseUrl,
  governanceCenterMock,
  linkListMarkup,
  linkMarkup,
  listMarkup,
  renderInternalSurfaceGate,
  renderSurfaceNavigation,
  setRegionBusy,
  titleCase,
} from "../shared/app.js";

const elements = {
  apiPill: document.querySelector("#governance-api-pill"),
  heroCopy: document.querySelector("#governance-hero-copy"),
  surfaceNav: document.querySelector("#surface-nav"),
  surfaceAccessNote: document.querySelector("#surface-access-note"),
  internalSurfaceGate: document.querySelector("#internal-surface-gate"),
  protectedSurfaceShell: document.querySelector("#protected-surface-shell"),
  activePolicyGrid: document.querySelector("#active-policy-grid"),
  publicationSignalGrid: document.querySelector("#publication-signal-grid"),
  requirementsList: document.querySelector("#requirements-list"),
  circularsList: document.querySelector("#circulars-list"),
  sourcesList: document.querySelector("#sources-list"),
  traceabilityList: document.querySelector("#traceability-list"),
  observabilityStatusList: document.querySelector("#observability-status-list"),
  agentRuntimeStatusList: document.querySelector("#agent-runtime-status-list"),
  agentRuntimeNotesList: document.querySelector("#agent-runtime-notes-list"),
  observabilityReadinessList: document.querySelector("#observability-readiness-list"),
  observabilityGuardrailsList: document.querySelector("#observability-guardrails-list"),
  exceptionRulesList: document.querySelector("#exception-rules-list"),
};

const state = {
  apiBaseUrl: getStoredApiBaseUrl(),
  apiAvailable: false,
};

const api = createApiClient(state.apiBaseUrl);

async function initialize() {
  renderSurfaceNavigation({
    navElement: elements.surfaceNav,
    noticeElement: elements.surfaceAccessNote,
    currentSurface: "governance",
    homeHref: "../",
    navLinks: [
      { label: "Frontend Home", href: "../", surface: "home" },
      { label: "Applicant Portal", href: "../applicant-portal/", surface: "applicant" },
      { label: "Officer Dashboard", href: "../officer-dashboard/", surface: "officer" },
      { label: "Supervisor Dashboard", href: "../supervisor-dashboard/", surface: "supervisor" },
      { label: "Governance Center", href: "./", surface: "governance" },
    ],
  });
  const canAccessSurface = renderInternalSurfaceGate({
    gateElement: elements.internalSurfaceGate,
    protectedElement: elements.protectedSurfaceShell,
    surfaceTitle: "The governance center",
    detail:
      "Role-scoped mode intentionally hides internal rule-pack traceability, publication drift checks, and source-lineage tooling outside workspace preview.",
    homeHref: "../",
  });
  if (!canAccessSurface) {
    elements.heroCopy.textContent =
      "Internal workspace preview is required before governance reference tooling is shown on this surface.";
    elements.apiPill.textContent = "Role-scoped mode";
    return;
  }
  setRegionBusy(elements.activePolicyGrid, true);
  setRegionBusy(elements.publicationSignalGrid, true);
  setRegionBusy(elements.traceabilityList, true);
  setRegionBusy(elements.observabilityStatusList, true);
  setRegionBusy(elements.agentRuntimeStatusList, true);
  setRegionBusy(elements.agentRuntimeNotesList, true);
  setRegionBusy(elements.observabilityReadinessList, true);
  setRegionBusy(elements.observabilityGuardrailsList, true);
  try {
    await api.getHealth();
    state.apiAvailable = true;
    elements.apiPill.textContent = `Live API: ${api.baseUrl}`;
    const [requirements, rules, observability, agentRuntime] = await Promise.all([
      api.getPolicyRequirements("TOURIST"),
      api.getActiveGovernanceRules(),
      api.getObservabilityStatus(),
      api.getAgentRuntimeStatus(),
    ]);
    elements.heroCopy.textContent =
      "Live API connected. The rule pack, policy source, and publication state below reflect the current backend governance references.";
    renderGovernanceCenter(requirements, rules, observability, agentRuntime);
  } catch {
    state.apiAvailable = false;
    elements.apiPill.textContent = "Mock preview mode";
    elements.heroCopy.textContent =
      "The backend is not currently reachable, so this screen is showing a contract-aligned governance reference preview.";
    renderGovernanceCenter(
      governanceCenterMock.requirements,
      governanceCenterMock.rules,
      governanceCenterMock.observability,
      governanceCenterMock.agentRuntime
    );
  } finally {
    setRegionBusy(elements.activePolicyGrid, false);
    setRegionBusy(elements.publicationSignalGrid, false);
    setRegionBusy(elements.traceabilityList, false);
    setRegionBusy(elements.observabilityStatusList, false);
    setRegionBusy(elements.agentRuntimeStatusList, false);
    setRegionBusy(elements.agentRuntimeNotesList, false);
    setRegionBusy(elements.observabilityReadinessList, false);
    setRegionBusy(elements.observabilityGuardrailsList, false);
  }
}

function renderGovernanceCenter(requirements, rules, observability, agentRuntime) {
  const activeVersion = rules.active_policy_version || {};
  const circulars = rules.active_circulars || [];
  const publications = circulars.flatMap((circular) => circular.publications || []);
  const sourceEntries = Array.from(new Set([...(rules.official_sources || []), ...(requirements.official_sources || [])]));
  const driftSignals = circulars.filter((circular) => String(circular.status || "").toUpperCase() !== "ACTIVE");
  const activePolicyItems = [
    ["Workflow pack", activeVersion.workflow_pack || rules.workflow_pack],
    ["Policy version", activeVersion.policy_version || requirements.policy_version],
    ["Rule version", activeVersion.rule_version || "Not available"],
    ["Effective date", formatDate(activeVersion.effective_date || requirements.effective_date)],
    ["Publication reference", activeVersion.publication_reference || "Not available"],
    ["Verified at", formatDate(rules.verified_at || requirements.verified_at)],
  ];

  elements.activePolicyGrid.innerHTML = activePolicyItems
    .map(
      ([label, value]) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${label}</span>
          <strong class="mt-2 block text-base font-extrabold text-slate-900">${value || "Not available"}</strong>
        </article>
      `
    )
    .join("");

  const publicationSignals = [
    [
      "Official sources",
      sourceEntries.length,
      "info",
      "Distinct official endpoints referenced by the active pack and policy requirements.",
    ],
    [
      "Circulars loaded",
      circulars.length,
      "info",
      "Circular or notice records currently exposed to officers and supervisors.",
    ],
    [
      "Publication channels",
      publications.length,
      publications.length ? "success" : "warning",
      "Published channel entries currently attached to the loaded circular set.",
    ],
    [
      "Potential drift signals",
      driftSignals.length,
      driftSignals.length ? "warning" : "success",
      driftSignals.length
        ? "At least one circular record is not marked ACTIVE, which means public wording drift should stay visible."
        : "No explicit publication drift signal is currently attached to the loaded circular set.",
    ],
  ];
  elements.publicationSignalGrid.innerHTML = publicationSignals
    .map(
      ([label, value, tone, description]) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${label}</span>
              <strong class="mt-2 block text-3xl font-extrabold text-slate-950">${value}</strong>
            </div>
            ${buildStatusChip(label, tone)}
          </div>
          <p class="text-sm leading-7 text-slate-600">${description}</p>
        </article>
      `
    )
    .join("");

  elements.requirementsList.innerHTML = listMarkup(
    (requirements.requirements || []).map(
      (item) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${item.policy_id}</span>
              <h3 class="mt-2 text-lg font-extrabold text-slate-900">${item.requirement}</h3>
            </div>
            ${buildStatusChip("active rule", "info")}
          </div>
        </article>
      `
    ),
    "No policy requirements are available yet."
  );

  elements.circularsList.innerHTML = listMarkup(
    (rules.active_circulars || []).map(
      (circular) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${circular.circular_id}</span>
              <h3 class="mt-2 text-lg font-extrabold text-slate-900">${circular.title}</h3>
            </div>
            ${buildStatusChip(circular.status)}
          </div>
          <p class="text-sm leading-7 text-slate-600"><strong class="text-slate-900">Public summary:</strong> ${circular.public_summary}</p>
          <p class="mt-3 text-sm leading-7 text-slate-600"><strong class="text-slate-900">Internal summary:</strong> ${circular.internal_summary}</p>
          <p class="mt-3 text-sm leading-7 text-slate-600"><strong class="text-slate-900">Legal owner:</strong> ${circular.legal_owner}</p>
          <div class="mt-4 grid gap-3">
            ${(circular.publications || [])
              .map(
                (publication) => `
                  <div class="rounded-[1.25rem] border border-slate-200/80 bg-slate-50/80 p-4 text-sm leading-6 text-slate-600">
                    <strong class="text-slate-900">${titleCase(publication.channel)}</strong><br />
                    Published: ${formatDate(publication.published_at)}<br />
                    Reference: <a class="text-teal-800 underline" href="${publication.reference}" target="_blank" rel="noreferrer">${publication.reference}</a><br />
                    ${publication.notes || ""}
                  </div>
                `
              )
              .join("")}
          </div>
        </article>
      `
    ),
    "No active circulars are available yet."
  );

  elements.sourcesList.innerHTML = listMarkup(
    sourceEntries.map(
      (source) => `
        <div class="rounded-[1.25rem] border border-slate-200/80 bg-white/80 p-4 text-sm leading-6 text-slate-700">
          ${linkMarkup(source)}
        </div>
      `
    ),
    "No official sources are available yet."
  );

  elements.traceabilityList.innerHTML = listMarkup(
    [
      `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">Active workflow pack trace</span>
              <h3 class="mt-2 text-lg font-extrabold text-slate-900">${activeVersion.workflow_pack || rules.workflow_pack}</h3>
            </div>
            ${buildStatusChip(activeVersion.rule_version || "rule pack", "info")}
          </div>
          <p class="text-sm leading-7 text-slate-600">
            <strong class="text-slate-900">Policy version:</strong> ${activeVersion.policy_version || requirements.policy_version}<br />
            <strong class="text-slate-900">Rule version:</strong> ${activeVersion.rule_version || "Not available"}<br />
            <strong class="text-slate-900">Publication reference:</strong> ${activeVersion.publication_reference || "Not available"}<br />
            <strong class="text-slate-900">Primary source URI:</strong> ${linkMarkup(requirements.source_uri || "Not available")}<br />
            <strong class="text-slate-900">Verified at:</strong> ${formatDate(rules.verified_at || requirements.verified_at)}
          </p>
        </article>
      `,
      `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">Official source stack</span>
              <h3 class="mt-2 text-lg font-extrabold text-slate-900">Policy and governance reference lineage</h3>
            </div>
            ${buildStatusChip(`${sourceEntries.length} linked sources`, sourceEntries.length ? "success" : "warning")}
          </div>
          <div class="grid gap-4 md:grid-cols-2">
            <div class="rounded-[1.25rem] border border-slate-200/80 bg-slate-50/80 p-4 text-sm leading-6 text-slate-700">
              <strong class="text-slate-900">Governance pack sources</strong>
              <div class="mt-3">${linkListMarkup(rules.official_sources)}</div>
            </div>
            <div class="rounded-[1.25rem] border border-slate-200/80 bg-slate-50/80 p-4 text-sm leading-6 text-slate-700">
              <strong class="text-slate-900">Policy requirement sources</strong>
              <div class="mt-3">${linkListMarkup(requirements.official_sources)}</div>
            </div>
          </div>
        </article>
      `,
      `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">Publication chain</span>
              <h3 class="mt-2 text-lg font-extrabold text-slate-900">How circular records map to outward channels</h3>
            </div>
            ${buildStatusChip(`${publications.length} channels`, publications.length ? "success" : "warning")}
          </div>
          <div class="grid gap-3">
            ${circulars
              .map(
                (circular) => `
                  <div class="rounded-[1.25rem] border border-slate-200/80 bg-slate-50/80 p-4 text-sm leading-6 text-slate-700">
                    <strong class="text-slate-900">${circular.circular_id}</strong> · ${titleCase(circular.status)}<br />
                    ${
                      (circular.publications || []).length
                        ? (circular.publications || [])
                            .map(
                              (publication) =>
                                `${titleCase(publication.channel)}: ${linkMarkup(publication.reference)}`
                            )
                            .join("<br />")
                        : "No publication channel entries are attached to this circular."
                    }
                  </div>
                `
              )
              .join("")}
          </div>
        </article>
      `,
      `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">Drift and mismatch watch</span>
              <h3 class="mt-2 text-lg font-extrabold text-slate-900">${
                driftSignals.length ? "Visibility required" : "No current mismatch signal"
              }</h3>
            </div>
            ${buildStatusChip(driftSignals.length ? "drift visible" : "stable", driftSignals.length ? "warning" : "success")}
          </div>
          <div class="grid gap-3">
            ${
              driftSignals.length
                ? driftSignals
                    .map(
                      (circular) => `
                        <div class="rounded-[1.25rem] border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900">
                          <strong>${circular.title}</strong><br />
                          Status: ${titleCase(circular.status)}<br />
                          ${circular.internal_summary || circular.public_summary}
                        </div>
                      `
                    )
                    .join("")
                : `<div class="rounded-[1.25rem] border border-emerald-200 bg-emerald-50 p-4 text-sm leading-6 text-emerald-900">The active circular set does not currently expose a non-active publication record.</div>`
            }
          </div>
        </article>
      `,
    ],
    "No governance traceability entries are available yet."
  );

  const observabilityCards = [
    ["Provider", observability.provider || "Phoenix", "info"],
    ["Status", observability.status || "DISABLED", observability.enabled ? "success" : "warning"],
    ["Target", observability.target || "LOCAL_ONLY", observability.enabled ? "info" : "warning"],
    ["Project", observability.project_name || "visaflow-mas", "info"],
    [
      "Google GenAI instrumentation",
      observability.google_genai_instrumentation_enabled ? "Enabled" : "Disabled",
      observability.google_genai_instrumentation_enabled ? "success" : "info",
    ],
    ["Phoenix MCP expected", observability.phoenix_mcp_expected ? "Yes" : "No", "info"],
  ];
  elements.observabilityStatusList.innerHTML = listMarkup(
    observabilityCards.map(
      ([label, value, tone]) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${label}</span>
              <strong class="mt-2 block text-base font-extrabold text-slate-900">${value}</strong>
            </div>
            ${buildStatusChip(value, tone)}
          </div>
        </article>
      `
    ),
    "Observability status is not available yet."
  );
  renderAgentRuntime(agentRuntime);
  renderObservabilityReadiness(observability);
  renderObservabilityGuardrails(observability);

  elements.exceptionRulesList.innerHTML = listMarkup(
    (rules.nationality_exception_rules || []).map(
      (rule) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${rule.rule_id}</span>
              <h3 class="mt-2 text-lg font-extrabold text-slate-900">${titleCase(rule.nationality)}</h3>
            </div>
            ${buildStatusChip(rule.requires_manual_review ? "manual review" : "standard route", rule.requires_manual_review ? "warning" : "success")}
          </div>
          <p class="text-sm leading-7 text-slate-600"><strong class="text-slate-900">Routing target:</strong> ${titleCase(rule.routing_target)}</p>
          <p class="mt-3 text-sm leading-7 text-slate-600"><strong class="text-slate-900">Sponsor required:</strong> ${rule.requires_sponsor ? "Yes" : "No"}</p>
          <p class="mt-3 text-sm leading-7 text-slate-600">${rule.reason}</p>
        </article>
      `
    ),
    "No nationality exception rules are available yet."
  );

  if (driftSignals.length) {
    elements.heroCopy.textContent =
      "The governance data currently includes non-active circular records alongside the active rule pack, so publication drift is being surfaced instead of hidden.";
  }
}

function renderAgentRuntime(agentRuntime) {
  const runtimeCards = [
    ["Runtime", agentRuntime.runtime || "GOOGLE_ADK", "info"],
    ["Provider", agentRuntime.provider || "Gemini", "info"],
    ["Status", agentRuntime.status || "DEGRADED", agentRuntime.live_model_available ? "success" : "warning"],
    ["Configured", agentRuntime.configured ? "Yes" : "No", agentRuntime.configured ? "success" : "warning"],
    ["Model", agentRuntime.model_name || "Not configured", "info"],
    ["Phoenix MCP config", agentRuntime.phoenix_mcp_config_present ? "Present" : "Missing", agentRuntime.phoenix_mcp_config_present ? "success" : "warning"],
    [
      "ADK instrumentation",
      agentRuntime.google_adk_instrumentation_enabled ? "Enabled" : "Disabled",
      agentRuntime.google_adk_instrumentation_enabled ? "success" : "info",
    ],
    [
      "GenAI instrumentation",
      agentRuntime.google_genai_instrumentation_enabled ? "Enabled" : "Disabled",
      agentRuntime.google_genai_instrumentation_enabled ? "success" : "info",
    ],
  ];

  elements.agentRuntimeStatusList.innerHTML = listMarkup(
    runtimeCards.map(
      ([label, value, tone]) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${label}</span>
              <strong class="mt-2 block text-base font-extrabold text-slate-900">${value}</strong>
            </div>
            ${buildStatusChip(value, tone)}
          </div>
        </article>
      `
    ),
    "Agent runtime status is not available yet."
  );

  const notes = [
    `Configured agent set: ${(agentRuntime.agent_names || []).join(", ") || "Not available"}`,
    ...(agentRuntime.notes || []),
  ];

  elements.agentRuntimeNotesList.innerHTML = listMarkup(
    notes.map(
      (note) => `
        <div class="rounded-[1.25rem] border border-slate-200/80 bg-white/80 p-4 text-sm leading-7 text-slate-700">
          ${note}
        </div>
      `
    ),
    "No agent runtime notes are available yet."
  );
}

function renderObservabilityReadiness(observability) {
  const status = String(observability.status || "DISABLED").toUpperCase();
  const readiness = observabilityReadinessState(status, observability);
  const checklist = observabilityReadinessChecklist(status, observability);

  elements.observabilityReadinessList.innerHTML = listMarkup(
    [
      `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">Runtime readiness</span>
              <h3 class="mt-2 text-lg font-extrabold text-slate-900">${readiness.title}</h3>
            </div>
            ${buildStatusChip(readiness.badge, readiness.tone)}
          </div>
          <p class="text-sm leading-7 text-slate-600">${readiness.message}</p>
        </article>
      `,
      `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">Deployment checklist</span>
              <h3 class="mt-2 text-lg font-extrabold text-slate-900">What the current status implies</h3>
            </div>
            ${buildStatusChip(`${checklist.length} checks`, checklist.length ? "info" : "success")}
          </div>
          <div class="grid gap-3">
            ${checklist
              .map(
                (item) => `
                  <div class="rounded-[1.25rem] border border-slate-200/80 bg-slate-50/80 p-4 text-sm leading-6 text-slate-700">
                    <strong class="text-slate-900">${item.title}</strong><br />
                    ${item.body}
                  </div>
                `
              )
              .join("")}
          </div>
        </article>
      `,
    ],
    "Observability readiness guidance is not available yet."
  );
}

function renderObservabilityGuardrails(observability) {
  const instrumentationState = observability.google_genai_instrumentation_enabled ? "enabled" : "disabled";
  const mcpState = observability.phoenix_mcp_expected ? "expected" : "optional";
  const guardrails = [
    {
      title: "Redaction policy",
      tone: "warning",
      body:
        "Phoenix is the redacted observability plane. Full name, date of birth, passport number, contact email, phone, file URI, and destination address should stay out of exported traces.",
    },
    {
      title: "Instrumentation posture",
      tone: observability.google_genai_instrumentation_enabled ? "success" : "info",
      body: `Google GenAI instrumentation is currently ${instrumentationState}. Enable it only when the deployment target is ready to export redacted traces safely.`,
    },
    {
      title: "MCP review path",
      tone: observability.phoenix_mcp_expected ? "info" : "success",
      body: `Phoenix MCP is ${mcpState} for this setup. The intended operator flow is to inspect weak traces, compare runs, and review missing policy citations before changing prompts or routing.`,
    },
  ];

  elements.observabilityGuardrailsList.innerHTML = listMarkup(
    guardrails.map(
      (item) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">Governance guardrail</span>
              <h3 class="mt-2 text-lg font-extrabold text-slate-900">${item.title}</h3>
            </div>
            ${buildStatusChip(item.title, item.tone)}
          </div>
          <p class="text-sm leading-7 text-slate-600">${item.body}</p>
        </article>
      `
    ),
    "Observability guardrails are not available yet."
  );
}

function observabilityReadinessState(status, observability) {
  switch (status) {
    case "READY":
      return {
        title: "Phoenix export path is ready",
        badge: "ready",
        tone: "success",
        message: `Observability is enabled for the ${observability.target || "configured"} target and the runtime is reporting ready status for project ${
          observability.project_name || "visaflow-mas"
        }.`,
      };
    case "DEGRADED":
      return {
        title: "Export is enabled but runtime is degraded",
        badge: "degraded",
        tone: "warning",
        message:
          "The deployment intends to export traces, but the runtime is not fully healthy. Operators should treat audit storage as the source of truth while fixing the Phoenix runtime path.",
      };
    case "PENDING":
      return {
        title: "Export path is enabled and still warming up",
        badge: "pending",
        tone: "info",
        message:
          "The backend is configured for observability, but the runtime has not yet confirmed readiness. This usually means the process has not completed runtime initialization or a first export cycle yet.",
      };
    default:
      return {
        title: "Observability is intentionally disabled",
        badge: "disabled",
        tone: "warning",
        message:
          "This deployment is still running local-audit-only mode. That is acceptable for early local work, but Phoenix setup is still required for the observability and evaluation track.",
      };
  }
}

function observabilityReadinessChecklist(status, observability) {
  if (status === "READY") {
    return [
      {
        title: "Keep audit as source of truth",
        body: "Continue treating local audit records as the legal reconstruction layer even when Phoenix is exporting successfully.",
      },
      {
        title: "Validate redaction continuously",
        body: "Spot-check traces for the expected redaction policy before using Phoenix data for prompt or routing analysis.",
      },
      {
        title: "Use MCP for comparisons",
        body: `Phoenix MCP is ${observability.phoenix_mcp_expected ? "expected" : "optional"} here, so trace comparison and weak-run review should happen through that path rather than ad hoc screenshots.`,
      },
    ];
  }

  if (status === "DEGRADED" || status === "PENDING") {
    return [
      {
        title: "Confirm deployment flags",
        body:
          "Check `VISAFLOW_OBSERVABILITY_ENABLED`, `VISAFLOW_OBSERVABILITY_TARGET`, and `PHOENIX_PROJECT_NAME` before assuming the export path is healthy.",
      },
      {
        title: "Verify Phoenix runtime packages",
        body:
          "The runtime needs the Phoenix and OpenInference packages present before traces can export cleanly.",
      },
      {
        title: "Preserve fallback behavior",
        body:
          "Case processing should keep running even while observability is degraded. Treat audit and case status APIs as the operational fallback until runtime health is restored.",
      },
    ];
  }

  return [
    {
      title: "Enable the backend flag",
      body: "Set `VISAFLOW_OBSERVABILITY_ENABLED=1` when you want the deployment to move beyond local-audit-only mode.",
    },
    {
      title: "Set Phoenix target details",
      body:
        "Configure `VISAFLOW_OBSERVABILITY_TARGET`, `PHOENIX_PROJECT_NAME`, `PHOENIX_COLLECTOR_ENDPOINT`, and `PHOENIX_API_KEY` for the real export destination.",
    },
    {
      title: "Choose instrumentation deliberately",
      body:
        "Enable Google GenAI instrumentation only when the deployment is ready to export redacted traces and evaluation metadata safely.",
    },
  ];
}

initialize();
