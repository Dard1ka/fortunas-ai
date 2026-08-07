// Fortunas backend client. All requests go through Vite proxy (/api/* → :8000).

import { humanizeError } from './errors.js';
import { recordLatency } from './latency.js';

const BASE = '/api';
const TOKEN_KEY = 'fortunas_token';
const PREFIX_KEY = 'fortunas_prefix';
// Kunci token customer SENGAJA terpisah dari token UMKM (dua peran, dua JWT
// backend berbeda) — interceptor tidak boleh cross-attach; ada test yang
// menjaganya (src/api/roles.test.js).
const CUSTOMER_TOKEN_KEY = 'fortunas_customer_token';

// ── Auth token UMKM (JWT) di localStorage ─────────────────────────
export function getToken() {
  try { return localStorage.getItem(TOKEN_KEY) || ''; } catch { return ''; }
}
export function setToken(token) {
  try { localStorage.setItem(TOKEN_KEY, token); } catch { /* ignore */ }
}
export function clearToken() {
  try { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(PREFIX_KEY); } catch { /* ignore */ }
}

// ── Auth token CUSTOMER (JWT terpisah) ────────────────────────────
export function getCustomerToken() {
  try { return localStorage.getItem(CUSTOMER_TOKEN_KEY) || ''; } catch { return ''; }
}
export function setCustomerToken(token) {
  try { localStorage.setItem(CUSTOMER_TOKEN_KEY, token); } catch { /* ignore */ }
}
export function clearCustomerToken() {
  try { localStorage.removeItem(CUSTOMER_TOKEN_KEY); } catch { /* ignore */ }
}

// ── Tenant prefix (untuk namespace data lokal per-bisnis, mis. riwayat voice) ──
export function setPrefix(prefix) {
  try { localStorage.setItem(PREFIX_KEY, prefix || ''); } catch { /* ignore */ }
}
export function getPrefix() {
  try { return localStorage.getItem(PREFIX_KEY) || ''; } catch { return ''; }
}
// Key riwayat voice DIPISAH per tenant supaya tidak tercampur antar bisnis.
export function voiceHistoryKey() {
  return `fortunas_voice_${getPrefix() || 'anon'}`;
}

async function request(path, { method = 'GET', body, signal, trackLatency = false, auth = true, role = 'umkm' } = {}) {
  const started = trackLatency ? performance.now() : 0;
  const headers = {};
  if (body) headers['Content-Type'] = 'application/json';
  const token = role === 'customer' ? getCustomerToken() : getToken();
  if (auth && token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      signal,
      headers: Object.keys(headers).length ? headers : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    if (err?.name === 'AbortError') throw err;
    throw new Error(humanizeError(err, 0) || 'Tidak dapat terhubung ke server.');
  }

  if (trackLatency) recordLatency(performance.now() - started);

  if (!res.ok) {
    // Token invalid/kedaluwarsa → logout otomatis PER PERAN — 401 customer
    // TIDAK boleh menghapus sesi UMKM (dan sebaliknya).
    if (res.status === 401 && auth) {
      if (role === 'customer') {
        clearCustomerToken();
        window.dispatchEvent(new Event('customer:logout'));
      } else {
        clearToken();
        window.dispatchEvent(new Event('auth:logout'));
      }
    }
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
  health:       (signal)              => request('/health', { signal, auth: false }),
  analyses:     (signal)              => request('/analyses', { signal, auth: false }),
  // ── Auth ──
  register:     (payload, signal)     => request('/auth/register', { method: 'POST', body: payload, signal, auth: false }),
  login:        (payload, signal)     => request('/auth/login', { method: 'POST', body: payload, signal, auth: false }),
  me:           (signal)              => request('/auth/me', { signal }),
  updateAddress: (address, signal)    =>
    request('/umkm/address', { method: 'PUT', body: { address }, signal }),
  // ── Data (butuh token) ──
  ask:          (question, signal)    =>
    request('/ask', { method: 'POST', body: { question }, signal, trackLatency: true }),
  briefing:     (signal)              => request('/briefing', { signal, trackLatency: true }),
  reportDaily:  (signal)              => request('/report/daily', { signal }),
  umkmTransactions: (limit = 200, signal) => request(`/umkm/transactions?limit=${limit}`, { signal }),
  reportRun:    (signal)              => request('/report/daily/run', { method: 'POST', signal, trackLatency: true }),
  // ── Customer (peran terpisah — Bearer = customer token) ──
  customerBootstrap: (payload, signal) =>
    request('/customer/auth/bootstrap', { method: 'POST', body: payload, signal, auth: false }),
  customerHome: (signal)              => request('/customer/home', { signal, role: 'customer' }),
  customerQrSession: (signal)         =>
    request('/customer/qr/session', { method: 'POST', signal, role: 'customer' }),
  scanValidate: (token, signal)       =>
    request('/umkm/customer/scan/validate', { method: 'POST', body: { customer_qr_token: token }, signal }),
  getDpa:       (signal)             => request('/umkm/dpa', { signal }),
  putDpa:       (payload, signal)    =>
    request('/umkm/dpa', { method: 'PUT', body: payload, signal }),
  checkoutConfirm: (payload, signal) =>
    request('/checkout/confirm', { method: 'POST', body: payload, signal, trackLatency: true }),
  productsSearch: (q, signal) =>
    request(`/umkm/products/search?q=${encodeURIComponent(q)}`, { signal }),
  voiceParse:   (transcript, signal)  =>
    request('/voice/parse', { method: 'POST', body: { transcript }, signal }),
  // /voice/transaction: jalur tulis legacy backend — UI kini menulis lewat
  // /checkout/confirm (K5, ADR-0002); method client-nya dihapus (nol pemakai).
};
