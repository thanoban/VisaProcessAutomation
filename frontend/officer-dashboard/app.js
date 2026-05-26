import {
  buildStatusChip,
  createApiClient,
  formatDate,
  formatDateTime,
  getStoredApiBaseUrl,
  linkListMarkup,
  linkMarkup,
  listMarkup,
  officerDashboardMock,
  rememberRecentCase,
  setButtonBusy,
  setRegionBusy,
  titleCase,
} from "../shared/app.js";

const elements = {
  apiPill: document.querySelector("#dashboard-api-pill"),
  heroCopy: document.querySelector("#dashboard-hero-copy"),
  lookupForm: document.querySelector("#dashboard-lookup-form"),
  sampleButton: document.querySelector("#dashboard-sample-button"),
  feedback: document.querySelector("#dashboard-feedback"),
  results: document.querySelector("#dashboard-results"),
  empty: document.querySelector("#dashboard-empty"),
  recommendationValue: document.querySelector("#recommendation-value"),
  holderValue: document.querySelector("#dashboard-holder-value"),
  actionValue: document.querySelector("#dashboard-action-value"),
  applicantSummary: document.querySelector("#applicant-summary"),
  briefDefinitionGrid: document.querySelector("#brief-definition-grid"),
  confidenceChip: document.querySelector("#confidence-chip"),
  recommendationPanelGrid: document.querySelector("#recommendation-panel-grid"),
  workspaceLinks: document.querySelector("#dashboard-workspace-links"),
  routeHandlingPanel: document.querySelector("#route-handling-panel"),
  agentResultsList: document.querySelector("#agent-results-list"),
  evidenceList: document.querySelector("#evidence-list"),
  policyList: document.querySelector("#policy-list"),
  questionList: document.querySelector("#question-list"),
  auditList: document.querySelector("#audit-list"),
  decisionOutcomePanel: document.querySelector("#decision-outcome-panel"),
  decisionForm: document.querySelector("#decision-form"),
  decisionChoice: document.querySelector("#decision-choice"),
  decisionGuidance: document.querySelector("#decision-guidance"),
  overrideReason: document.querySelector("#decision-override"),
  decisionFeedback: document.querySelector("#decision-feedback"),
  caseIdInput: document.querySelector("#dashboard-case-id"),
  lookupSubmitButton: document.querySelector("#dashboard-lookup-form button[type='submit']"),
  decisionSubmitButton: document.querySelector("#decision-form button[type='submit']"),
};

const state = {
  apiBaseUrl: getStoredApiBaseUrl(),
  apiAvailable: false,
  currentCaseId: new URLSearchParams(window.location.search).get("case")?.trim() || officerDashboardMock.casePacket.case_id,
  currentRecommendation: officerDashboardMock.officerBrief.recommendation,
};

const api = createApiClient(state.apiBaseUrl);

async function initialize() {
  elements.caseIdInput.value = state.currentCaseId;
  wireEvents();
  await loadDashboardChrome();
  renderDashboard(officerDashboardMock.casePacket, officerDashboardMock.officerBrief, true);
  if (state.apiAvailable && state.currentCaseId) {
    await loadAndRenderCase(state.currentCaseId);
  }
}

function wireEvents() {
  elements.lookupForm.addEventListener("submit", handleLookup);
  elements.sampleButton.addEventListener("click", () => {
    state.currentCaseId = officerDashboardMock.casePacket.case_id;
    elements.caseIdInput.value = state.currentCaseId;
    syncCaseQueryParam(state.currentCaseId);
    renderDashboard(officerDashboardMock.casePacket, officerDashboardMock.officerBrief, true);
  });
  elements.decisionForm.addEventListener("submit", handleDecisionSubmit);
  elements.decisionChoice.addEventListener("change", syncDecisionGuidance);
}

