const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export function createApiClient(baseUrl) {
  const normalizedBaseUrl = (baseUrl || DEFAULT_API_BASE_URL).replace(/\/+$/, "");

  async function request(path, options = {}) {
    const response = await fetch(`${normalizedBaseUrl}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
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
    getChecklist() {
      return request("/checklists/tourist-visit");
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

export const applicantPortalMock = {
  checklist: {
    workflow_pack: "SRI_LANKA_TOURIST_VISIT",
    visa_class: "TOURIST",
    checklist: [
      {
        code: "PASSPORT",
        title: "Passport biodata page",
        description: "Provide a clear scan of the passport biodata page.",
        required: true,
        guidance: "Ensure the MRZ and passport number are legible.",
      },
      {
        code: "FLIGHT_ITINERARY",
        title: "Flight itinerary",
        description: "Provide a tentative arrival and departure itinerary.",
        required: true,
        guidance: "Dates should align with the application stay window.",
      },
      {
        code: "FUNDS",
        title: "Proof of funds",
        description: "Show the ability to support the proposed visit.",
        required: true,
        guidance: "Recent statements are preferred for manual review readiness.",
      },
    ],
    notes: [
      "Final entry clearance is still decided at the port of entry.",
      "Manual referral may require additional sponsor or mission review.",
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
    ],
    workflow: {
      current_state: "DOCUMENT_REVIEW",
      current_holder: "SYSTEM",
      next_action: "VERIFY_UPLOADED_DOCUMENTS",
      action_required_from: "SYSTEM",
      eta_status: "ETA_SUBMITTED",
      port_clearance_state: "NOT_STARTED",
      extension_state: "NOT_REQUESTED",
      workflow_pack: "SRI_LANKA_TOURIST_VISIT",
      manual_referral_reason: null,
    },
    policy_context: {
      effective_rule_version: "sl-rule-pack-2026-05-25",
      publication_reference: "ETA-40-COUNTRY-SCHEME-2026-05-25",
      policy_version: "sl-tourist-policy-v1",
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
        state: "DOCUMENT_REVIEW",
        timestamp: "2026-05-25T08:40:00Z",
        actor: "SYSTEM",
        description: "Documents entered the pre-check and readability review stage.",
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
  casePacket: applicantPortalMock.casePacket,
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
        policy_id: "TOURIST-12-A",
        requirement: "Valid passport and travel purpose must align with a short tourist visit.",
        status: "SATISFIED",
      },
      {
        policy_id: "TOURIST-12-B",
        requirement: "Applicant must demonstrate sufficient support for the travel period.",
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
      policy_source_uri: "https://example.gov.lk/tourist-policy",
      official_sources: ["https://eta.gov.lk", "https://immigration.gov.lk"],
      verified_at: "2026-05-25T10:15:00Z",
    },
    audit_timeline: [
      {
        timestamp: "2026-05-25T08:15:00Z",
        event_type: "CASE_CREATED",
        actor_type: "SYSTEM",
        actor_id: "portal",
        recommendation: "",
        human_action: "",
      },
      {
        timestamp: "2026-05-25T09:05:00Z",
        event_type: "CASE_READY_FOR_OFFICER_REVIEW",
        actor_type: "SYSTEM",
        actor_id: "workflow",
        recommendation: "APPROVE_READY",
        human_action: "",
      },
    ],
  },
};
