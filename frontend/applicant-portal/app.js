import {
  applicantPortalMock,
  buildStatusChip,
  createApiClient,
  formatDate,
  formatDateTime,
  getStoredApiBaseUrl,
  isMissingFileUploadSupport,
  linkListMarkup,
  linkMarkup,
  listMarkup,
  rememberRecentCase,
  setButtonBusy,
  setRegionBusy,
  startCaseId,
  titleCase,
  workflowGlossary,
} from "../shared/app.js";

const elements = {
  apiModePill: document.querySelector("#api-mode-pill"),
  heroNoticeCopy: document.querySelector("#hero-notice-copy"),
  applicationForm: document.querySelector("#application-form"),
  statusForm: document.querySelector("#status-form"),
  documentResponseForm: document.querySelector("#document-response-form"),
  formFeedback: document.querySelector("#form-feedback"),
  documentResponseFeedback: document.querySelector("#document-response-feedback"),
  caseIdInput: document.querySelector("#case-id"),
  lookupCaseIdInput: document.querySelector("#lookup-case-id"),
  documentResponseCaseIdInput: document.querySelector("#document-response-case-id"),
  loadSampleButton: document.querySelector("#load-sample-button"),
  useSampleStatusButton: document.querySelector("#use-sample-status-button"),
  checklistList: document.querySelector("#checklist-list"),
  checklistNotes: document.querySelector("#checklist-notes"),
  noticeList: document.querySelector("#notice-list"),
  workflowGlossaryList: document.querySelector("#workflow-glossary-list"),
  statusResults: document.querySelector("#status-results"),
  statusEmpty: document.querySelector("#status-empty"),
  stateValue: document.querySelector("#state-value"),
  holderValue: document.querySelector("#holder-value"),
  nextActionValue: document.querySelector("#next-action-value"),
  statusDefinitionGrid: document.querySelector("#status-definition-grid"),
  latestMessagePanel: document.querySelector("#latest-message-panel"),
  requiredActionsPanel: document.querySelector("#required-actions-panel"),
  specialHandlingPanel: document.querySelector("#special-handling-panel"),
  caseServiceNoticesPanel: document.querySelector("#case-service-notices-panel"),
  travelFollowUpPanel: document.querySelector("#travel-follow-up-panel"),
  workspaceLinksPanel: document.querySelector("#workspace-links-panel"),
  documentSummaryList: document.querySelector("#document-summary-list"),
  timelineList: document.querySelector("#timeline-list"),
  applicationSubmitButton: document.querySelector("#application-form button[type='submit']"),
  statusSubmitButton: document.querySelector("#status-form button[type='submit']"),
  documentResponseSubmitButton: document.querySelector("#document-response-form button[type='submit']"),
};

const state = {
  apiBaseUrl: getStoredApiBaseUrl(),
  apiAvailable: false,
  linkedCaseId: new URLSearchParams(window.location.search).get("case")?.trim() || "",
};

const api = createApiClient(state.apiBaseUrl);

async function initialize() {
  elements.caseIdInput.value = startCaseId();
  elements.lookupCaseIdInput.value = state.linkedCaseId || applicantPortalMock.casePacket.case_id;
  wireEvents();
  await Promise.all([loadOperationalChrome(), renderSampleCasePreview()]);
  if (state.linkedCaseId && state.apiAvailable) {
    await loadCaseStatus(state.linkedCaseId);
  }
}

function wireEvents() {
  elements.applicationForm.addEventListener("submit", handleApplicationSubmit);
  elements.statusForm.addEventListener("submit", handleStatusLookup);
  elements.documentResponseForm.addEventListener("submit", handleDocumentResponseSubmit);
  elements.loadSampleButton.addEventListener("click", loadSampleIntoForm);
  elements.useSampleStatusButton.addEventListener("click", () => {
    renderCaseStatus(applicantPortalMock.casePacket, {
      latestStatus: buildMockStatus(applicantPortalMock.casePacket),
      useMock: true,
    });
  });
}