async function loadDashboardChrome() {
  try {
    await api.getHealth();
    state.apiAvailable = true;
    elements.apiPill.textContent = `Live API: ${api.baseUrl}`;
    elements.heroCopy.textContent =
      "Live API connected. Officers can process a case, review the brief, and submit a decision from this dashboard.";
  } catch {
    state.apiAvailable = false;
    elements.apiPill.textContent = "Mock preview mode";
    elements.heroCopy.textContent =
      "The backend is not currently reachable, so the dashboard is showing a contract-aligned officer review preview.";
  }
}

async function handleLookup(event) {
  event.preventDefault();
  const caseId = elements.caseIdInput.value.trim();
  if (!caseId) {
    return;
  }

  await loadAndRenderCase(caseId);
}

async function loadAndRenderCase(caseId) {
  state.currentCaseId = caseId;
  elements.feedback.textContent = "Loading case packet and officer brief...";
  elements.empty.hidden = false;
  elements.empty.textContent = `Loading officer review data for ${caseId}...`;
  setButtonBusy(elements.lookupSubmitButton, true, "Loading brief...");
  setRegionBusy(elements.results, true);

  try {
    if (!state.apiAvailable) {
      renderDashboard(officerDashboardMock.casePacket, officerDashboardMock.officerBrief, true);
      elements.feedback.textContent = "Mock mode is active. Showing the sample officer review case.";
      return;
    }

    const { casePacket, officerBrief } = await loadOfficerReviewCase(caseId);
    renderDashboard(casePacket, officerBrief, false);
    elements.feedback.textContent = `Officer brief loaded for ${caseId}.`;
  } catch (error) {
    elements.empty.hidden = false;
    elements.results.hidden = true;
    elements.empty.textContent = `Unable to load officer review data for ${caseId}: ${error.message}`;
    elements.feedback.textContent = "Officer brief load failed.";
  } finally {
    setButtonBusy(elements.lookupSubmitButton, false, "Loading brief...");
    setRegionBusy(elements.results, false);
  }
}

