const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export function normalizeApiBaseUrl(value) {
  return (value || DEFAULT_API_BASE_URL).trim().replace(/\/+$/, "") || DEFAULT_API_BASE_URL;
}

export function getStoredApiBaseUrl() {
  return normalizeApiBaseUrl(localStorage.getItem("visaFlowApiBaseUrl") || DEFAULT_API_BASE_URL);
}

export function setStoredApiBaseUrl(value) {
  const normalized = normalizeApiBaseUrl(value);
  localStorage.setItem("visaFlowApiBaseUrl", normalized);
  return normalized;
}

export function clearStoredApiBaseUrl() {
  localStorage.removeItem("visaFlowApiBaseUrl");
  return DEFAULT_API_BASE_URL;
}

export function createApiClient(baseUrl) {
  const normalizedBaseUrl = normalizeApiBaseUrl(baseUrl);

  async function request(path, options = {}) {
    const headers = {
      ...(options.headers || {}),
    };
    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    const response = await fetch(`${normalizedBaseUrl}${path}`, {
      headers,
      ...options,
    });

    if (!response.ok) {
      let message = `${response.status} ${response.statusText}`;
      try {
        const payload = await response.json();
        message = payload.detail || payload.message || message;
      } catch {
        // Keep the HTTP status message when the body is not JSON.
      }
      throw new Error(message);
    }

    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      return response.json();
    }
    return response.text();
  }

  return {
    get baseUrl() {
      return normalizedBaseUrl;
    },
    getHealth() {
      return request("/health");
    },
    getSystemNotices() {
      return request("/system/notices");
    },
    getSupervisorQueues() {
      return request("/supervisor/queues");
    },
    getSupervisorCases(filters = {}) {
      const params = new URLSearchParams();
      if (filters.state) {
        params.set("state", filters.state);
      }
      if (filters.holder) {
        params.set("holder", filters.holder);
      }
      const query = params.toString();
      return request(`/supervisor/cases${query ? `?${query}` : ""}`);
    },
    getChecklist() {
      return request("/checklists/tourist-visit");
    },
    getPolicyRequirements(visaClass = "TOURIST") {
      return request(`/policies/${encodeURIComponent(visaClass)}/requirements`);
    },
    getActiveGovernanceRules() {
      return request("/governance/rules/active");
    },
    createApplication(payload) {
      return request("/applications", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    getCase(caseId) {
      return request(`/cases/${encodeURIComponent(caseId)}`);
    },
    uploadDocuments(caseId, payload) {
      return request(`/cases/${encodeURIComponent(caseId)}/documents`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    uploadDocumentFile(caseId, documentType, file) {
      const formData = new FormData();
      formData.set("document_type", documentType);
      formData.set("file", file);
      return request(`/cases/${encodeURIComponent(caseId)}/document-files`, {
        method: "POST",
        body: formData,
      });
    },
    getCaseStatus(caseId) {
      return request(`/cases/${encodeURIComponent(caseId)}/status`);
    },
    getAuthorizationStatus(caseId) {
      return request(`/cases/${encodeURIComponent(caseId)}/authorization-status`);
    },
    getCaseTimeline(caseId) {
      return request(`/cases/${encodeURIComponent(caseId)}/timeline`);
    },
    processCase(caseId) {
      return request(`/cases/${encodeURIComponent(caseId)}/process`, {
        method: "POST",
      });
    },
    getOfficerBrief(caseId) {
      return request(`/cases/${encodeURIComponent(caseId)}/officer-brief`);
    },
    getAudit(caseId) {
      return request(`/cases/${encodeURIComponent(caseId)}/audit`);
    },
    submitOfficerDecision(caseId, payload) {
      return request(`/cases/${encodeURIComponent(caseId)}/officer-decision`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
  };
}

export function formatDate(value) {
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
  }).format(parsed);
}

export function formatDateTime(value) {
  if (!value) {
    return "Not available";
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

export function startCaseId(prefix = "VISA") {
  const stamp = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  const randomSuffix = Math.random().toString(36).slice(2, 6).toUpperCase();
  return `${prefix}-${stamp}-${randomSuffix}`;
}

export function titleCase(value) {
  return String(value || "")
    .toLowerCase()
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(" ");
}

export function toneForStatus(value) {
  const normalized = String(value || "").toUpperCase();
  if (/(APPROV|READY|COMPLETE|CLEAR|ACTIVE|PAID)/.test(normalized)) {
    return "success";
  }
  if (/(REJECT|REFUS|ERROR|INVALID|RISK)/.test(normalized)) {
    return "danger";
  }
  if (/(WAIT|REVIEW|REQUEST|MANUAL|PENDING|ESCALATE)/.test(normalized)) {
    return "warning";
  }
  return "info";
}

export function buildStatusChip(label, tone = toneForStatus(label)) {
  const toneClasses = {
    success: "bg-emerald-100 text-emerald-800 ring-emerald-200",
    warning: "bg-amber-100 text-amber-800 ring-amber-200",
    danger: "bg-rose-100 text-rose-800 ring-rose-200",
    info: "bg-teal-100 text-teal-800 ring-teal-200",
  };

  return `<span class="inline-flex items-center rounded-full px-3 py-1 text-xs font-bold uppercase tracking-[0.18em] ring-1 ${
    toneClasses[tone] || toneClasses.info
  }">${titleCase(label)}</span>`;
}

export function listMarkup(items, emptyText) {
  if (!items || !items.length) {
    return `<div class="rounded-3xl border border-dashed border-slate-300 bg-white/45 p-5 text-sm leading-7 text-slate-600">${emptyText}</div>`;
  }
  return items.join("");
}

export function setRegionBusy(element, isBusy) {
  if (!element) {
    return;
  }
  element.setAttribute("aria-busy", String(Boolean(isBusy)));
}

export function setButtonBusy(button, isBusy, busyLabel) {
  if (!button) {
    return;
  }
  if (!button.dataset.idleLabel) {
    button.dataset.idleLabel = button.textContent.trim();
  }
  button.disabled = Boolean(isBusy);
  button.setAttribute("aria-busy", String(Boolean(isBusy)));
  button.textContent = isBusy ? busyLabel : button.dataset.idleLabel;
}

export const applicantPortalMock = {
  checklist: {
    workflow_pack: "SRI_LANKA_TOURIST_VISIT",
    country: "Sri Lanka",
    visa_class: "TOURIST",
    verified_at: "2026-05-25",
    official_sources: [
      "https://www.immigration.gov.lk/pages_e.php?id=14&os=av..",
      "https://www.eta.gov.lk/slvisa/visainfo/weta.jsp?ch1=current&locale=en_US",
    ],
    checklist: [
      {
        code: "PASSPORT",
        title: "Valid Passport",
        description: "Provide a passport valid for at least six months from the intended date of arrival in Sri Lanka.",
        required: true,
        guidance: "Use a clear, readable copy. The passport details must match the application data.",
      },
      {
        code: "FUNDS",
        title: "Funds and Return Assurance",
        description: "Show evidence of adequate funds and return or onward travel assurance for the intended short visit.",
        required: true,
        guidance: "Recent bank statements and onward ticket or itinerary evidence are the baseline support set in this PoC.",
      },
      {
        code: "PURPOSE",
        title: "Tourist Visit Purpose",
        description: "Provide travel purpose details consistent with a short tourist visit to Sri Lanka.",
        required: true,
        guidance: "Avoid mixing tourist travel with work, long-stay, or business-only activity in the same purpose statement.",
      },
      {
        code: "OFFICIAL_PAYMENT",
        title: "Official Payment Channel",
        description: "Use only the official ETA and immigration payment channels.",
        required: true,
        guidance: "The product should make official payment and case references explicit to reduce scam exposure.",
      },
    ],
    notes: [
      "ETA is not the same as final port-of-entry clearance.",
      "Some nationalities or special cases may require sponsor-backed or manual handling.",
      "Extension handling may require online steps, appointments, or head-office action.",
    ],
  },
  notices: [
    {
      code: "HUMAN_REVIEW_REQUIRED",
      level: "INFO",
      message: "This portal supports processing, but the legal decision remains with an immigration officer.",
    },
  ],
  casePacket: {
    case_id: "VISA-2026-0001",
    applicant: {
      full_name: "Arjun Mehta",
      date_of_birth: "1998-04-12",
      nationality: "Indian",
      passport_number: "P1234567",
      contact_email: "arjun@example.com",
      phone: "+91 9876543210",
    },
    visa_application: {
      visa_class: "TOURIST",
      purpose_of_travel: "Tourism and sightseeing in Sri Lanka",
      arrival_date: "2026-08-10",
      departure_date: "2026-08-20",
      sponsor: null,
      destination_address: "Hotel Example, Colombo",
      country_of_application: "India",
      payment_status: "PAID",
    },
    documents: [
      {
        document_id: "DOC-001",
        document_type: "PASSPORT",
        file_uri: "gs://visa-docs/case-0001/passport.pdf",
        status: "PROCESSED",
      },
      {
        document_id: "DOC-002",
        document_type: "BANK_STATEMENT",
        file_uri: "gs://visa-docs/case-0001/bank.pdf",
        status: "UPLOADED",
      },
      {
        document_id: "DOC-003",
        document_type: "FLIGHT_ITINERARY",
        file_uri: "gs://visa-docs/case-0001/flight.pdf",
        status: "UPLOADED",
      },
    ],
    workflow: {
      current_state: "UNDER_PRECHECK",
      current_holder: "SYSTEM",
      next_action: "RUN_INTAKE_PRECHECK",
      action_required_from: "SYSTEM",
      eta_status: "ETA_UNDER_PRECHECK",
      port_clearance_state: "NOT_STARTED",
      extension_state: "NOT_REQUESTED",
      workflow_pack: "SRI_LANKA_TOURIST_VISIT",
      manual_referral_reason: null,
      appointments: [],
      port_clearance_events: [],
      decision_notice: null,
    },
    policy_context: {
      effective_rule_version: "sl-rule-pack-2026-05-25",
      publication_reference: "ETA-40-COUNTRY-SCHEME-2026-05-25",
      policy_version: "sl-tourist-policy-v1",
      effective_date: "2026-05-25",
      source_uri: "https://www.immigration.gov.lk/pages_e.php?id=14&os=av..",
      official_sources: [
        "https://www.immigration.gov.lk/pages_e.php?id=14&os=av..",
        "https://www.eta.gov.lk/slvisa/visainfo/weta.jsp?ch1=current&locale=en_US",
      ],
      verified_at: "2026-05-25",
    },
    status_timeline: [
      {
        state: "SUBMITTED",
        timestamp: "2026-05-25T08:15:00Z",
        actor: "SYSTEM",
        description: "Case submitted through the online portal.",
        action_owner: "SYSTEM",
      },
      {
        state: "UNDER_PRECHECK",
        timestamp: "2026-05-25T08:40:00Z",
        actor: "SYSTEM",
        description: "The case entered the Sri Lanka tourist visit pre-check and readability review stage.",
        action_owner: "SYSTEM",
      },
    ],
    applicant_message_history: [
      {
        subject: "Application received",
        message: "Your case was created and is waiting for pre-check validation.",
        required_actions: [],
      },
    ],
    decision_due_at: "2026-06-03T17:00:00Z",
  },
};

export const officerDashboardMock = {
  casePacket: {
    ...applicantPortalMock.casePacket,
    workflow: {
      ...applicantPortalMock.casePacket.workflow,
      current_state: "READY_FOR_OFFICER_REVIEW",
      current_holder: "OFFICER",
      next_action: "HUMAN_OFFICER_FINAL_REVIEW",
      action_required_from: "OFFICER",
      eta_status: "ETA_UNDER_OFFICER_REVIEW",
    },
    status_timeline: [
      ...applicantPortalMock.casePacket.status_timeline,
      {
        state: "READY_FOR_OFFICER_REVIEW",
        timestamp: "2026-05-25T09:05:00Z",
        actor: "SYSTEM",
        description: "Automated checks completed and the case moved to human officer review.",
        action_owner: "OFFICER",
      },
    ],
  },
  officerBrief: {
    case_id: "VISA-2026-0001",
    visa_class: "TOURIST",
    applicant_summary:
      "Arjun Mehta, passport P1234567, travel purpose: Tourism and sightseeing in Sri Lanka, workflow pack: SRI_LANKA_TOURIST_VISIT",
    recommendation: "APPROVE_READY",
    confidence: 0.91,
    human_decision_required: true,
    agent_results: [
      {
        agent_name: "intake_completeness_agent",
        status: "COMPLETE",
        summary: "All required baseline evidence is present for the current stage.",
        risk_level: "INFO",
      },
      {
        agent_name: "document_validator_agent",
        status: "VALID",
        summary: "Passport extraction and validation completed without blocking mismatches.",
        risk_level: "INFO",
      },
      {
        agent_name: "financial_employment_agent",
        status: "PASS",
        summary: "Average balance is above the configured threshold for the visit window.",
        risk_level: "INFO",
      },
      {
        agent_name: "policy_compliance_agent",
        status: "MEETS_REQUIREMENTS",
        summary: "Current rule pack requirements appear satisfied on the available evidence.",
        risk_level: "INFO",
      },
      {
        agent_name: "security_background_agent",
        status: "CLEAR",
        summary: "No blocking security matches were surfaced in the mock review path.",
        risk_level: "CLEAR",
      },
      {
        agent_name: "risk_fraud_agent",
        status: "LOW",
        summary: "Fraud indicators remain low and do not block officer review.",
        risk_level: "LOW",
      },
    ],
    key_evidence: ["DOC-001", "DOC-002", "DOC-003"],
    policy_references: [
      {
        policy_id: "TOURIST-01-A",
        requirement: "Applicant must hold a passport valid for at least six months from the intended date of arrival in Sri Lanka.",
        status: "SATISFIED",
      },
      {
        policy_id: "TOURIST-12-B",
        requirement: "Applicant must show adequate funds for maintenance during the intended short stay in Sri Lanka.",
        status: "SATISFIED",
      },
      {
        policy_id: "TOURIST-20-C",
        requirement: "Applicant must provide return or onward travel assurance consistent with a temporary tourist visit to Sri Lanka.",
        status: "SATISFIED",
      },
    ],
    risk_flags: [],
    missing_items: [],
    questions_for_officer: [
      "Confirm that the recommendation aligns with the Sri Lanka case record, active rule pack, and local operating procedures.",
      "Remember that ETA issuance does not remove port-of-entry clearance requirements.",
    ],
    final_decision_options: ["APPROVE", "REJECT", "REQUEST_MORE_INFO", "ESCALATE"],
    recommendation_panel: {
      recommendation: "APPROVE_READY",
      human_decision_required: true,
      next_action: "HUMAN_OFFICER_FINAL_REVIEW",
      current_holder: "OFFICER",
      action_required_from: "OFFICER",
    },
    evidence_viewer: {
      passport_fields: {
        passport_number: "P1234567",
        full_name: "Arjun Mehta",
        date_of_birth: "1998-04-12",
        nationality: "Indian",
        expiry_date: "2032-03-02",
      },
      bank_statement_metrics: {
        average_balance: 4200,
        currency: "USD",
        suspicious_patterns: [],
      },
      itinerary_evidence: ["DOC-003"],
      rule_version_used: "sl-rule-pack-2026-05-25",
      publication_reference: "ETA-40-COUNTRY-SCHEME-2026-05-25",
      policy_source_uri: "https://www.immigration.gov.lk/pages_e.php?id=14&os=av..",
      official_sources: [
        "https://www.immigration.gov.lk/pages_e.php?id=14&os=av..",
        "https://www.eta.gov.lk/slvisa/visainfo/weta.jsp?ch1=current&locale=en_US",
      ],
      verified_at: "2026-05-25",
    },
    audit_timeline: [
      {
        timestamp: "2026-05-25T08:15:00Z",
        event_type: "CASE_CREATED",
        actor_type: "SYSTEM",
        actor_id: "portal",
        policy_version: "sl-tourist-policy-v1",
        rule_version_used: "sl-rule-pack-2026-05-25",
        recommendation: "",
        human_action: "",
      },
      {
        timestamp: "2026-05-25T09:05:00Z",
        event_type: "CASE_READY_FOR_OFFICER_REVIEW",
        actor_type: "SYSTEM",
        actor_id: "workflow",
        policy_version: "sl-tourist-policy-v1",
        rule_version_used: "sl-rule-pack-2026-05-25",
        recommendation: "APPROVE_READY",
        human_action: "",
      },
    ],
  },
};

export const supervisorDashboardMock = {
  queues: {
    workflow_pack: "SRI_LANKA_TOURIST_VISIT",
    counts_by_state: {
      SUBMITTED: 4,
      WAITING_FOR_DOCUMENTS: 3,
      REFERRED_TO_MANUAL_REVIEW: 2,
      READY_FOR_OFFICER_REVIEW: 6,
      POST_DECISION_FULFILLMENT: 1,
    },
    manual_referrals: 2,
    waiting_for_documents: 3,
    ready_for_officer_review: 6,
  },
  cases: {
    workflow_pack: "SRI_LANKA_TOURIST_VISIT",
    total_cases: 4,
    filtered_count: 4,
    state_filter: "",
    holder_filter: "",
    cases: [
      {
        case_id: "VISA-2026-0041",
        applicant_name: "Arjun Mehta",
        nationality: "Indian",
        visa_class: "TOURIST",
        current_state: "READY_FOR_OFFICER_REVIEW",
        current_holder: "OFFICER",
        next_action: "HUMAN_OFFICER_FINAL_REVIEW",
        action_required_from: "OFFICER",
        eta_status: "ETA_UNDER_OFFICER_REVIEW",
        manual_referral_reason: null,
        policy_version: "sl-tourist-policy-v1",
        rule_version_used: "sl-rule-pack-2026-05-25",
        publication_reference: "ETA-40-COUNTRY-SCHEME-2026-05-25",
        decision_due_at: "2026-06-03T17:00:00Z",
        updated_at: "2026-05-26T07:40:00Z",
      },
      {
        case_id: "VISA-2026-0042",
        applicant_name: "Amina Yusuf",
        nationality: "Nigerian",
        visa_class: "TOURIST",
        current_state: "REFERRED_TO_MANUAL_REVIEW",
        current_holder: "MISSION_OR_HEAD_OFFICE",
        next_action: "MANUAL_SPONSOR_OR_EXCEPTION_REVIEW",
        action_required_from: "MISSION_OR_HEAD_OFFICE",
        eta_status: "ETA_MANUAL_REVIEW",
        manual_referral_reason: "Tourist or business ETA should be routed through Sri Lankan sponsor and head-office handling.",
        policy_version: "sl-tourist-policy-v1",
        rule_version_used: "sl-rule-pack-2026-05-25",
        publication_reference: "ETA-40-COUNTRY-SCHEME-2026-05-25",
        decision_due_at: "2026-06-05T12:00:00Z",
        updated_at: "2026-05-26T07:32:00Z",
      },
      {
        case_id: "VISA-2026-0043",
        applicant_name: "Nimal Perera",
        nationality: "Sri Lankan Sponsor Route",
        visa_class: "TOURIST",
        current_state: "WAITING_FOR_DOCUMENTS",
        current_holder: "APPLICANT",
        next_action: "RESPOND_TO_INFORMATION_REQUEST",
        action_required_from: "APPLICANT",
        eta_status: "ETA_ADDITIONAL_EVIDENCE_REQUIRED",
        manual_referral_reason: null,
        policy_version: "sl-tourist-policy-v1",
        rule_version_used: "sl-rule-pack-2026-05-25",
        publication_reference: "ETA-40-COUNTRY-SCHEME-2026-05-25",
        decision_due_at: "2026-06-01T09:00:00Z",
        updated_at: "2026-05-26T07:25:00Z",
      },
      {
        case_id: "VISA-2026-0044",
        applicant_name: "Sara Ahmed",
        nationality: "Syrian",
        visa_class: "TOURIST",
        current_state: "REFERRED_TO_MANUAL_REVIEW",
        current_holder: "MISSION_OR_HEAD_OFFICE",
        next_action: "MANUAL_SPONSOR_OR_EXCEPTION_REVIEW",
        action_required_from: "MISSION_OR_HEAD_OFFICE",
        eta_status: "ETA_MANUAL_REVIEW",
        manual_referral_reason: "Tourist or business ETA should be routed through Sri Lankan sponsor and head-office handling.",
        policy_version: "sl-tourist-policy-v1",
        rule_version_used: "sl-rule-pack-2026-05-25",
        publication_reference: "ETA-40-COUNTRY-SCHEME-2026-05-25",
        decision_due_at: "2026-06-07T16:30:00Z",
        updated_at: "2026-05-26T07:18:00Z",
      },
    ],
  },
  notices: applicantPortalMock.notices,
};

export const governanceCenterMock = {
  requirements: {
    visa_class: "TOURIST",
    workflow_pack: "SRI_LANKA_TOURIST_VISIT",
    policy_version: "sl-tourist-policy-v1",
    effective_date: "2026-05-25",
    source_uri: "https://www.immigration.gov.lk/pages_e.php?id=14&os=av..",
    official_sources: [
      "https://www.eta.gov.lk/",
      "https://www.eta.gov.lk/slvisa/visainfo/weta.jsp?ch1=current&locale=en_US",
      "https://www.immigration.gov.lk/pages_e.php?id=14&os=av..",
    ],
    verified_at: "2026-05-25",
    requirements: [
      {
        policy_id: "TOURIST-01-A",
        requirement: "Applicant must hold a passport valid for at least six months from the intended arrival date.",
      },
      {
        policy_id: "TOURIST-12-B",
        requirement: "Applicant must show adequate funds for the intended short stay in Sri Lanka.",
      },
      {
        policy_id: "TOURIST-20-C",
        requirement: "Applicant must show return or onward travel assurance consistent with a temporary tourist visit.",
      },
    ],
  },
  rules: {
    workflow_pack: "SRI_LANKA_TOURIST_VISIT",
    country: "Sri Lanka",
    verified_at: "2026-05-25",
    official_sources: [
      "https://www.eta.gov.lk/",
      "https://www.eta.gov.lk/slvisa/visainfo/weta.jsp?ch1=current&locale=en_US",
      "https://www.immigration.gov.lk/pages_e.php?id=14&os=vb..",
      "https://www.immigration.gov.lk/pages_e.php?id=14&os=av..",
      "https://www.immigration.gov.lk/pages_e.php?id=58",
      "https://eservices.immigration.gov.lk/appointment_service.html",
    ],
    active_policy_version: {
      workflow_pack: "SRI_LANKA_TOURIST_VISIT",
      policy_version: "sl-tourist-policy-v1",
      rule_version: "sl-rule-pack-2026-05-25",
      effective_date: "2026-05-25",
      publication_reference: "ETA-40-COUNTRY-SCHEME-2026-05-25",
      notes: "Officer workflow should use the active internal rule pack even when public channels lag.",
    },
    active_circulars: [
      {
        circular_id: "SL-ETA-2026-05-25",
        title: "40-country free-of-charge tourist ETA scheme",
        effective_date: "2026-05-25",
        status: "ACTIVE",
        legal_owner: "Department of Immigration and Emigration",
        public_summary: "Certain nationalities can obtain a 30-day tourist ETA free of charge.",
        internal_summary: "Apply the active 2026 tourist ETA pack and preserve nationality-based exceptions separately.",
        publications: [
          {
            channel: "ETA_PORTAL",
            published_at: "2026-05-25",
            reference: "https://www.eta.gov.lk/",
            notes: "40-country free-of-charge tourist ETA notice visible on ETA site.",
          },
        ],
      },
      {
        circular_id: "SL-ETA-2025-10-13-REVOKED",
        title: "ETA mandatory announcement revoked until further notice",
        effective_date: "2025-10-13",
        status: "REVOKED_NOTICE_REMAINS_VISIBLE",
        legal_owner: "Department of Immigration and Emigration",
        public_summary: "Some public pages still show wording about the revocation of the ETA-mandatory notice.",
        internal_summary: "Public channel inconsistency must not override the active internal rule pack.",
        publications: [
          {
            channel: "IMMIGRATION_GENERAL_INFO",
            published_at: "2025-10-13",
            reference: "https://www.immigration.gov.lk/pages_e.php?id=14&os=vb..",
            notes: "General information page still references revoked ETA wording.",
          },
        ],
      },
    ],
    nationality_exception_rules: [
      {
        rule_id: "SL-SPONSOR-001",
        nationality: "AFGHANISTAN",
        requires_sponsor: true,
        requires_manual_review: true,
        routing_target: "HEAD_OFFICE",
        reason: "Tourist or business ETA should be routed through Sri Lankan sponsor and head-office handling.",
      },
      {
        rule_id: "SL-SPONSOR-004",
        nationality: "NIGERIA",
        requires_sponsor: true,
        requires_manual_review: true,
        routing_target: "HEAD_OFFICE",
        reason: "Tourist or business ETA should be routed through Sri Lankan sponsor and head-office handling.",
      },
      {
        rule_id: "SL-SPONSOR-006",
        nationality: "SYRIA",
        requires_sponsor: true,
        requires_manual_review: true,
        routing_target: "HEAD_OFFICE",
        reason: "Tourist or business ETA should be routed through Sri Lankan sponsor and head-office handling.",
      },
    ],
  },
};
