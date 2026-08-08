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

// ── /public/* — jalur pelanggan anonim (Wave C). Paritas auth_interceptor
// Flutter: Bearer TIDAK PERNAH menempel di path /public/, walau token UMKM
// dan customer dua-duanya ada di localStorage.
test('rute /public/* TIDAK membawa Authorization walau kedua token ada', async () => {
  const seen = stubFetch(200, { code: 'KDS-001', name: 'Toko', products: [], count: 0 });
  await api.getPublicUmkm('KDS-001');
  await api.getPublicOrderStatus('ORD-1-abc');
  expect(seen).toHaveLength(2);
  expect(seen[0].auth).toBeNull();
  expect(seen[1].auth).toBeNull();
});

test('createPublicOrder & confirm-payment juga tanpa Authorization', async () => {
  const seen = stubFetch(201, { id: 1, status: 'pending_payment' });
  await api.createPublicOrder('KDS-001', {
    customer_name: 'Budi', customer_phone: '08123', items: [{ product_id: 1, qty: 2 }],
  });
  await api.confirmPublicOrderPayment('ORD-1-abc');
  expect(seen[0].auth).toBeNull();
  expect(seen[1].auth).toBeNull();
});

test('401 dari /public/* TIDAK menghapus sesi siapa pun', async () => {
  stubFetch(401, { detail: 'nope' });
  await expect(api.getPublicUmkm('XXX-999')).rejects.toThrow();
  expect(getToken()).toBe('UMKM-TOKEN');
  expect(getCustomerToken()).toBe('CUST-TOKEN');
});

test('endpoint customer Wave C memakai token customer', async () => {
  const seen = stubFetch(200, { promos: [], balance: 0, recent: [], transactions: [] });
  await api.customerPoints();
  await api.customerPromos();
  await api.customerGeneratePromo(3);
  await api.customerTransactions();
  for (const call of seen) expect(call.auth).toBe('Bearer CUST-TOKEN');
});

test('endpoint UMKM Wave C (produk/orders) memakai token UMKM', async () => {
  const seen = stubFetch(200, { products: [], orders: [], categories: [], count: 0 });
  await api.listProducts();
  await api.listOrders('paid');
  expect(seen[0].auth).toBe('Bearer UMKM-TOKEN');
  expect(seen[1].auth).toBe('Bearer UMKM-TOKEN');
  expect(seen[1].url).toContain('/umkm/orders?status=paid');
});
