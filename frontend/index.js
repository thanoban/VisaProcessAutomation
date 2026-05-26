import {
  buildStatusChip,
  clearStoredApiBaseUrl,
  createApiClient,
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
};

async function initialize() {
  elements.apiInput.value = getStoredApiBaseUrl();
  elements.apiForm.addEventListener("submit", handleSaveTarget);
  elements.resetButton.addEventListener("click", handleResetTarget);
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

initialize();
