import {
  applicantPortalMock,
  buildStatusChip,
  createApiClient,
  formatDate,
  formatDateTime,
  listMarkup,
  startCaseId,
  titleCase,
} from "../shared/app.js";

const elements = {
  apiModePill: document.querySelector("#api-mode-pill"),
  heroNoticeCopy: document.querySelector("#hero-notice-copy"),
  applicationForm: document.querySelector("#application-form"),
  statusForm: document.querySelector("#status-form"),
  formFeedback: document.querySelector("#form-feedback"),
  caseIdInput: document.querySelector("#case-id"),
  lookupCaseIdInput: document.querySelector("#lookup-case-id"),
  loadSampleButton: document.querySelector("#load-sample-button"),
  useSampleStatusButton: document.querySelector("#use-sample-status-button"),
  checklistList: document.querySelector("#checklist-list"),
  checklistNotes: document.querySelector("#checklist-notes"),
  noticeList: document.querySelector("#notice-list"),
  statusResults: document.querySelector("#status-results"),
  statusEmpty: document.querySelector("#status-empty"),
  stateValue: document.querySelector("#state-value"),
  holderValue: document.querySelector("#holder-value"),
  nextActionValue: document.querySelector("#next-action-value"),
  statusDefinitionGrid: document.querySelector("#status-definition-grid"),
  documentSummaryList: document.querySelector("#document-summary-list"),
  timelineList: document.querySelector("#timeline-list"),
};

const state = {
  apiBaseUrl: localStorage.getItem("visaFlowApiBaseUrl") || "http://127.0.0.1:8000",
  apiAvailable: false,
};

const api = createApiClient(state.apiBaseUrl);

async function initialize() {
  elements.caseIdInput.value = startCaseId();
  elements.lookupCaseIdInput.value = applicantPortalMock.casePacket.case_id;
  wireEvents();
  await Promise.all([loadOperationalChrome(), renderSampleCasePreview()]);
}

function wireEvents() {
  elements.applicationForm.addEventListener("submit", handleApplicationSubmit);
  elements.statusForm.addEventListener("submit", handleStatusLookup);
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
            `<div class="rounded-[1.25rem] border border-slate-200/80 bg-white/75 p-4 text-sm leading-6 text-slate-600"><strong class="text-slate-900">Official sources:</strong> ${payload.official_sources.join(", ")}</div>`,
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
    await api.processCase(createdCase.case_id);

    const [processedCase, caseStatus] = await Promise.all([
      api.getCase(createdCase.case_id),
      api.getCaseStatus(createdCase.case_id),
    ]);

    elements.lookupCaseIdInput.value = createdCase.case_id;
    renderCaseStatus(processedCase, {
      latestStatus: caseStatus,
      useMock: false,
    });
    elements.formFeedback.textContent = `Application ${createdCase.case_id} created and entered the Sri Lanka processing workflow.`;
  } catch (error) {
    elements.formFeedback.textContent = `Submission failed: ${error.message}`;
  }
}

async function handleStatusLookup(event) {
  event.preventDefault();
  const caseId = elements.lookupCaseIdInput.value.trim();
  if (!caseId) {
    return;
  }

  try {
    if (!state.apiAvailable) {
      renderCaseStatus(applicantPortalMock.casePacket, {
        latestStatus: buildMockStatus(applicantPortalMock.casePacket),
        useMock: true,
      });
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
  elements.statusResults.hidden = false;
  elements.statusEmpty.hidden = true;
  elements.stateValue.innerHTML = buildStatusChip(status.status);
  elements.holderValue.textContent = titleCase(status.current_holder);
  elements.nextActionValue.textContent = titleCase(status.next_action);

  const detailItems = [
    ["Case ID", casePacket.case_id],
    ["Applicant", casePacket.applicant.full_name],
    ["Travel window", `${formatDate(casePacket.visa_application.arrival_date)} to ${formatDate(casePacket.visa_application.departure_date)}`],
    ["Decision due", formatDateTime(casePacket.decision_due_at)],
    ["ETA status", buildStatusChip(status.authorization_status?.eta_status || casePacket.workflow.eta_status)],
    ["Port clearance", buildStatusChip(status.port_clearance_state || casePacket.workflow.port_clearance_state)],
    ["Action required from", titleCase(status.action_required_from)],
    ["Policy version", status.authorization_status?.policy_version || casePacket.policy_context.policy_version],
    ["Rule version", status.authorization_status?.rule_version_used || casePacket.policy_context.effective_rule_version],
    ["Publication reference", status.authorization_status?.publication_reference || casePacket.policy_context.publication_reference],
    ["Policy source", status.authorization_status?.source_uri || casePacket.policy_context.source_uri],
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

  const uploadedDocuments = status.uploaded_documents?.length ? status.uploaded_documents : casePacket.documents;
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
          <p class="text-sm leading-7 text-slate-600 break-all">${document.file_uri || "No file reference available."}</p>
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

function buildMockStatus(casePacket) {
  return {
    case_id: casePacket.case_id,
    status: casePacket.workflow.current_state,
    latest_message: casePacket.applicant_message_history.at(-1) || null,
    required_actions: [],
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
      policy_version: casePacket.policy_context.policy_version,
      effective_date: casePacket.policy_context.effective_date,
      rule_version_used: casePacket.policy_context.effective_rule_version,
      publication_reference: casePacket.policy_context.publication_reference,
      source_uri: casePacket.policy_context.source_uri,
      official_sources: casePacket.policy_context.official_sources,
      verified_at: casePacket.policy_context.verified_at,
    },
    port_clearance_state: casePacket.workflow.port_clearance_state,
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

function buildDocumentsPayload(formData) {
  const documentSpecs = [
    ["DOC-001", "PASSPORT", formData.get("passportDocumentUri")],
    ["DOC-002", "BANK_STATEMENT", formData.get("bankDocumentUri")],
    ["DOC-003", "FLIGHT_ITINERARY", formData.get("flightDocumentUri")],
    ["DOC-004", "HOTEL_BOOKING_OR_INVITATION", formData.get("accommodationDocumentUri")],
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

initialize();