function renderDashboard(casePacket, brief, useMock) {
  state.currentRecommendation = brief.recommendation;
  elements.results.hidden = false;
  elements.empty.hidden = true;
  elements.recommendationValue.innerHTML = buildStatusChip(brief.recommendation);
  elements.holderValue.textContent = titleCase(brief.recommendation_panel.current_holder || casePacket.workflow.current_holder);
  elements.actionValue.textContent = titleCase(
    brief.recommendation_panel.action_required_from || casePacket.workflow.action_required_from
  );
  elements.workspaceLinks.innerHTML = buildWorkspaceLinks(casePacket.case_id, "officer");

  if (!useMock) {
    state.currentCaseId = casePacket.case_id;
    syncCaseQueryParam(casePacket.case_id);
    rememberRecentCase({
      case_id: casePacket.case_id,
      surface: "officer",
      current_state: casePacket.workflow.current_state,
      current_holder: casePacket.workflow.current_holder,
      next_action: casePacket.workflow.next_action,
    });
  }

  elements.applicantSummary.textContent = brief.applicant_summary;
  elements.confidenceChip.innerHTML = buildStatusChip(`confidence ${Math.round((brief.confidence || 0) * 100)}%`, "info");

  const detailItems = [
    ["Case ID", casePacket.case_id],
    ["Visa class", brief.visa_class],
    ["Arrival date", formatDate(casePacket.visa_application.arrival_date)],
    ["Departure date", formatDate(casePacket.visa_application.departure_date)],
    ["ETA status", buildStatusChip(casePacket.workflow.eta_status)],
    ["Port clearance", buildStatusChip(casePacket.workflow.port_clearance_state)],
    ["Policy version", casePacket.policy_context.policy_version],
    ["Rule version", casePacket.policy_context.effective_rule_version],
  ];

  elements.briefDefinitionGrid.innerHTML = detailItems
    .map(
      ([label, value]) => `
        <div class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-4">
          <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${label}</span>
          <strong class="mt-2 block text-base font-extrabold text-slate-900">${value || "Not available"}</strong>
        </div>
      `
    )
    .join("");

  const panelItems = [
    ["Recommended route", buildStatusChip(brief.recommendation_panel.recommendation || brief.recommendation)],
    ["Next action", titleCase(brief.recommendation_panel.next_action || casePacket.workflow.next_action)],
    ["Human decision required", brief.recommendation_panel.human_decision_required ? "Yes" : "No"],
  ];

  elements.recommendationPanelGrid.innerHTML = panelItems
    .map(
      ([label, value]) => `
        <div class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-4">
          <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${label}</span>
          <strong class="mt-2 block text-base font-extrabold text-slate-900">${value}</strong>
        </div>
      `
    )
    .join("");

  const appointments = casePacket.workflow.appointments || [];
  const routeHandlingCards = [
    `
      <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
        <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">Current operating route</span>
            <h3 class="mt-2 text-lg font-extrabold text-slate-900">${
              casePacket.workflow.manual_referral_reason ? "Manual or exception route" : "Straight-through officer route"
            }</h3>
          </div>
          ${
            casePacket.workflow.manual_referral_reason
              ? buildStatusChip("manual referral active", "warning")
              : buildStatusChip("standard route", "success")
          }
        </div>
        <p class="text-sm leading-7 text-slate-600">${
          casePacket.workflow.manual_referral_reason ||
          "No sponsor, nationality, or exception-driven manual referral is currently attached to this case."
        }</p>
      </article>
    `,
    `
      <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
        <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">Extension and travel handling</span>
            <h3 class="mt-2 text-lg font-extrabold text-slate-900">${titleCase(casePacket.workflow.extension_state || "NOT_REQUESTED")}</h3>
          </div>
          ${buildStatusChip(casePacket.workflow.extension_state || "NOT_REQUESTED")}
        </div>
        <p class="text-sm leading-7 text-slate-600">
          <strong class="text-slate-900">Port clearance:</strong> ${titleCase(casePacket.workflow.port_clearance_state || "NOT_STARTED")}<br />
          <strong class="text-slate-900">Next action:</strong> ${titleCase(casePacket.workflow.next_action || "Not available")}
        </p>
      </article>
    `,
    ...appointments.map(
      (appointment) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${appointment.appointment_id || "Service appointment"}</span>
              <h3 class="mt-2 text-lg font-extrabold text-slate-900">${titleCase(appointment.appointment_type || "Appointment")}</h3>
            </div>
            ${buildStatusChip(appointment.status || "PENDING")}
          </div>
          <p class="text-sm leading-7 text-slate-600">
            <strong class="text-slate-900">Location:</strong> ${appointment.location || "Not assigned yet"}<br />
            <strong class="text-slate-900">Scheduled for:</strong> ${formatDateTime(appointment.scheduled_for)}<br />
            ${appointment.instructions || "No additional instructions are attached to this appointment yet."}
          </p>
        </article>
      `
    ),
  ];
  elements.routeHandlingPanel.innerHTML = routeHandlingCards.join("");

  elements.agentResultsList.innerHTML = listMarkup(
    (brief.agent_results || []).map(
      (result) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${result.agent_name}</span>
              <h3 class="mt-2 text-lg font-extrabold text-slate-900">${titleCase(result.status)}</h3>
            </div>
            ${buildStatusChip(result.risk_level || result.status)}
          </div>
          <p class="text-sm leading-7 text-slate-600">${result.summary}</p>
        </article>
      `
    ),
    "No agent results are available yet for this case."
  );

  const evidence = brief.evidence_viewer || {};
  const evidenceItems = [
    ["Passport fields", objectPairsMarkup(evidence.passport_fields)],
    ["Bank statement metrics", objectPairsMarkup(evidence.bank_statement_metrics)],
    ["Itinerary evidence", arrayMarkup(evidence.itinerary_evidence)],
    ["Rule version used", evidence.rule_version_used || "Not available"],
    ["Publication reference", evidence.publication_reference || "Not available"],
    ["Policy source", linkMarkup(evidence.policy_source_uri || "Not available")],
    ["Official sources", linkListMarkup(evidence.official_sources)],
    ["Verified at", formatDateTime(evidence.verified_at)],
  ];

  elements.evidenceList.innerHTML = evidenceItems
    .map(
      ([label, value]) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${label}</span>
          <div class="mt-3 text-sm leading-7 text-slate-600">${value}</div>
        </article>
      `
    )
    .join("");

  elements.policyList.innerHTML = listMarkup(
    (brief.policy_references || []).map(
      (reference) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${reference.policy_id}</span>
              <h3 class="mt-2 text-lg font-extrabold text-slate-900">${reference.requirement}</h3>
            </div>
            ${buildStatusChip(reference.status)}
          </div>
        </article>
      `
    ),
    "No policy references are available yet for this case."
  );

  elements.questionList.innerHTML = listMarkup(
    [
      ...(brief.risk_flags || []).map(
        (flag) => `<div class="rounded-[1.25rem] border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900">${flag}</div>`
      ),
      ...(brief.missing_items || []).map(
        (item) => `<div class="rounded-[1.25rem] border border-rose-200 bg-rose-50 p-4 text-sm leading-6 text-rose-900">Missing item: ${item}</div>`
      ),
      ...(brief.questions_for_officer || []).map(
        (question) => `<div class="rounded-[1.25rem] border border-slate-200/80 bg-white/80 p-4 text-sm leading-6 text-slate-700">${question}</div>`
      ),
    ],
    "No questions or blocking items are currently attached to this case."
  );

  elements.auditList.innerHTML = listMarkup(
    (brief.audit_timeline || []).map(
      (entry) => `
        <article class="relative mb-4 rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5 last:mb-0">
          <span class="absolute -left-[1.85rem] top-6 h-3 w-3 rounded-full bg-teal-600 ring-8 ring-teal-100"></span>
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${formatDateTime(entry.timestamp)}</span>
              <h3 class="mt-2 text-lg font-extrabold text-slate-900">${titleCase(entry.event_type)}</h3>
            </div>
            ${buildStatusChip(entry.actor_type || "SYSTEM")}
          </div>
          <p class="text-sm leading-7 text-slate-600">
            Actor: ${entry.actor_id || "Unknown"}${entry.recommendation ? ` | Recommendation: ${titleCase(entry.recommendation)}` : ""}${
              entry.human_action ? ` | Human action: ${titleCase(entry.human_action)}` : ""
            }
          </p>
        </article>
      `
    ),
    "No audit events have been recorded yet."
  );

  elements.decisionOutcomePanel.innerHTML = buildDecisionOutcomeMarkup(casePacket);

  elements.decisionFeedback.textContent = useMock
    ? "Decision submission is disabled in mock mode and becomes live when the API is reachable."
    : `Ready to submit an officer action for ${casePacket.case_id}.`;
  syncDecisionGuidance();
}

