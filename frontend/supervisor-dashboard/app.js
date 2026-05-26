import {
  buildStatusChip,
  createApiClient,
  getStoredApiBaseUrl,
  listMarkup,
  setButtonBusy,
  setRegionBusy,
  supervisorDashboardMock,
  titleCase,
} from "../shared/app.js";

const elements = {
  apiPill: document.querySelector("#supervisor-api-pill"),
  heroCopy: document.querySelector("#supervisor-hero-copy"),
  refreshButton: document.querySelector("#refresh-queues-button"),
  filterForm: document.querySelector("#supervisor-filter-form"),
  clearFiltersButton: document.querySelector("#clear-filters-button"),
  stateFilter: document.querySelector("#supervisor-state-filter"),
  holderFilter: document.querySelector("#supervisor-holder-filter"),
  metrics: document.querySelector("#supervisor-metrics"),
  stateCounts: document.querySelector("#state-counts-list"),
  caseMeta: document.querySelector("#supervisor-case-meta"),
  activeFilters: document.querySelector("#supervisor-active-filters"),
  caseList: document.querySelector("#supervisor-case-list"),
  hotspotList: document.querySelector("#hotspot-list"),
  noticeList: document.querySelector("#supervisor-notice-list"),
};

const state = {
  apiBaseUrl: getStoredApiBaseUrl(),
  apiAvailable: false,
  filters: {
    state: "",
    holder: "",
  },
};

const api = createApiClient(state.apiBaseUrl);

async function initialize() {
  elements.refreshButton.addEventListener("click", loadSupervisorData);
  elements.filterForm.addEventListener("change", handleFilterChange);
  elements.clearFiltersButton.addEventListener("click", clearFilters);
  elements.metrics.addEventListener("click", handleDrillDownClick);
  elements.stateCounts.addEventListener("click", handleDrillDownClick);
  readInitialFilters();
  syncFilterControls();
  await loadSupervisorData();
}

async function loadSupervisorData() {
  setButtonBusy(elements.refreshButton, true, "Refreshing queues...");
  setRegionBusy(elements.metrics, true);
  setRegionBusy(elements.caseList, true);
  elements.caseMeta.textContent = "Loading supervisor case drill-down.";

  try {
    await api.getHealth();
    state.apiAvailable = true;
    elements.apiPill.textContent = `Live API: ${api.baseUrl}`;
    const [queues, notices, cases] = await Promise.all([
      api.getSupervisorQueues(),
      api.getSystemNotices(),
      api.getSupervisorCases(state.filters),
    ]);
    elements.heroCopy.textContent =
      "Live API connected. Queue counts below reflect the current workflow inventory and supervisor-visible backlog signals.";
    renderSupervisorDashboard(queues, notices, cases);
  } catch {
    state.apiAvailable = false;
    elements.apiPill.textContent = "Mock preview mode";
    elements.heroCopy.textContent =
      "The backend is not currently reachable, so this screen is showing a contract-aligned mock operations view.";
    renderSupervisorDashboard(
      supervisorDashboardMock.queues,
      supervisorDashboardMock.notices,
      applyMockFilters(supervisorDashboardMock.cases, state.filters)
    );
  } finally {
    setButtonBusy(elements.refreshButton, false, "Refreshing queues...");
    setRegionBusy(elements.metrics, false);
    setRegionBusy(elements.caseList, false);
  }
}