async function loadOperationalChrome() {
  try {
    await api.getHealth();
    state.apiAvailable = true;
    elements.apiModePill.textContent = `Live API: ${api.baseUrl}`;

    const [checklist, notices] = await Promise.all([api.getChecklist(), api.getSystemNotices()]);
    renderChecklist(checklist);
    renderNotices(notices);
    elements.heroNoticeCopy.textContent =
      notices[0]?.message || "Live API connected. This portal is ready to surface operational guidance.";
  } catch (error) {
    state.apiAvailable = false;
    elements.apiModePill.textContent = "Mock preview mode";
    elements.heroNoticeCopy.textContent =
      "The backend is not currently reachable, so the portal is showing a realistic preview with contract-aligned mock data.";
    elements.formFeedback.textContent =
      "Mock mode is active. Start the FastAPI backend to submit or fetch real case data.";
    renderChecklist(applicantPortalMock.checklist);
    renderNotices(applicantPortalMock.notices);
  }
  renderGlossary();
}

function renderChecklist(payload) {
  const items = (payload.checklist || []).map(
    (item) => `
      <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
        <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${item.code}</span>
            <h3 class="mt-2 text-lg font-extrabold text-slate-900">${item.title}</h3>
          </div>
          ${buildStatusChip(item.required ? "required" : "optional", item.required ? "warning" : "info")}
        </div>
        <p class="text-sm leading-7 text-slate-600">${item.description}</p>
        <p class="mt-3 text-sm text-slate-500">${item.guidance || "No additional guidance supplied yet."}</p>
      </article>
    `
  );

  elements.checklistList.innerHTML = listMarkup(items, "Checklist guidance has not been loaded yet.");
  elements.checklistNotes.innerHTML = listMarkup(
    [
      ...(payload.verified_at
        ? [
            `<div class="rounded-[1.25rem] border border-teal-200 bg-teal-50 p-4 text-sm leading-6 text-teal-900">Verified against the current Sri Lanka reference pack on ${formatDate(payload.verified_at)}.</div>`,
          ]
        : []),
      ...((payload.official_sources || []).length
        ? [
            `<div class="rounded-[1.25rem] border border-slate-200/80 bg-white/75 p-4 text-sm leading-6 text-slate-600"><strong class="text-slate-900">Official sources:</strong><div class="mt-3">${linkListMarkup(payload.official_sources)}</div></div>`,
          ]
        : []),
      ...(payload.notes || []).map(
        (note) => `<div class="rounded-[1.25rem] border border-slate-200/80 bg-white/75 p-4 text-sm leading-6 text-slate-600">${note}</div>`
      ),
    ],
    ""
  );
}

function renderNotices(notices) {
  const items = (notices || []).map(
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
  );

  elements.noticeList.innerHTML = listMarkup(items, "No current notices have been published.");
}

