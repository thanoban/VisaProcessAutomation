import {
  buildStatusChip,
  clearStoredApiBaseUrl,
  createApiClient,
  formatDateTime,
  getRecentCases,
  getStoredApiBaseUrl,
  setButtonBusy,
  setStoredApiBaseUrl,
} from "./shared/app.js";

const elements = {
  apiPill: document.querySelector("#frontend-api-pill"),
  apiForm: document.querySelector("#api-target-form"),
  apiInput: document.querySelector("#api-base-url"),
  resetButton: document.querySelector("#reset-api-target-button"),
  currentTarget: document.querySelector("#current-api-target"),
  healthChip: document.querySelector("#api-health-chip"),
  feedback: document.querySelector("#api-target-feedback"),
  clearRecentCasesButton: document.querySelector("#clear-recent-cases-button"),
  recentCasesList: document.querySelector("#recent-cases-list"),
};

async function initialize() {
  elements.apiInput.value = getStoredApiBaseUrl();
  elements.apiForm.addEventListener("submit", handleSaveTarget);
  elements.resetButton.addEventListener("click", handleResetTarget);
  elements.clearRecentCasesButton.addEventListener("click", handleClearRecentCases);
  renderRecentCases();
  await refreshHealthState("Saved API target loaded.");
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
  setButtonBusy(elements.apiForm.querySelector("button[type='submit']"), true, "Saving...");
  setButtonBusy(elements.resetButton, true, "Resetting...");

  try {
    const health = await api.getHealth();
    elements.apiPill.textContent = `Live API: ${apiBaseUrl}`;
    elements.healthChip.innerHTML = buildStatusChip(health.status || "connected", "success");
    elements.feedback.textContent = `${messagePrefix} Health check succeeded for ${apiBaseUrl}.`;
  } catch (error) {
    elements.apiPill.textContent = `Saved target: ${apiBaseUrl}`;
    elements.healthChip.innerHTML = buildStatusChip("unreachable", "warning");
    elements.feedback.textContent = `${messagePrefix} Health check failed for ${apiBaseUrl}: ${error.message}`;
  } finally {
    setButtonBusy(elements.apiForm.querySelector("button[type='submit']"), false, "Saving...");
    setButtonBusy(elements.resetButton, false, "Resetting...");
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
            <strong class="text-slate-900">Current holder:</strong> ${titleForToken(item.current_holder)}<br />
            <strong class="text-slate-900">Next action:</strong> ${titleForToken(item.next_action)}
          </div>
          <div class="mt-4 flex flex-wrap gap-3">
            <a class="rounded-full bg-visa-navy px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-slate-900/10 transition hover:-translate-y-0.5" href="${surfaceHref(item.surface, item.case_id)}">
              Resume ${titleForSurface(item.surface)}
            </a>
            <a class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5" href="./applicant-portal/?case=${encodeURIComponent(item.case_id)}">
              Applicant View
            </a>
            <a class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5" href="./officer-dashboard/?case=${encodeURIComponent(item.case_id)}">
              Officer View
            </a>
          </div>
        </article>
      `
    )
    .join("");
}

function surfaceHref(surface, caseId) {
  const encoded = encodeURIComponent(caseId);
  if (surface === "officer") {
    return `./officer-dashboard/?case=${encoded}`;
  }
  return `./applicant-portal/?case=${encoded}`;
}

function titleForSurface(surface) {
  return surface === "officer" ? "Officer Dashboard" : "Applicant Portal";
}

function titleForToken(value) {
  return String(value || "")
    .toLowerCase()
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(" ");
}

initialize();