function renderSupervisorDashboard(queues, notices, casesResponse) {
  const totalCases = Object.values(queues.counts_by_state || {}).reduce((sum, value) => sum + value, 0);
  const metrics = [
    ["Total active cases", totalCases, "info", "", "", "Show all cases"],
    [
      "Manual referrals",
      queues.manual_referrals,
      queues.manual_referrals > 0 ? "warning" : "success",
      "REFERRED_TO_MANUAL_REVIEW",
      "MISSION_OR_HEAD_OFFICE",
      "Open manual referral cases",
    ],
    [
      "Waiting for documents",
      queues.waiting_for_documents,
      queues.waiting_for_documents > 0 ? "warning" : "success",
      "WAITING_FOR_DOCUMENTS",
      "APPLICANT",
      "Open waiting cases",
    ],
    [
      "Ready for officer review",
      queues.ready_for_officer_review,
      queues.ready_for_officer_review > 0 ? "info" : "warning",
      "READY_FOR_OFFICER_REVIEW",
      "OFFICER",
      "Open officer-ready cases",
    ],
  ];

  elements.metrics.innerHTML = metrics
    .map(
      ([label, value, tone, filterState, filterHolder, buttonLabel]) => `
        <article class="rounded-3xl border border-slate-200/80 bg-white/85 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${label}</span>
              <strong class="mt-3 block text-3xl font-extrabold text-slate-950">${value}</strong>
            </div>
            ${buildStatusChip(label, tone)}
          </div>
          <button
            class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5"
            type="button"
            data-filter-state="${filterState}"
            data-filter-holder="${filterHolder}"
          >
            ${buttonLabel}
          </button>
        </article>
      `
    )
    .join("");

  renderActiveFilters();
  elements.stateCounts.innerHTML = listMarkup(
    Object.entries(queues.counts_by_state || {}).map(
      ([stateName, count]) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${titleCase(stateName)}</span>
              <strong class="mt-2 block text-2xl font-extrabold text-slate-950">${count}</strong>
            </div>
            ${buildStatusChip(stateName)}
          </div>
          <button
            class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5"
            type="button"
            data-filter-state="${stateName}"
            data-filter-holder=""
          >
            Show matching cases
          </button>
        </article>
      `
    ),
    "No queue states are available yet."
  );

  elements.caseMeta.textContent = `Showing ${casesResponse.filtered_count} of ${casesResponse.total_cases} supervisor-visible cases.${buildFilterSummaryText()}`;
  elements.caseList.innerHTML = listMarkup(
    (casesResponse.cases || []).map(
      (item) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${item.case_id}</span>
              <h3 class="mt-2 text-lg font-extrabold text-slate-900">${item.applicant_name}</h3>
              <p class="mt-2 text-sm leading-7 text-slate-600">${titleCase(item.nationality)} | ${titleCase(item.visa_class)} | Updated ${formatCaseTimestamp(item.updated_at)}</p>
            </div>
            <div class="flex flex-wrap gap-2">
              ${buildStatusChip(item.current_state)}
              ${buildStatusChip(item.current_holder)}
            </div>
          </div>
          <div class="grid gap-4 md:grid-cols-2">
            <div class="rounded-[1.25rem] border border-slate-200/80 bg-slate-50/80 p-4 text-sm leading-7 text-slate-600">
              <strong class="text-slate-900">Next action:</strong> ${titleCase(item.next_action)}<br />
              <strong class="text-slate-900">Action required from:</strong> ${titleCase(item.action_required_from)}<br />
              <strong class="text-slate-900">ETA status:</strong> ${titleCase(item.eta_status)}
            </div>
            <div class="rounded-[1.25rem] border border-slate-200/80 bg-slate-50/80 p-4 text-sm leading-7 text-slate-600">
              <strong class="text-slate-900">Rule version:</strong> ${item.rule_version_used || "Not available"}<br />
              <strong class="text-slate-900">Publication reference:</strong> ${item.publication_reference || "Not available"}<br />
              <strong class="text-slate-900">Decision due:</strong> ${formatCaseTimestamp(item.decision_due_at)}
            </div>
          </div>
          <div class="mt-4 flex flex-wrap gap-3">
            <a
              class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5"
              href="../officer-dashboard/?case=${encodeURIComponent(item.case_id)}"
            >
              Open officer view
            </a>
            <a
              class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5"
              href="../applicant-portal/?case=${encodeURIComponent(item.case_id)}"
            >
              Open applicant view
            </a>
          </div>
          ${
            item.manual_referral_reason
              ? `<div class="mt-4 rounded-[1.25rem] border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900"><strong>Manual referral reason:</strong> ${item.manual_referral_reason}</div>`
              : ""
          }
        </article>
      `
    ),
    "No cases match the current supervisor filters."
  );

  const hotspots = buildHotspots(queues);
  elements.hotspotList.innerHTML = listMarkup(
    hotspots.map(
      (item) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${item.code}</span>
              <h3 class="mt-2 text-lg font-extrabold text-slate-900">${item.title}</h3>
            </div>
            ${buildStatusChip(item.level, item.tone)}
          </div>
          <p class="text-sm leading-7 text-slate-600">${item.message}</p>
        </article>
      `
    ),
    "No intervention hotspots are currently visible."
  );

  elements.noticeList.innerHTML = listMarkup(
    (notices || []).map(
      (notice) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${notice.code}</span>
              <h3 class="mt-2 text-lg font-extrabold text-slate-900">${titleCase(notice.level)}</h3>
            </div>
            ${buildStatusChip(notice.level)}
          </div>
          <p class="text-sm leading-7 text-slate-600">${notice.message}</p>
        </article>
      `
    ),
    "No service notices are currently published."
  );
}

function handleFilterChange() {
  applyFilters({
    state: elements.stateFilter.value,
    holder: elements.holderFilter.value,
  });
}

