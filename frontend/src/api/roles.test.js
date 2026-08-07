// Pemisahan token per-peran — regresi paling berbahaya di dual-auth:
// token UMKM bocor ke rute customer (atau sebaliknya), atau 401 satu peran
// menghapus sesi peran lain.
import { api, setToken, setCustomerToken, getToken, getCustomerToken, clearToken, clearCustomerToken } from './client.js';

function stubFetch(status = 200, body = {}) {
  const seen = [];
  vi.stubGlobal('fetch', vi.fn(async (url, opts = {}) => {
    seen.push({ url: String(url), auth: opts.headers?.Authorization || null });
    return new Response(JSON.stringify(body), { status });
  }));
  return seen;
}

beforeEach(() => {
  localStorage.clear();
  setToken('UMKM-TOKEN');
  setCustomerToken('CUST-TOKEN');
});
afterEach(() => {
  vi.unstubAllGlobals();
  clearToken();
  clearCustomerToken();
});

test('rute customer memakai token customer, BUKAN token UMKM', async () => {
  const seen = stubFetch(200, { username: 'x', total_points: 0, memberships: [] });
  await api.customerHome();
  expect(seen[0].auth).toBe('Bearer CUST-TOKEN');
});

test('rute UMKM (scan) memakai token UMKM', async () => {
  const seen = stubFetch(200, { valid: true });
  await api.scanValidate('tok-1234567890');
  expect(seen[0].auth).toBe('Bearer UMKM-TOKEN');
});

test('401 pada rute customer TIDAK menghapus sesi UMKM', async () => {
  stubFetch(401, { detail: 'expired' });
  await expect(api.customerHome()).rejects.toThrow();
  expect(getCustomerToken()).toBe('');
  expect(getToken()).toBe('UMKM-TOKEN');
});

test('401 pada rute UMKM TIDAK menghapus sesi customer', async () => {
  stubFetch(401, { detail: 'expired' });
  await expect(api.me()).rejects.toThrow();
  expect(getToken()).toBe('');
  expect(getCustomerToken()).toBe('CUST-TOKEN');
});
