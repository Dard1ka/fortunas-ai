// Multipart create produk (Wave C area A): FormData harus dikirim apa adanya
// TANPA Content-Type manual — browser yang menulis boundary. Kalau header
// diset manual, backend menolak dan errornya membingungkan (422/400).
import { api, setToken, clearToken } from './client.js';

beforeEach(() => {
  localStorage.clear();
  setToken('UMKM-TOKEN');
});
afterEach(() => {
  vi.unstubAllGlobals();
  clearToken();
});

test('createProduct mengirim FormData asli tanpa Content-Type manual', async () => {
  const seen = [];
  vi.stubGlobal('fetch', vi.fn(async (url, opts = {}) => {
    seen.push({ url: String(url), opts });
    return new Response(JSON.stringify({ id: 1, name: 'Kopi' }), { status: 201 });
  }));

  const fd = new FormData();
  fd.append('name', 'Kopi');
  fd.append('description', '');
  fd.append('image', new Blob(['x'], { type: 'image/png' }), 'produk.png');

  await api.createProduct(fd);

  expect(seen).toHaveLength(1);
  expect(seen[0].url).toBe('/api/umkm/products');
  expect(seen[0].opts.method).toBe('POST');
  expect(seen[0].opts.body).toBe(fd); // FormData diteruskan apa adanya
  expect(seen[0].opts.headers['Content-Type']).toBeUndefined();
  expect(seen[0].opts.headers.Authorization).toBe('Bearer UMKM-TOKEN');
});

test('body JSON biasa tetap di-stringify dengan Content-Type json', async () => {
  const seen = [];
  vi.stubGlobal('fetch', vi.fn(async (url, opts = {}) => {
    seen.push({ url: String(url), opts });
    return new Response(JSON.stringify({ id: 1 }), { status: 200 });
  }));

  await api.setStock(7, null);

  expect(seen[0].url).toBe('/api/umkm/products/7/stock');
  expect(seen[0].opts.method).toBe('PATCH');
  expect(seen[0].opts.body).toBe(JSON.stringify({ stock: null }));
  expect(seen[0].opts.headers['Content-Type']).toBe('application/json');
});
