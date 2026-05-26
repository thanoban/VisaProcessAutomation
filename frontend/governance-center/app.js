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
  try {
    await api.getHealth();
    state.apiAvailable = true;
    elements.apiPill.textContent = `Live API: ${api.baseUrl}`;
    const [requirements, rules, observability] = await Promise.all([
      api.getPolicyRequirements("TOURIST"),
      api.getActiveGovernanceRules(),
      api.getObservabilityStatus(),
    ]);
    elements.heroCopy.textContent =
      "Live API connected. The rule pack, policy source, and publication state below reflect the current backend governance references.";
    renderGovernanceCenter(requirements, rules, observability);
  } catch {
    state.apiAvailable = false;
    elements.apiPill.textContent = "Mock preview mode";
    elements.heroCopy.textContent =
      "The backend is not currently reachable, so this screen is showing a contract-aligned governance reference preview.";
    renderGovernanceCenter(
      governanceCenterMock.requirements,
      governanceCenterMock.rules,
      governanceCenterMock.observability
    );
  } finally {
    setRegionBusy(elements.activePolicyGrid, false);
    setRegionBusy(elements.publicationSignalGrid, false);
    setRegionBusy(elements.traceabilityList, false);
    setRegionBusy(elements.observabilityStatusList, false);
  }
}

function renderGovernanceCenter(requirements, rules, observability) {
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

initialize();
