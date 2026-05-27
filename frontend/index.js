import {
  appendWorkspacePreviewParam,
  applicantPortalMock,
  buildStatusChip,
  clearStoredApiBaseUrl,
  createApiClient,
  formatDateTime,
  governanceCenterMock,
  isExtensionWorkflowActive,
  getRecentCases,
  getStoredApiBaseUrl,
  renderSurfaceNavigation,
  setButtonBusy,
  setRegionBusy,
  setStoredApiBaseUrl,
  supervisorDashboardMock,
  titleCase,
  workspacePreviewModeEnabled,
  workflowGlossary,
} from "./shared/app.js";

const elements = {
  snapshotModePill: document.querySelector("#snapshot-mode-pill"),
  snapshotFeedback: document.querySelector("#snapshot-feedback"),
  surfaceNav: document.querySelector("#surface-nav"),
  surfaceAccessNote: document.querySelector("#surface-access-note"),
  surfaceDirectoryNote: document.querySelector("#surface-directory-note"),
  operationalSnapshotSection: document.querySelector("#operational-snapshot-section"),
  recentWorkSection: document.querySelector("#recent-work-section"),
  surfaceCards: Array.from(document.querySelectorAll("[data-surface-card]")),
  homeOpsMetrics: document.querySelector("#home-ops-metrics"),
  homeNoticesList: document.querySelector("#home-notices-list"),
  homeGovernanceSummary: document.querySelector("#home-governance-summary"),
  apiPill: document.querySelector("#frontend-api-pill"),
  apiForm: document.querySelector("#api-target-form"),
  apiInput: document.querySelector("#api-base-url"),
  resetButton: document.querySelector("#reset-api-target-button"),
  currentTarget: document.querySelector("#current-api-target"),
  healthChip: document.querySelector("#api-health-chip"),
  feedback: document.querySelector("#api-target-feedback"),
  clearRecentCasesButton: document.querySelector("#clear-recent-cases-button"),
  recentCasesList: document.querySelector("#recent-cases-list"),
  workflowGlossaryList: document.querySelector("#workflow-glossary-list"),
};

async function initialize() {
  renderSurfaceNavigation({
    navElement: elements.surfaceNav,
    noticeElement: elements.surfaceAccessNote,
    currentSurface: "home",
    homeHref: "./",
    navLinks: [
      { label: "Frontend Home", href: "./", surface: "home" },
      { label: "Applicant Portal", href: "./applicant-portal/", surface: "applicant" },
      { label: "Officer Dashboard", href: "./officer-dashboard/", surface: "officer" },
      { label: "Supervisor Dashboard", href: "./supervisor-dashboard/", surface: "supervisor" },
      { label: "Governance Center", href: "./governance-center/", surface: "governance" },
    ],
  });
  renderHomeAccessMode();
  elements.apiInput.value = getStoredApiBaseUrl();
  elements.apiForm.addEventListener("submit", handleSaveTarget);
  elements.resetButton.addEventListener("click", handleResetTarget);
  elements.clearRecentCasesButton.addEventListener("click", handleClearRecentCases);
  renderRecentCases();
  renderGlossary();
  setRegionBusy(elements.homeOpsMetrics, true);
  setRegionBusy(elements.homeNoticesList, true);
  setRegionBusy(elements.homeGovernanceSummary, true);
  await refreshHealthState("Saved API target loaded.");
}

function renderHomeAccessMode() {
  if (workspacePreviewModeEnabled()) {
    elements.surfaceDirectoryNote.innerHTML = `
      <div class="rounded-[1.5rem] border border-teal-200 bg-teal-50 p-4 text-sm leading-7 text-teal-900">
        <strong class="text-teal-950">Internal workspace preview:</strong> all role surfaces and recent live-case shortcuts are visible for demo, QA, and operator walkthroughs.
      </div>
    `;
    elements.operationalSnapshotSection.hidden = false;
    elements.recentWorkSection.hidden = false;
    elements.surfaceCards.forEach((card) => {
      syncSurfaceCardHref(card, true);
      card.hidden = false;
    });
    return;
  }

  elements.surfaceDirectoryNote.innerHTML = `
    <div class="rounded-[1.5rem] border border-slate-200/80 bg-white/75 p-4 text-sm leading-7 text-slate-600">
      <strong class="text-slate-900">Role-scoped mode:</strong> the applicant portal stays visible publicly, while officer, supervisor, and governance surfaces remain restricted to internal workspace preview.
    </div>
  `;
  elements.operationalSnapshotSection.hidden = true;
  elements.recentWorkSection.hidden = true;
  elements.surfaceCards.forEach((card) => {
    syncSurfaceCardHref(card, false);
    card.hidden = card.dataset.surfaceCard !== "applicant";
  });
}