async function handleDecisionSubmit(event) {
  event.preventDefault();
  const formData = new FormData(elements.decisionForm);
  const payload = {
    decision: formData.get("decision"),
    officer_id: formData.get("officerId"),
    reason: formData.get("reason"),
    override_reason: formData.get("overrideReason") || "",
  };

  if (!state.apiAvailable) {
    elements.decisionFeedback.textContent =
      "Mock mode is active. Start the backend to submit a real officer decision.";
    return;
  }

  try {
    elements.decisionFeedback.textContent = "Submitting officer decision...";
    setButtonBusy(elements.decisionSubmitButton, true, "Submitting decision...");
    setRegionBusy(elements.results, true);
    const result = await api.submitOfficerDecision(state.currentCaseId, payload);
    const { casePacket, officerBrief } = await loadOfficerReviewCase(state.currentCaseId, false);
    renderDashboard(casePacket, officerBrief, false);
    elements.decisionFeedback.textContent = `Decision recorded with status: ${result.status}. The dashboard has been refreshed with the latest case state and audit trail.`;
  } catch (error) {
    elements.decisionFeedback.textContent = `Decision submission failed: ${error.message}`;
  } finally {
    setButtonBusy(elements.decisionSubmitButton, false, "Submitting decision...");
    setRegionBusy(elements.results, false);
  }
}

