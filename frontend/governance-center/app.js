import {
  buildStatusChip,
  createApiClient,
  formatDate,
  governanceCenterMock,
  listMarkup,
  titleCase,
} from "../shared/app.js";

const elements = {
  apiPill: document.querySelector("#governance-api-pill"),
  heroCopy: document.querySelector("#governance-hero-copy"),
  activePolicyGrid: document.querySelector("#active-policy-grid"),
  requirementsList: document.querySelector("#requirements-list"),
  circularsList: document.querySelector("#circulars-list"),
  sourcesList: document.querySelector("#sources-list"),
  exceptionRulesList: document.querySelector("#exception-rules-list"),
};

const state = {
  apiBaseUrl: localStorage.getItem("visaFlowApiBaseUrl") || "http://127.0.0.1:8000",
  apiAvailable: false,
};

const api = createApiClient(state.apiBaseUrl);

async function initialize() {
  try {
    await api.getHealth();
    state.apiAvailable = true;
    elements.apiPill.textContent = `Live API: ${api.baseUrl}`;
    const [requirements, rules] = await Promise.all([
      api.getPolicyRequirements("TOURIST"),
      api.getActiveGovernanceRules(),
    ]);
    elements.heroCopy.textContent =
      "Live API connected. The rule pack, policy source, and publication state below reflect the current backend governance references.";
    renderGovernanceCenter(requirements, rules);
  } catch {
    state.apiAvailable = false;
    elements.apiPill.textContent = "Mock preview mode";
    elements.heroCopy.textContent =
      "The backend is not currently reachable, so this screen is showing a contract-aligned governance reference preview.";
    renderGovernanceCenter(governanceCenterMock.requirements, governanceCenterMock.rules);
  }
}

function renderGovernanceCenter(requirements, rules) {
  const activeVersion = rules.active_policy_version || {};
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

  const sourceEntries = Array.from(new Set([...(rules.official_sources || []), ...(requirements.official_sources || [])]));
  elements.sourcesList.innerHTML = listMarkup(
    sourceEntries.map(
      (source) => `
        <a class="rounded-[1.25rem] border border-slate-200/80 bg-white/80 p-4 text-sm leading-6 text-teal-800 underline break-all" href="${source}" target="_blank" rel="noreferrer">
          ${source}
        </a>
      `
    ),
    "No official sources are available yet."
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
}

initialize();
