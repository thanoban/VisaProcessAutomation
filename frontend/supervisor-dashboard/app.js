import {
  buildStatusChip,
  createApiClient,
  listMarkup,
  supervisorDashboardMock,
  titleCase,
} from "../shared/app.js";

const elements = {
  apiPill: document.querySelector("#supervisor-api-pill"),
  heroCopy: document.querySelector("#supervisor-hero-copy"),
  refreshButton: document.querySelector("#refresh-queues-button"),
  metrics: document.querySelector("#supervisor-metrics"),
  stateCounts: document.querySelector("#state-counts-list"),
  hotspotList: document.querySelector("#hotspot-list"),
  noticeList: document.querySelector("#supervisor-notice-list"),
};

const state = {
  apiBaseUrl: localStorage.getItem("visaFlowApiBaseUrl") || "http://127.0.0.1:8000",
  apiAvailable: false,
};

const api = createApiClient(state.apiBaseUrl);

async function initialize() {
  elements.refreshButton.addEventListener("click", loadSupervisorData);
  await loadSupervisorData();
}

async function loadSupervisorData() {
  try {
    await api.getHealth();
    state.apiAvailable = true;
    elements.apiPill.textContent = `Live API: ${api.baseUrl}`;
    const [queues, notices] = await Promise.all([api.getSupervisorQueues(), api.getSystemNotices()]);
    elements.heroCopy.textContent =
      "Live API connected. Queue counts below reflect the current workflow inventory and supervisor-visible backlog signals.";
    renderSupervisorDashboard(queues, notices);
  } catch {
    state.apiAvailable = false;
    elements.apiPill.textContent = "Mock preview mode";
    elements.heroCopy.textContent =
      "The backend is not currently reachable, so this screen is showing a contract-aligned mock operations view.";
    renderSupervisorDashboard(supervisorDashboardMock.queues, supervisorDashboardMock.notices);
  }
}

function renderSupervisorDashboard(queues, notices) {
  const totalCases = Object.values(queues.counts_by_state || {}).reduce((sum, value) => sum + value, 0);
  const metrics = [
    ["Total active cases", totalCases, "info"],
    ["Manual referrals", queues.manual_referrals, queues.manual_referrals > 0 ? "warning" : "success"],
    [
      "Waiting for documents",
      queues.waiting_for_documents,
      queues.waiting_for_documents > 0 ? "warning" : "success",
    ],
    [
      "Ready for officer review",
      queues.ready_for_officer_review,
      queues.ready_for_officer_review > 0 ? "info" : "warning",
    ],
  ];

  elements.metrics.innerHTML = metrics
    .map(
      ([label, value, tone]) => `
        <article class="rounded-3xl border border-slate-200/80 bg-white/85 p-5">
          <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${label}</span>
          <strong class="mt-3 block text-3xl font-extrabold text-slate-950">${value}</strong>
          <div class="mt-4">${buildStatusChip(label, tone)}</div>
        </article>
      `
    )
    .join("");

  elements.stateCounts.innerHTML = listMarkup(
    Object.entries(queues.counts_by_state || {}).map(
      ([stateName, count]) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${titleCase(stateName)}</span>
          <strong class="mt-2 block text-2xl font-extrabold text-slate-950">${count}</strong>
        </article>
      `
    ),
    "No queue states are available yet."
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