async function loadOfficerReviewCase(caseId, processIfMissingBrief = true) {
  const casePacket = await api.getCase(caseId);
  let officerBrief;

  try {
    officerBrief = await api.getOfficerBrief(caseId);
  } catch (error) {
    if (!processIfMissingBrief) {
      throw error;
    }
    await api.processCase(caseId);
    officerBrief = await api.getOfficerBrief(caseId);
  }

  const auditTimeline = await api.getAudit(caseId);
  return {
    casePacket,
    officerBrief: mergeBriefWithCurrentCase(officerBrief, casePacket, auditTimeline),
  };
}

function mergeBriefWithCurrentCase(brief, casePacket, auditTimeline) {
  return {
    ...brief,
    recommendation_panel: {
      ...(brief.recommendation_panel || {}),
      current_holder: casePacket.workflow.current_holder,
      action_required_from: casePacket.workflow.action_required_from,
      next_action: casePacket.workflow.next_action,
      human_decision_required: true,
    },
    audit_timeline: auditTimeline,
  };
}

function syncDecisionGuidance() {
  const selectedDecision = elements.decisionChoice.value;
  const requiresOverride = overrideReasonRequired(state.currentRecommendation, selectedDecision);
  elements.overrideReason.required = requiresOverride;

  if (!state.currentRecommendation) {
    elements.decisionGuidance.textContent =
      "The override requirement will update once a recommendation is loaded for this case.";
    return;
  }

  if (requiresOverride) {
    elements.decisionGuidance.textContent =
      `The current recommendation is ${titleCase(state.currentRecommendation)}. Because ${titleCase(selectedDecision)} differs from that route, an override reason is required before submission.`;
    return;
  }

  elements.decisionGuidance.textContent =
    `The current recommendation is ${titleCase(state.currentRecommendation)}. ${titleCase(selectedDecision)} can be submitted without an override reason for this case.`;
}

function overrideReasonRequired(recommendation, decision) {
  const allowedDecisions = {
    APPROVE_READY: new Set(["APPROVE"]),
    REQUEST_MORE_INFO: new Set(["REQUEST_MORE_INFO"]),
    REFUSAL_DRAFT_READY: new Set(["REJECT"]),
    ENHANCED_REVIEW: new Set(["APPROVE", "REJECT", "REQUEST_MORE_INFO", "ESCALATE"]),
  };
  const normalizedRecommendation = String(recommendation || "").toUpperCase();
  const normalizedDecision = String(decision || "").toUpperCase();
  if (!allowedDecisions[normalizedRecommendation]) {
    return false;
  }
  return !allowedDecisions[normalizedRecommendation].has(normalizedDecision);
}

