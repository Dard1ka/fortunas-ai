// Lightweight latency tracker — average of last N samples.
// Used to set realistic expectations on the loading screen ("~5 detik").

const KEY = 'fortunas.latencies.v1';
const MAX_SAMPLES = 5;

function readJSON(fallback = []) {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function writeJSON(value) {
  try {
    localStorage.setItem(KEY, JSON.stringify(value));
  } catch {
    /* quota or disabled — non-fatal */
  }
}

export function recordLatency(ms) {
  const arr = readJSON();
  const next = [...arr, ms].slice(-MAX_SAMPLES);
  writeJSON(next);
  return next;
}

export function formatLatencyRange() {
  const samples = readJSON();
  if (!samples.length) return null;
  const avg = samples.reduce((a, b) => a + b, 0) / samples.length;
  const seconds = Math.round(avg / 1000);
  if (seconds <= 0) return null;
  return `~${seconds} detik`;
}