function handleDrillDownClick(event) {
  const button = event.target.closest("[data-filter-state],[data-filter-holder]");
  if (!button) {
    return;
  }
  applyFilters({
    state: button.dataset.filterState ?? state.filters.state,
    holder: button.dataset.filterHolder ?? state.filters.holder,
  });
}

function applyFilters(nextFilters) {
  state.filters.state = String(nextFilters.state || "");
  state.filters.holder = String(nextFilters.holder || "");
  syncFilterQueryParams();
  syncFilterControls();
  loadSupervisorData();
}

function clearFilters() {
  applyFilters({ state: "", holder: "" });
}

function syncFilterControls() {
  elements.stateFilter.value = state.filters.state;
  elements.holderFilter.value = state.filters.holder;
}

function readInitialFilters() {
  const params = new URLSearchParams(window.location.search);
  state.filters.state = String(params.get("state") || "");
  state.filters.holder = String(params.get("holder") || "");
}

function syncFilterQueryParams() {
  const params = new URLSearchParams(window.location.search);
  if (state.filters.state) {
    params.set("state", state.filters.state);
  } else {
    params.delete("state");
  }
  if (state.filters.holder) {
    params.set("holder", state.filters.holder);
  } else {
    params.delete("holder");
  }
  const nextQuery = params.toString();
  const nextUrl = `${window.location.pathname}${nextQuery ? `?${nextQuery}` : ""}`;
  window.history.replaceState({}, "", nextUrl);
}

function renderActiveFilters() {
  const activeFilters = [];
  if (state.filters.state) {
    activeFilters.push(`
      <div class="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700">
        State: ${titleCase(state.filters.state)}
      </div>
    `);
  }
  if (state.filters.holder) {
    activeFilters.push(`
      <div class="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700">
        Holder: ${titleCase(state.filters.holder)}
      </div>
    `);
  }

  elements.activeFilters.innerHTML = activeFilters.length
    ? `${activeFilters.join("")}<button class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5" type="button" data-clear-filters="true">Reset drill-down</button>`
    : `<div class="rounded-full border border-dashed border-slate-300 bg-white/50 px-4 py-2 text-sm text-slate-500">Use the metric and state cards above to drill directly into the queue.</div>`;
  elements.activeFilters.querySelector("[data-clear-filters]")?.addEventListener("click", clearFilters);
}

function buildFilterSummaryText() {
  const activeParts = [];
  if (state.filters.state) {
    activeParts.push(`state ${titleCase(state.filters.state)}`);
  }
  if (state.filters.holder) {
    activeParts.push(`holder ${titleCase(state.filters.holder)}`);
  }
  return activeParts.length ? ` Active filters: ${activeParts.join(", ")}.` : "";
}

function applyMockFilters(casesResponse, filters) {
  const stateFilter = String(filters.state || "").toUpperCase();
  const holderFilter = String(filters.holder || "").toUpperCase();
  const cases = (casesResponse.cases || []).filter((item) => {
    if (stateFilter && item.current_state !== stateFilter) {
      return false;
    }
    if (holderFilter && item.current_holder !== holderFilter) {
      return false;
    }
    return true;
  });
  return {
    ...casesResponse,
    filtered_count: cases.length,
    state_filter: stateFilter,
    holder_filter: holderFilter,
    cases,
  };
}

function formatCaseTimestamp(value) {
  if (!value) {
    return "Not set";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(parsed);
}

function buildHotspots(queues) {
  const hotspots = [];

  if (queues.waiting_for_documents > 0) {
    hotspots.push({
      code: "DOC_LOOP",
      title: "Document-loop backlog detected",
      level: "warning",
      tone: "warning",
      message:
        "Applicants are currently waiting on replacement or additional evidence. Review whether unreadable or incomplete cases are lingering without intervention.",
    });
  }

  if (queues.manual_referrals > 0) {
    hotspots.push({
      code: "MANUAL_REFERRAL",
      title: "Manual referral queue needs oversight",
      level: "warning",
      tone: "warning",
      message:
        "Nationality, sponsor, or exception-driven cases are sitting outside the straight-through path and may require mission or head-office attention.",
    });
  }

  if (queues.ready_for_officer_review > 0) {
    hotspots.push({
      code: "OFFICER_LOAD",
      title: "Officer-ready inventory is available",
      level: "info",
      tone: "info",
      message:
        "Cases are ready for human review. Use this signal to balance reviewer load before delays turn into avoidable backlog.",
    });
  }

  if (!hotspots.length) {
    hotspots.push({
      code: "STABLE",
      title: "No major pressure signal detected",
      level: "success",
      tone: "success",
      message:
        "The current mock or live queue does not show a high-pressure hotspot. Continue monitoring for document loops and manual referrals.",
    });
  }

  return hotspots;
}

initialize();