function buildDecisionOutcomeMarkup(casePacket) {
  const workflow = casePacket.workflow || {};
  const decisionNotice = workflow.decision_notice;
  const portEvents = workflow.port_clearance_events || [];
  const outcomeCards = [
    `
      <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
        <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">Current workflow state</span>
            <h3 class="mt-2 text-lg font-extrabold text-slate-900">${titleCase(workflow.current_state || "UNKNOWN")}</h3>
          </div>
          <div class="flex flex-wrap gap-2">
            ${buildStatusChip(workflow.current_holder || "SYSTEM")}
            ${casePacket.override_required ? buildStatusChip("override required", "warning") : buildStatusChip("no override", "success")}
          </div>
        </div>
        <p class="text-sm leading-7 text-slate-600">
          <strong class="text-slate-900">Next action:</strong> ${titleCase(workflow.next_action || "Not available")}<br />
          <strong class="text-slate-900">Action required from:</strong> ${titleCase(workflow.action_required_from || "SYSTEM")}
        </p>
      </article>
    `,
  ];

  if (decisionNotice) {
    outcomeCards.push(`
      <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
        <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${decisionNotice.subject || "Decision notice"}</span>
        <p class="mt-3 text-sm leading-7 text-slate-600">${decisionNotice.summary || "No decision summary is available yet."}</p>
        <div class="mt-4 grid gap-2">
          ${(decisionNotice.next_steps || [])
            .map(
              (step) => `<div class="rounded-[1.25rem] border border-slate-200/80 bg-slate-50/80 p-4 text-sm leading-6 text-slate-700">${step}</div>`
            )
            .join("")}
        </div>
      </article>
    `);
  }

  if (portEvents.length) {
    outcomeCards.push(`
      <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
        <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">Port-of-entry follow-up</span>
        <div class="mt-4 grid gap-3">
          ${portEvents
            .map(
              (event) => `
                <div class="rounded-[1.25rem] border border-slate-200/80 bg-slate-50/80 p-4 text-sm leading-6 text-slate-700">
                  <strong class="text-slate-900">${titleCase(event.event_type)}</strong><br />
                  Status: ${titleCase(event.status)}<br />
                  Recorded: ${formatDateTime(event.timestamp)}<br />
                  ${event.notes || ""}
                </div>
              `
            )
            .join("")}
        </div>
      </article>
    `);
  }

  if (!decisionNotice && !portEvents.length) {
    outcomeCards.push(`
      <div class="rounded-[1.5rem] border border-dashed border-slate-300 bg-white/45 p-5 text-sm leading-7 text-slate-600">
        No final decision outcome has been recorded for this case yet. Once an officer action is submitted, the dashboard will show the decision notice and any port-of-entry follow-up requirements here.
      </div>
    `);
  }

  return outcomeCards.join("");
}

function objectPairsMarkup(value) {
  const entries = Object.entries(value || {});
  if (!entries.length) {
    return "Not available";
  }
  return entries
    .map(
      ([key, itemValue]) => `
        <div class="flex items-start justify-between gap-4 border-b border-slate-100 py-2 last:border-b-0">
          <span class="font-semibold text-slate-700">${titleCase(key)}</span>
          <span class="text-right">${Array.isArray(itemValue) ? arrayMarkup(itemValue) : itemValue}</span>
        </div>
      `
    )
    .join("");
}

function arrayMarkup(items) {
  if (!items || !items.length) {
    return "None";
  }
  return items.map((item) => `<span class="mr-2 inline-block rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">${item}</span>`).join("");
}

function syncCaseQueryParam(caseId) {
  const params = new URLSearchParams(window.location.search);
  if (caseId) {
    params.set("case", caseId);
  } else {
    params.delete("case");
  }
  const nextQuery = params.toString();
  const nextUrl = `${window.location.pathname}${nextQuery ? `?${nextQuery}` : ""}`;
  window.history.replaceState({}, "", nextUrl);
}

function buildWorkspaceLinks(caseId, currentSurface) {
  const links = [
    ["Applicant Portal", "../applicant-portal/", "applicant"],
    ["Officer Dashboard", "../officer-dashboard/", "officer"],
    ["Supervisor Dashboard", "../supervisor-dashboard/", "supervisor"],
    ["Governance Center", "../governance-center/", "governance"],
  ];
  return links
    .map(([label, href, surface]) => {
      const activeClasses =
        surface === currentSurface
          ? "bg-visa-navy text-white shadow-lg shadow-slate-900/10"
          : "border border-slate-200 bg-white text-slate-700";
      const target =
        surface === "governance" ? href : `${href}?case=${encodeURIComponent(caseId)}`;
      return `<a class="rounded-full px-4 py-2 text-sm font-semibold transition hover:-translate-y-0.5 ${activeClasses}" href="${target}">${label}</a>`;
    })
    .join("");
}

initialize();