function syncSurfaceCardHref(card, workspaceMode = workspacePreviewModeEnabled()) {
  if (!card) {
    return;
  }
  const baseHref = card.dataset.baseHref || card.getAttribute("href") || "";
  card.setAttribute("href", appendWorkspacePreviewParam(baseHref, workspaceMode));
}

async function handleSaveTarget(event) {
  event.preventDefault();
  const nextValue = setStoredApiBaseUrl(elements.apiInput.value);
  elements.apiInput.value = nextValue;
  await refreshHealthState(`Saved API target: ${nextValue}`);
}

async function handleResetTarget() {
  const nextValue = clearStoredApiBaseUrl();
  elements.apiInput.value = nextValue;
  await refreshHealthState(`Reset API target to default: ${nextValue}`);
}

async function refreshHealthState(messagePrefix) {
  const apiBaseUrl = getStoredApiBaseUrl();
  const api = createApiClient(apiBaseUrl);
  elements.currentTarget.textContent = apiBaseUrl;
  setRegionBusy(elements.homeOpsMetrics, true);
  setRegionBusy(elements.homeNoticesList, true);
  setRegionBusy(elements.homeGovernanceSummary, true);
  setButtonBusy(elements.apiForm.querySelector("button[type='submit']"), true, "Saving...");
  setButtonBusy(elements.resetButton, true, "Resetting...");

  try {
    const health = await api.getHealth();
    const [queues, notices, rules, observability, submissionReadiness] = await Promise.all([
      api.getSupervisorQueues(),
      api.getSystemNotices(),
      api.getActiveGovernanceRules(),
      api.getObservabilityStatus(),
      api.getSubmissionReadiness(),
    ]);
    elements.apiPill.textContent = `Live API: ${apiBaseUrl}`;
    elements.healthChip.innerHTML = buildStatusChip(health.status || "connected", "success");
    elements.feedback.textContent = `${messagePrefix} Health check succeeded for ${apiBaseUrl}.`;
    setSnapshotMode(true);
    elements.snapshotFeedback.textContent =
      "Queue, notice, governance, and observability summaries below are being pulled from the selected live backend target.";
    renderOperationalSnapshot(queues, notices, rules, observability, submissionReadiness);
  } catch (error) {
    elements.apiPill.textContent = `Saved target: ${apiBaseUrl}`;
    elements.healthChip.innerHTML = buildStatusChip("unreachable", "warning");
    elements.feedback.textContent = `${messagePrefix} Health check failed for ${apiBaseUrl}: ${error.message}`;
    setSnapshotMode(false);
    elements.snapshotFeedback.textContent =
      `The selected API target is not reachable right now, so the operational snapshot is showing contract-aligned mock data instead. Last error: ${error.message}`;
    renderOperationalSnapshot(
      supervisorDashboardMock.queues,
      applicantPortalMock.notices,
      governanceCenterMock.rules,
      governanceCenterMock.observability,
      governanceCenterMock.submissionReadiness
    );
  } finally {
    setButtonBusy(elements.apiForm.querySelector("button[type='submit']"), false, "Saving...");
    setButtonBusy(elements.resetButton, false, "Resetting...");
    setRegionBusy(elements.homeOpsMetrics, false);
    setRegionBusy(elements.homeNoticesList, false);
    setRegionBusy(elements.homeGovernanceSummary, false);
  }
}

function setSnapshotMode(isLive) {
  elements.snapshotModePill.textContent = isLive ? "Live snapshot" : "Mock snapshot";
  elements.snapshotModePill.className = `rounded-full border px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] ${
    isLive
      ? "border-emerald-200 bg-emerald-50 text-emerald-800"
      : "border-amber-200 bg-amber-50 text-amber-800"
  }`;
}