function renderGlossary() {
  elements.workflowGlossaryList.innerHTML = workflowGlossary
    .map(
      (item) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${item.code}</span>
          <h3 class="mt-2 text-lg font-extrabold text-slate-900">${item.title}</h3>
          <p class="mt-3 text-sm leading-7 text-slate-600">${item.description}</p>
        </article>
      `
    )
    .join("");
}

function loadSampleIntoForm() {
  const sample = applicantPortalMock.casePacket;
  const form = elements.applicationForm;
  form.caseId.value = sample.case_id;
  form.fullName.value = sample.applicant.full_name;
  form.dateOfBirth.value = sample.applicant.date_of_birth;
  form.nationality.value = sample.applicant.nationality;
  form.passportNumber.value = sample.applicant.passport_number;
  form.contactEmail.value = sample.applicant.contact_email;
  form.phone.value = sample.applicant.phone || "";
  form.countryOfApplication.value = sample.visa_application.country_of_application;
  form.purposeOfTravel.value = sample.visa_application.purpose_of_travel;
  form.arrivalDate.value = sample.visa_application.arrival_date;
  form.departureDate.value = sample.visa_application.departure_date;
  form.destinationAddress.value = sample.visa_application.destination_address || "";
  form.sponsor.value = sample.visa_application.sponsor || "";
  form.decisionDueAt.value = "2026-06-03T17:00";
  form.paymentStatus.value = sample.visa_application.payment_status;
  form.passportDocumentUri.value =
    sample.documents.find((document) => document.document_type === "PASSPORT")?.file_uri || "";
  form.bankDocumentUri.value =
    sample.documents.find((document) => document.document_type === "BANK_STATEMENT")?.file_uri || "";
  form.flightDocumentUri.value =
    sample.documents.find((document) => document.document_type === "FLIGHT_ITINERARY")?.file_uri || "";
  form.accommodationDocumentUri.value =
    sample.documents.find((document) => document.document_type === "HOTEL_BOOKING_OR_INVITATION")?.file_uri || "";
  elements.formFeedback.textContent = "Sample application data loaded into the intake form.";
}

async function handleApplicationSubmit(event) {
  event.preventDefault();

  const payload = buildApplicationPayload(new FormData(elements.applicationForm));
  elements.formFeedback.textContent = "Submitting application payload...";
  setButtonBusy(elements.applicationSubmitButton, true, "Creating application...");
  setRegionBusy(elements.statusResults, true);

  try {
    if (!state.apiAvailable) {
      renderCaseStatus(applicantPortalMock.casePacket, {
        latestStatus: buildMockStatus(applicantPortalMock.casePacket),
        useMock: true,
      });
      elements.formFeedback.textContent =
        "Mock mode is active, so the sample case preview was refreshed instead of submitting to the API.";
      return;
    }

    const createdCase = await api.createApplication(payload);
    const fileUploadWarnings = await uploadSelectedFiles(createdCase.case_id, elements.applicationForm, "", {
      hasUriFallback: payload.documents.length > 0,
    });
    await api.processCase(createdCase.case_id);

    const [processedCase, caseStatus] = await Promise.all([
      api.getCase(createdCase.case_id),
      api.getCaseStatus(createdCase.case_id),
    ]);

    state.linkedCaseId = createdCase.case_id;
    elements.lookupCaseIdInput.value = createdCase.case_id;
    renderCaseStatus(processedCase, {
      latestStatus: caseStatus,
      useMock: false,
    });
    elements.formFeedback.textContent = fileUploadWarnings.length
      ? `Application ${createdCase.case_id} was created with URI-backed documents. ${fileUploadWarnings.join(" ")}`
      : `Application ${createdCase.case_id} created and entered the Sri Lanka processing workflow.`;
  } catch (error) {
    elements.formFeedback.textContent = `Submission failed: ${error.message}`;
  } finally {
    setButtonBusy(elements.applicationSubmitButton, false, "Creating application...");
    setRegionBusy(elements.statusResults, false);
  }
}

async function handleStatusLookup(event) {
  event.preventDefault();
  const caseId = elements.lookupCaseIdInput.value.trim();
  if (!caseId) {
    return;
  }

  await loadCaseStatus(caseId);
}

async function loadCaseStatus(caseId) {
  elements.statusEmpty.hidden = false;
  elements.statusEmpty.textContent = `Loading case ${caseId}...`;
  setButtonBusy(elements.statusSubmitButton, true, "Loading status...");
  setRegionBusy(elements.statusResults, true);

  try {
    if (!state.apiAvailable) {
      renderCaseStatus(applicantPortalMock.casePacket, {
        latestStatus: buildMockStatus(applicantPortalMock.casePacket),
        useMock: true,
      });
      elements.statusEmpty.textContent =
        "Mock mode is active. Start the backend to replace the sample case with the requested live case.";
      return;
    }

    const [casePacket, caseStatus] = await Promise.all([api.getCase(caseId), api.getCaseStatus(caseId)]);
    renderCaseStatus(casePacket, {
      latestStatus: caseStatus,
      useMock: false,
    });
  } catch (error) {
    elements.statusEmpty.hidden = false;
    elements.statusResults.hidden = true;
    elements.statusEmpty.textContent = `Unable to load case ${caseId}: ${error.message}`;
  } finally {
    setButtonBusy(elements.statusSubmitButton, false, "Loading status...");
    setRegionBusy(elements.statusResults, false);
  }
}

async function handleDocumentResponseSubmit(event) {
  event.preventDefault();
  const formData = new FormData(elements.documentResponseForm);
  const caseId = String(formData.get("documentResponseCaseId") || "").trim();
  const documents = buildDocumentsPayload(formData, "documentResponse");
  const selectedFiles = collectSelectedFiles(elements.documentResponseForm, "documentResponse");

  if (!caseId) {
    elements.documentResponseFeedback.textContent = "Enter a case ID before submitting document updates.";
    return;
  }

  if (!documents.length && !selectedFiles.length) {
    elements.documentResponseFeedback.textContent = "Provide at least one document file or URI to continue.";
    return;
  }

  try {
    if (!state.apiAvailable) {
      elements.documentResponseFeedback.textContent =
        "Mock mode is active. Start the backend to submit a real document response.";
      return;
    }

    elements.documentResponseFeedback.textContent = "Submitting document response and triggering re-check...";
    setButtonBusy(elements.documentResponseSubmitButton, true, "Submitting response...");
    setRegionBusy(elements.statusResults, true);
    if (documents.length) {
      await api.uploadDocuments(caseId, { documents });
    }
    const fileUploadWarnings = await uploadSelectedFiles(caseId, elements.documentResponseForm, "documentResponse", {
      hasUriFallback: documents.length > 0,
    });
    await api.processCase(caseId);
    const [casePacket, caseStatus] = await Promise.all([api.getCase(caseId), api.getCaseStatus(caseId)]);
    renderCaseStatus(casePacket, {
      latestStatus: caseStatus,
      useMock: false,
    });
    state.linkedCaseId = caseId;
    elements.lookupCaseIdInput.value = caseId;
    elements.documentResponseFeedback.textContent = fileUploadWarnings.length
      ? `Document response accepted with URI-backed fallback. ${fileUploadWarnings.join(" ")}`
      : "Document response accepted. The case has been sent back through the Sri Lanka review workflow.";
  } catch (error) {
    elements.documentResponseFeedback.textContent = `Document response failed: ${error.message}`;
  } finally {
    setButtonBusy(elements.documentResponseSubmitButton, false, "Submitting response...");
    setRegionBusy(elements.statusResults, false);
  }
}

async function renderSampleCasePreview() {
  renderCaseStatus(applicantPortalMock.casePacket, {
    latestStatus: buildMockStatus(applicantPortalMock.casePacket),
    useMock: true,
  });
}

function renderCaseStatus(casePacket, options) {
  const status = options.latestStatus || buildMockStatus(casePacket);
  const manualReferralReason =
    status.manual_referral_reason ||
    status.authorization_status?.manual_referral_reason ||
    casePacket.workflow.manual_referral_reason ||
    "";
  const appointments = status.appointments?.length ? status.appointments : casePacket.workflow.appointments || [];
  const decisionNotice = status.decision_notice || casePacket.workflow.decision_notice || null;
  const portClearanceEvents =
    status.port_clearance_events?.length ? status.port_clearance_events : casePacket.workflow.port_clearance_events || [];
  elements.statusResults.hidden = false;
  elements.statusEmpty.hidden = true;
  elements.stateValue.innerHTML = buildStatusChip(status.status);
  elements.holderValue.textContent = titleCase(status.current_holder);
  elements.nextActionValue.textContent = titleCase(status.next_action);
  elements.workspaceLinksPanel.innerHTML = buildWorkspaceLinks(casePacket.case_id, "applicant");

  if (!options.useMock) {
    state.linkedCaseId = casePacket.case_id;
    syncCaseQueryParam(casePacket.case_id);
    rememberRecentCase({
      case_id: casePacket.case_id,
      surface: "applicant",
      current_state: status.status,
      current_holder: status.current_holder,
      next_action: status.next_action,
    });
  }

  const detailItems = [
    ["Case ID", casePacket.case_id],
    ["Applicant", casePacket.applicant.full_name],
    ["Travel window", `${formatDate(casePacket.visa_application.arrival_date)} to ${formatDate(casePacket.visa_application.departure_date)}`],
    ["Decision due", formatDateTime(casePacket.decision_due_at)],
    ["ETA status", buildStatusChip(status.authorization_status?.eta_status || casePacket.workflow.eta_status)],
    ["Port clearance", buildStatusChip(status.port_clearance_state || casePacket.workflow.port_clearance_state)],
    ["Extension status", buildStatusChip(status.extension_state || casePacket.workflow.extension_state || "NOT_REQUESTED")],
    ["Action required from", titleCase(status.action_required_from)],
    ["Policy version", status.authorization_status?.policy_version || casePacket.policy_context.policy_version],
    ["Rule version", status.authorization_status?.rule_version_used || casePacket.policy_context.effective_rule_version],
    ["Publication reference", status.authorization_status?.publication_reference || casePacket.policy_context.publication_reference],
    ["Policy source", linkMarkup(status.authorization_status?.source_uri || casePacket.policy_context.source_uri)],
    ["Official sources", linkListMarkup(status.authorization_status?.official_sources || casePacket.policy_context.official_sources)],
  ];

  elements.statusDefinitionGrid.innerHTML = detailItems
    .map(
      ([label, value]) => `
        <div class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${label}</span>
          <strong class="mt-2 block text-base font-extrabold text-slate-900">${value || "Not available"}</strong>
        </div>
      `
    )
    .join("");

  const latestMessage = status.latest_message;
  elements.latestMessagePanel.innerHTML = latestMessage
    ? `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${latestMessage.subject || "Status update"}</span>
          <p class="mt-3 text-sm leading-7 text-slate-600">${latestMessage.message || "No message body is available yet."}</p>
        </article>
      `
    : `<div class="rounded-[1.5rem] border border-dashed border-slate-300 bg-white/45 p-5 text-sm leading-7 text-slate-600">No applicant-facing message has been recorded for this case yet.</div>`;

  const requiredActionCards = [
    ...(status.required_actions || []).map(
      (action) => `
        <article class="rounded-[1.5rem] border border-amber-200 bg-amber-50 p-5 text-sm leading-7 text-amber-900">
          ${action}
        </article>
      `
    ),
    ...((status.additional_evidence_requests || []).map(
      (request) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-3 flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${request.request_id || "Evidence request"}</span>
              <h3 class="mt-2 text-base font-extrabold text-slate-900">${titleCase(request.status || "OPEN")}</h3>
            </div>
            ${buildStatusChip(request.status || "OPEN")}
          </div>
          <p class="text-sm leading-7 text-slate-600">${request.reason || "Additional evidence has been requested for this case."}</p>
          <div class="mt-4 text-sm text-slate-500">
            <strong class="text-slate-700">Requested items:</strong> ${(request.requested_items || []).join(", ") || "No items listed."}
          </div>
          ${
            request.deadline
              ? `<div class="mt-2 text-sm text-slate-500"><strong class="text-slate-700">Deadline:</strong> ${formatDateTime(request.deadline)}</div>`
              : ""
          }
        </article>
      `
    )),
  ];
  elements.requiredActionsPanel.innerHTML = listMarkup(
    requiredActionCards,
    "No applicant action is currently outstanding for this case."
  );

  const specialHandlingCards = [
    `
      <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
        <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">Manual referral route</span>
        <div class="mt-3">${manualReferralReason ? buildStatusChip("manual referral active", "warning") : buildStatusChip("straight-through route", "success")}</div>
        <p class="mt-4 text-sm leading-7 text-slate-600">${
          manualReferralReason ||
          "No sponsor, nationality, or exception-driven manual referral is currently attached to this case."
        }</p>
      </article>
    `,
    `
      <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
        <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">Extension handling</span>
        <div class="mt-3">${buildStatusChip(status.extension_state || casePacket.workflow.extension_state || "NOT_REQUESTED")}</div>
        <p class="mt-4 text-sm leading-7 text-slate-600">${
          status.extension_state && status.extension_state !== "NOT_REQUESTED"
            ? "An extension-related workflow is active. Follow the latest service instructions before assuming travel or stay dates can change."
            : "No extension workflow is active for this case right now."
        }</p>
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
            ${appointment.instructions || "Instructions will appear here when scheduling details are available."}
          </p>
        </article>
      `
    ),
  ];
  elements.specialHandlingPanel.innerHTML = listMarkup(
    specialHandlingCards,
    "No special-handling signals are currently active for this case."
  );

  elements.caseServiceNoticesPanel.innerHTML = listMarkup(
    (status.service_notices || []).map(
      (notice) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${notice.code || "Case notice"}</span>
          <p class="mt-3 text-sm leading-7 text-slate-600">${notice.message || "No notice text is available for this item."}</p>
        </article>
      `
    ),
    "No additional case-specific notices are active right now."
  );

  const travelFollowUpCards = [
    ...(decisionNotice
      ? [
          `
            <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${decisionNotice.subject || "Decision notice"}</span>
              <p class="mt-3 text-sm leading-7 text-slate-600">${decisionNotice.summary || "No traveler-facing summary is available yet."}</p>
              <div class="mt-4 grid gap-3">
                ${(decisionNotice.next_steps || [])
                  .map(
                    (step) =>
                      `<div class="rounded-[1.25rem] border border-slate-200/80 bg-slate-50/80 p-4 text-sm leading-6 text-slate-700">${step}</div>`
                  )
                  .join("")}
              </div>
            </article>
          `,
        ]
      : []),
    ...(appointments.length
      ? [
          `
            <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">Appointment instructions</span>
              <div class="mt-4 grid gap-3">
                ${appointments
                  .map(
                    (appointment) => `
                      <div class="rounded-[1.25rem] border border-slate-200/80 bg-slate-50/80 p-4 text-sm leading-6 text-slate-700">
                        <strong class="text-slate-900">${titleCase(appointment.appointment_type || "Appointment")}</strong><br />
                        Status: ${titleCase(appointment.status || "PENDING")}<br />
                        Location: ${appointment.location || "Not assigned yet"}<br />
                        Scheduled for: ${formatDateTime(appointment.scheduled_for)}<br />
                        ${appointment.instructions || "Detailed appointment instructions will be shown here once available."}
                      </div>
                    `
                  )
                  .join("")}
              </div>
            </article>
          `,
        ]
      : []),
    ...(portClearanceEvents.length
      ? [
          `
            <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">Port-of-entry follow-up</span>
              <div class="mt-4 grid gap-3">
                ${portClearanceEvents
                  .map(
                    (event) => `
                      <div class="rounded-[1.25rem] border border-slate-200/80 bg-slate-50/80 p-4 text-sm leading-6 text-slate-700">
                        <strong class="text-slate-900">${titleCase(event.event_type || "Port event")}</strong><br />
                        Status: ${titleCase(event.status || "PENDING")}<br />
                        Recorded: ${formatDateTime(event.timestamp)}<br />
                        ${event.notes || "No additional port-of-entry note is available yet."}
                      </div>
                    `
                  )
                  .join("")}
              </div>
            </article>
          `,
        ]
      : []),
  ];
  elements.travelFollowUpPanel.innerHTML = listMarkup(
    travelFollowUpCards,
    "No post-decision travel or appointment follow-up is active for this case yet."
  );

  const uploadedDocuments = status.uploaded_documents?.length ? status.uploaded_documents : casePacket.documents;
  hydrateDocumentResponseForm(casePacket, uploadedDocuments);
  elements.documentSummaryList.innerHTML = listMarkup(
    (uploadedDocuments || []).map(
      (document) => `
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5">
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${document.document_id}</span>
              <h3 class="mt-2 text-lg font-extrabold text-slate-900">${titleCase(document.document_type)}</h3>
            </div>
            ${buildStatusChip(document.status || "UPLOADED")}
          </div>
          ${
            document.file_uri
              ? `<div class="text-sm leading-7 text-slate-600">${linkMarkup(document.file_uri, state.apiBaseUrl)}</div>`
              : `<p class="text-sm leading-7 text-slate-600 break-all">No file reference available.</p>`
          }
        </article>
      `
    ),
    "No uploaded documents are attached to this case yet."
  );

  const timelineMarkup = (status.timeline || casePacket.status_timeline || []).map(
    (event) => `
      <article class="relative mb-4 rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-5 last:mb-0">
        <span class="absolute -left-[1.85rem] top-6 h-3 w-3 rounded-full bg-teal-600 ring-8 ring-teal-100"></span>
        <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <span class="block text-[0.72rem] uppercase tracking-[0.18em] text-slate-500">${formatDateTime(event.timestamp)}</span>
            <h3 class="mt-2 text-lg font-extrabold text-slate-900">${titleCase(event.state)}</h3>
          </div>
          ${buildStatusChip(event.action_owner || event.actor)}
        </div>
        <p class="text-sm leading-7 text-slate-600">${event.description || "No description was attached to this timeline event."}</p>
      </article>
    `
  );

  elements.timelineList.innerHTML = listMarkup(timelineMarkup, "No timeline events have been recorded yet.");

  if (options.useMock) {
    elements.statusEmpty.textContent =
      "The sample case is shown below. Start the backend to replace this preview with live API data.";
  }
}

function hydrateDocumentResponseForm(casePacket, documents) {
  elements.documentResponseCaseIdInput.value = casePacket.case_id;
  setDocumentInputValue("documentResponsePassportUri", documents, "PASSPORT");
  setDocumentInputValue("documentResponseBankUri", documents, "BANK_STATEMENT");
  setDocumentInputValue("documentResponseFlightUri", documents, "FLIGHT_ITINERARY");
  setDocumentInputValue("documentResponseAccommodationUri", documents, "HOTEL_BOOKING_OR_INVITATION");
}

function setDocumentInputValue(fieldName, documents, documentType) {
  const input = elements.documentResponseForm?.elements?.namedItem(fieldName);
  if (!input) {
    return;
  }
  input.value = documents.find((document) => document.document_type === documentType)?.file_uri || "";
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

function buildMockStatus(casePacket) {
  const latestMessage = casePacket.applicant_message_history.at(-1) || null;
  return {
    case_id: casePacket.case_id,
    status: casePacket.workflow.current_state,
    latest_message: latestMessage,
    required_actions: latestMessage?.required_actions || [],
    additional_evidence_requests: casePacket.workflow.additional_evidence_requests || [],
    uploaded_documents: casePacket.documents,
    deadlines: {
      decision_due_at: casePacket.decision_due_at,
    },
    service_notices: applicantPortalMock.notices,
    timeline: casePacket.status_timeline,
    current_holder: casePacket.workflow.current_holder,
    next_action: casePacket.workflow.next_action,
    action_required_from: casePacket.workflow.action_required_from,
    authorization_status: {
      workflow_pack: casePacket.workflow.workflow_pack,
      eta_status: casePacket.workflow.eta_status,
      manual_referral_reason: casePacket.workflow.manual_referral_reason || null,
      policy_version: casePacket.policy_context.policy_version,
      effective_date: casePacket.policy_context.effective_date,
      rule_version_used: casePacket.policy_context.effective_rule_version,
      publication_reference: casePacket.policy_context.publication_reference,
      source_uri: casePacket.policy_context.source_uri,
      official_sources: casePacket.policy_context.official_sources,
      verified_at: casePacket.policy_context.verified_at,
    },
    port_clearance_state: casePacket.workflow.port_clearance_state,
    extension_state: casePacket.workflow.extension_state || "NOT_REQUESTED",
    manual_referral_reason: casePacket.workflow.manual_referral_reason || null,
    appointments: casePacket.workflow.appointments || [],
    decision_notice: casePacket.workflow.decision_notice || null,
    port_clearance_events: casePacket.workflow.port_clearance_events || [],
  };
}

function buildApplicationPayload(formData) {
  const decisionDueAt = formData.get("decisionDueAt");
  return {
    case_id: formData.get("caseId") || startCaseId(),
    applicant: {
      full_name: formData.get("fullName"),
      date_of_birth: formData.get("dateOfBirth"),
      nationality: formData.get("nationality"),
      passport_number: formData.get("passportNumber"),
      contact_email: formData.get("contactEmail"),
      phone: formData.get("phone") || null,
    },
    visa_application: {
      visa_class: "TOURIST",
      purpose_of_travel: formData.get("purposeOfTravel"),
      arrival_date: formData.get("arrivalDate"),
      departure_date: formData.get("departureDate"),
      sponsor: formData.get("sponsor") || null,
      destination_address: formData.get("destinationAddress") || null,
      country_of_application: formData.get("countryOfApplication"),
      payment_status: formData.get("paymentStatus"),
    },
    documents: buildDocumentsPayload(formData),
    decision_due_at: decisionDueAt ? new Date(decisionDueAt).toISOString() : null,
  };
}

async function uploadSelectedFiles(caseId, form, prefix = "", options = {}) {
  const selectedFiles = collectSelectedFiles(form, prefix);
  const warnings = [];
  for (const upload of selectedFiles) {
    try {
      await api.uploadDocumentFile(caseId, upload.documentType, upload.file);
    } catch (error) {
      if (isMissingFileUploadSupport(error) && options.hasUriFallback) {
        warnings.push(
          "Direct file upload is not enabled on the current backend target yet, so the portal used the provided file URI values instead."
        );
        return warnings;
      }
      if (isMissingFileUploadSupport(error)) {
        throw new Error(
          "The current backend target does not support direct file uploads yet. Provide document URIs for this flow or enable the backend document-files endpoint."
        );
      }
      throw error;
    }
  }
  return warnings;
}

function collectSelectedFiles(form, prefix = "") {
  const input = (name) => form?.elements?.namedItem(`${prefix}${name}`);
  return [
    ["PASSPORT", input("PassportFile")],
    ["BANK_STATEMENT", input("BankFile")],
    ["FLIGHT_ITINERARY", input("FlightFile")],
    ["HOTEL_BOOKING_OR_INVITATION", input("AccommodationFile")],
  ]
    .map(([documentType, element]) => ({
      documentType,
      file: element?.files?.[0] || null,
    }))
    .filter((entry) => entry.file);
}

function buildDocumentsPayload(formData, prefix = "") {
  const field = (name) => formData.get(`${prefix}${name}`);
  const documentSpecs = [
    ["DOC-001", "PASSPORT", prefix ? field("PassportUri") : formData.get("passportDocumentUri")],
    ["DOC-002", "BANK_STATEMENT", prefix ? field("BankUri") : formData.get("bankDocumentUri")],
    ["DOC-003", "FLIGHT_ITINERARY", prefix ? field("FlightUri") : formData.get("flightDocumentUri")],
    ["DOC-004", "HOTEL_BOOKING_OR_INVITATION", prefix ? field("AccommodationUri") : formData.get("accommodationDocumentUri")],
  ];

  return documentSpecs
    .filter(([, , fileUri]) => String(fileUri || "").trim())
    .map(([documentId, documentType, fileUri]) => ({
      document_id: documentId,
      document_type: documentType,
      file_uri: String(fileUri).trim(),
      status: "UPLOADED",
    }));
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
