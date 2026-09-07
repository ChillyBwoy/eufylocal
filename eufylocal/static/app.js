"use strict";

const STATUS_BADGE_CLASSES = {
  idle: "badge-idle",
  scanning: "badge-scanning",
  connecting: "badge-scanning",
  connected: "badge-connected",
  error: "badge-error",
};

function formatTime(iso) {
  if (!iso) return "—";
  const date = new Date(iso);
  return date.toLocaleString();
}

function formatWeight(kg) {
  if (kg === null || kg === undefined) return "—";
  return kg.toFixed(2);
}

function renderStatus(snapshot) {
  const bluetooth = snapshot.bluetooth || {};
  const badge = document.getElementById("bluetooth-status");
  const status = bluetooth.status || "idle";

  badge.textContent = status;
  badge.className = "badge " + (STATUS_BADGE_CLASSES[status] || "badge-idle");

  document.getElementById("status-value").textContent = status;
  document.getElementById("device-value").textContent = bluetooth.device_name || "—";
  document.getElementById("device-id").textContent = bluetooth.device_id || "—";
  document.getElementById("error-value").textContent = bluetooth.last_error || "—";
}

function renderLatest(snapshot) {
  const latest = snapshot.last_measurement;
  const live = snapshot.bluetooth && snapshot.bluetooth.live_weight_kg;
  const liveActive = snapshot.bluetooth && snapshot.bluetooth.live_weight_active;

  if (liveActive && live !== null && live !== undefined) {
    document.getElementById("current-weight").textContent = formatWeight(live);
    document.getElementById("last-time").textContent = "live (unstable)";
  } else if (latest) {
    document.getElementById("current-weight").textContent = formatWeight(latest.weight_kg);
    document.getElementById("last-time").textContent = "measured at " + formatTime(latest.measured_at);
  } else {
    document.getElementById("current-weight").textContent = "—";
    document.getElementById("last-time").textContent = "no measurement yet";
  }
}

function renderMeasurements(measurements) {
  const body = document.getElementById("measurements-body");
  if (!measurements || measurements.length === 0) {
    body.innerHTML = '<tr><td colspan="5" class="muted">no measurements yet</td></tr>';
    return;
  }

  body.innerHTML = measurements
    .map(function (m) {
      return (
        "<tr>" +
        "<td>" + formatTime(m.measured_at) + "</td>" +
        "<td>" + formatWeight(m.weight_kg) + "</td>" +
        "<td>" + (m.impedance_ohm === null ? "—" : m.impedance_ohm.toFixed(1)) + "</td>" +
        "<td>" + m.source + "</td>" +
        "<td>" + m.device_id + "</td>" +
        "</tr>"
      );
    })
    .join("");
}

async function refresh() {
  try {
    const [statusRes, measurementsRes] = await Promise.all([
      fetch("/api/status"),
      fetch("/api/measurements?limit=50"),
    ]);
    const snapshot = await statusRes.json();
    const measurements = await measurementsRes.json();

    renderStatus(snapshot);
    renderLatest(snapshot);
    renderMeasurements(measurements.measurements);
  } catch (error) {
    const badge = document.getElementById("bluetooth-status");
    badge.textContent = "server unreachable";
    badge.className = "badge badge-error";
  }
}

refresh();
setInterval(refresh, 3000);