function renderOperationalSnapshot(
  queues,
  notices,
  rules,
  observability = governanceCenterMock.observability,
  submissionReadiness = governanceCenterMock.submissionReadiness
) {
  const totalCases = Object.values(queues.counts_by_state || {}).reduce((sum, value) => sum + value, 0);
  const metrics = [
    ["Total active cases", totalCases, "info", appendWorkspacePreviewParam("./supervisor-dashboard/"), "Open supervisor operations"],
    [
      "Overdue decisions",
      queues.overdue_cases || 0,
      (queues.overdue_cases || 0) > 0 ? "danger" : "success",
      appendWorkspacePreviewParam("./supervisor-dashboard/?urgency=OVERDUE"),
      "Review overdue cases",
    ],
    [
      "Due within 48 hours",
      queues.due_within_48h || 0,
      (queues.due_within_48h || 0) > 0 ? "warning" : "success",
      appendWorkspacePreviewParam("./supervisor-dashboard/?urgency=DUE_WITHIN_48H"),
      "Review due-soon cases",
    ],
    [
      "Manual referrals",
      queues.manual_referrals || 0,
      (queues.manual_referrals || 0) > 0 ? "warning" : "success",
      appendWorkspacePreviewParam("./supervisor-dashboard/?state=REFERRED_TO_MANUAL_REVIEW&holder=MISSION_OR_HEAD_OFFICE"),
      "Open manual referrals",
    ],
    [
      "Waiting for documents",
      queues.waiting_for_documents || 0,
      (queues.waiting_for_documents || 0) > 0 ? "warning" : "success",
      appendWorkspacePreviewParam("./supervisor-dashboard/?state=WAITING_FOR_DOCUMENTS&holder=APPLICANT"),
      "Open document queue",
    ],
    [
      "Ready for officer review",
      queues.ready_for_officer_review || 0,
      (queues.ready_for_officer_review || 0) > 0 ? "info" : "warning",
      appendWorkspacePreviewParam("./supervisor-dashboard/?state=READY_FOR_OFFICER_REVIEW&holder=OFFICER"),
      "Open officer queue",
    ],
    [
      "Extension requests",
      queues.extension_requested || 0,
      (queues.extension_requested || 0) > 0 ? "warning" : "success",
      appendWorkspacePreviewParam("./supervisor-dashboard/?state=EXTENSION_REQUESTED&holder=OFFICER"),
      "Open extension review",
    ],
    [
      "Extension appointments",
      queues.extension_appointment_required || 0,
      (queues.extension_appointment_required || 0) > 0 ? "warning" : "success",
      appendWorkspacePreviewParam("./supervisor-dashboard/?state=EXTENSION_APPOINTMENT_REQUIRED&holder=APPLICANT"),
      "Open appointment backlog",
    ],
    [
      "Extension review backlog",
      queues.under_extension_review || 0,
      (queues.under_extension_review || 0) > 0 ? "info" : "success",
      appendWorkspacePreviewParam("./supervisor-dashboard/?state=UNDER_EXTENSION_REVIEW&holder=OFFICER"),
      "Open extension review queue",
    ],
  ];

  elements.homeOpsMetrics.innerHTML = metrics
    .map(
      ([label, value, tone, href, actionLabel]) => `
        <article class="rounded-3xl border border-slate-200/80 bg-white/85 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${label}</span>
              <strong class="mt-3 block text-3xl font-extrabold text-slate-950">${value}</strong>
            </div>
            ${buildStatusChip(label, tone)}
          </div>
          <a class="inline-flex rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5" href="${href}">
            ${actionLabel}
          </a>
        </article>
      `
    )
    .join("");

  elements.homeNoticesList.innerHTML = (notices || []).length
    ? notices
        .map(
          (notice) => `
            <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/85 p-5">
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
        )
        .join("")
    : '<div class="rounded-3xl border border-dashed border-slate-300 bg-white/45 p-5 text-sm leading-7 text-slate-600">No service notices are currently published.</div>';

  const activeVersion = rules.active_policy_version || {};
  const driftSignals = (rules.active_circulars || []).filter(
    (circular) => String(circular.status || "").toUpperCase() !== "ACTIVE"
  );
  const requiredReadinessItems = (submissionReadiness.items || []).filter((item) => item.required);
  const blockingSubmissionItems = requiredReadinessItems.filter((item) => item.status !== "PASS");
  const readinessWarnings = (submissionReadiness.items || []).filter((item) => item.status === "WARNING");
  const governanceCards = [
    ["Workflow pack", activeVersion.workflow_pack || rules.workflow_pack || "Not available"],
    ["Policy version", activeVersion.policy_version || "Not available"],
    ["Rule version", activeVersion.rule_version || "Not available"],
    ["Publication reference", activeVersion.publication_reference || "Not available"],
    ["Phoenix status", observability.status || "DISABLED"],
    ["Observability target", observability.target || "LOCAL_ONLY"],
    ["Phoenix project", observability.project_name || "visaflow-mas"],
    [
      "Submission readiness",
      submissionReadiness.ready_for_submission ? "READY" : submissionReadiness.overall_status || "ACTION_REQUIRED",
    ],
    ["Submission blockers", blockingSubmissionItems.length],
    ["Submission warnings", readinessWarnings.length],
    ["Oldest due date", formatDateTime(queues.oldest_due_at || "")],
    ["Drift signals", driftSignals.length],
    ["Official sources", (rules.official_sources || []).length],
    ["Verified at", formatDateTime(rules.verified_at || "")],
  ];

  elements.homeGovernanceSummary.innerHTML = governanceCards
    .map(
      ([label, value]) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/85 p-5">
          <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${label}</span>
          <strong class="mt-2 block text-base font-extrabold text-slate-900">${value}</strong>
        </article>
      `
    )
    .join("") +
    `
      <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/85 p-5">
        <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">Observability posture</span>
            <h3 class="mt-2 text-lg font-extrabold text-slate-900">${observabilitySnapshotTitle(observability)}</h3>
          </div>
          ${buildStatusChip(
            observability.status || "DISABLED",
            toneForObservabilityStatus(observability.status || "DISABLED")
          )}
        </div>
        <p class="text-sm leading-7 text-slate-600">${observabilitySnapshotMessage(observability)}</p>
      </article>
      <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/85 p-5">
        <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">Submission readiness</span>
            <h3 class="mt-2 text-lg font-extrabold text-slate-900">${submissionReadinessSnapshotTitle(submissionReadiness)}</h3>
          </div>
          ${buildStatusChip(
            submissionReadiness.overall_status || "ACTION_REQUIRED",
            submissionReadiness.ready_for_submission
              ? "success"
              : blockingSubmissionItems.length
                ? "warning"
                : "info"
          )}
        </div>
        <p class="text-sm leading-7 text-slate-600">${submissionReadinessSnapshotMessage(
          submissionReadiness,
          blockingSubmissionItems.length,
          readinessWarnings.length
        )}</p>
      </article>
      <a class="inline-flex rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5" href="${appendWorkspacePreviewParam("./governance-center/")}">
        Open governance center
      </a>
      <a class="inline-flex rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5" href="${appendWorkspacePreviewParam("./governance-center/#demo-showcase-panel")}">
        Open demo showcase
      </a>
      <a class="inline-flex rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5" href="${appendWorkspacePreviewParam("./governance-center/#submission-readiness-panel")}">
        Open submission readiness
      </a>
    `;
}

