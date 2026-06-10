// Fortunas backend client. All requests go through Vite proxy (/api/* → :8000).

import { humanizeError } from './errors.js';
import { recordLatency } from './latency.js';

const BASE = '/api';

async function request(path, { method = 'GET', body, signal, trackLatency = false } = {}) {
  const started = trackLatency ? performance.now() : 0;
  let res;
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      signal,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    throw new Error(humanizeError(err, 0));
  }

  if (trackLatency) recordLatency(performance.now() - started);

  if (!res.ok) {
    let detail = '';
    try {
      const data = await res.json();
      detail = data?.detail || data?.message || '';
    } catch { /* ignore */ }
    const err = new Error(detail || humanizeError(null, res.status));
    err.status = res.status;
    throw err;
  }

  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  health:       (signal)              => request('/health', { signal }),
  ask:          (question, signal)    =>
    request('/ask', { method: 'POST', body: { question }, signal, trackLatency: true }),
  briefing:     (signal)              => request('/briefing', { signal, trackLatency: true }),
  reportDaily:  (signal)              => request('/report/daily', { signal }),
  reportRun:    (signal)              => request('/report/daily/run', { method: 'POST', signal, trackLatency: true }),
  voiceParse:   (transcript, signal)  =>
    request('/voice/parse', { method: 'POST', body: { transcript }, signal }),
  voiceTransaction: (payload, signal) =>
    request('/voice/transaction', { method: 'POST', body: payload, signal }),
};