function observabilitySnapshotTitle(observability) {
  const status = String(observability.status || "DISABLED").toUpperCase();
  switch (status) {
    case "READY":
      return "Phoenix runtime is ready";
    case "DEGRADED":
      return "Phoenix runtime needs attention";
    case "PENDING":
      return "Phoenix runtime is still warming up";
    default:
      return "Phoenix is still disabled";
  }
}

function observabilitySnapshotMessage(observability) {
  const status = String(observability.status || "DISABLED").toUpperCase();
  switch (status) {
    case "READY":
      return `The selected backend is exporting observability data for project ${observability.project_name || "visaflow-mas"} on target ${
        observability.target || "LOCAL_ONLY"
      }.`;
    case "DEGRADED":
      return "The selected backend intends to export traces, but the runtime is degraded. Audit remains the fallback source of truth until Phoenix health is restored.";
    case "PENDING":
      return "The selected backend has observability enabled, but runtime readiness is still pending. Open the governance center to review the rollout checklist.";
    default:
      return "The selected backend is still in local-audit-only mode. Open the governance center for the enablement checklist and redaction guardrails.";
  }
}

function submissionReadinessSnapshotTitle(submissionReadiness) {
  if (submissionReadiness.ready_for_submission) {
    return "Submission package is ready";
  }
  return "Submission package still has blockers";
}

function submissionReadinessSnapshotMessage(submissionReadiness, blockerCount, warningCount) {
  if (submissionReadiness.ready_for_submission) {
    return "The required hackathon packaging checks are currently satisfied from this backend target.";
  }
  return `This backend still reports ${blockerCount} required submission blocker${
    blockerCount === 1 ? "" : "s"
  } and ${warningCount} advisory warning${warningCount === 1 ? "" : "s"}. Open governance to review hosted URL, public repo, demo video, and live-runtime readiness gaps.`;
}

function toneForObservabilityStatus(value) {
  switch (String(value || "").toUpperCase()) {
    case "READY":
      return "success";
    case "DEGRADED":
      return "warning";
    case "PENDING":
      return "info";
    default:
      return "warning";
  }
}

function handleClearRecentCases() {
  localStorage.removeItem("visaFlowRecentCases");
  renderRecentCases();
}

function renderRecentCases() {
  const recentCases = getRecentCases();
  if (!recentCases.length) {
    elements.recentCasesList.innerHTML =
      '<div class="rounded-3xl border border-dashed border-slate-300 bg-white/45 p-5 text-sm leading-7 text-slate-600 md:col-span-2 xl:col-span-3">No recent live cases have been opened yet. Load a real case in the applicant or officer surfaces and it will appear here.</div>';
    return;
  }

  elements.recentCasesList.innerHTML = recentCases
    .map(
      (item) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/85 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${item.case_id}</span>
              <h3 class="mt-2 text-lg font-extrabold text-slate-900">${titleForSurface(item.surface)}</h3>
              <p class="mt-2 text-sm leading-7 text-slate-600">Updated ${formatDateTime(item.updated_at)}</p>
            </div>
            ${buildStatusChip(item.current_state || item.surface)}
          </div>
          <div class="rounded-[1.25rem] border border-slate-200/80 bg-slate-50/80 p-4 text-sm leading-7 text-slate-600">
            <strong class="text-slate-900">Current holder:</strong> ${titleCase(item.current_holder)}<br />
            <strong class="text-slate-900">Next action:</strong> ${titleCase(item.next_action)}
          </div>
          <div class="mt-4 flex flex-wrap gap-3">
            <a class="rounded-full bg-visa-navy px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-slate-900/10 transition hover:-translate-y-0.5" href="${surfaceHref(item.surface, item.case_id)}">
              Resume ${titleForSurface(item.surface)}
            </a>
            <a class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5" href="${appendWorkspacePreviewParam(`./governance-center/?case=${encodeURIComponent(item.case_id)}#self-improvement-panel`)}">
              Governance Review
            </a>
            ${
              isExtensionWorkflowActive(item.extension_state)
                ? `<a class="rounded-full border border-teal-200 bg-teal-50 px-4 py-2 text-sm font-semibold text-teal-900 transition hover:-translate-y-0.5" href="${appendWorkspacePreviewParam(`./officer-dashboard/?case=${encodeURIComponent(item.case_id)}#extension-operations-panel`)}">
                    Officer Extension Ops
                  </a>`
                : ""
            }
            <a class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5" href="${appendWorkspacePreviewParam(`./applicant-portal/?case=${encodeURIComponent(item.case_id)}`)}">
              Applicant View
            </a>
            <a class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5" href="${appendWorkspacePreviewParam(`./officer-dashboard/?case=${encodeURIComponent(item.case_id)}`)}">
              Officer View
            </a>
            <a class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5" href="${supervisorHref(item)}">
              Supervisor Queue
            </a>
          </div>
        </article>
      `
    )
    .join("");
}

function renderGlossary() {
  elements.workflowGlossaryList.innerHTML = workflowGlossary
    .map(
      (item) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/85 p-5">
          <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${item.code}</span>
          <h3 class="mt-2 text-lg font-extrabold text-slate-900">${item.title}</h3>
          <p class="mt-3 text-sm leading-7 text-slate-600">${item.description}</p>
        </article>
      `
    )
    .join("");
}

function surfaceHref(surface, caseId) {
  const encoded = encodeURIComponent(caseId);
  if (surface === "officer") {
    return appendWorkspacePreviewParam(`./officer-dashboard/?case=${encoded}`);
  }
  return appendWorkspacePreviewParam(`./applicant-portal/?case=${encoded}`);
}

function supervisorHref(item) {
  const params = new URLSearchParams();
  params.set("case", item.case_id);
  if (item.current_state) {
    params.set("state", item.current_state);
  }
  if (item.current_holder) {
    params.set("holder", item.current_holder);
  }
  return appendWorkspacePreviewParam(`./supervisor-dashboard/?${params.toString()}`);
}

function titleForSurface(surface) {
  return surface === "officer" ? "Officer Dashboard" : "Applicant Portal";
}

initialize();
