// Katalog produk (Wave C area A) — acceptance dipetakan dari test Flutter:
// products_screen_test (badge stok, dialog kosong→null, Batal=no-op),
// products_categories_test (dropdown seed, chip kategori),
// categories_manage_test (tambah/hapus + konfirmasi dampak).
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ProductsScreen from './ProductsScreen.jsx';

const PRODUCTS = {
  products: [
    { id: 1, tenant_id: 1, name: 'Sabun Cuci', description: 'Sabun andalan', stock_code: 'sa-001', image_url: '/media/products/1/aaaa.jpg', stock: null, price: null, category_id: null, created_at: '2026-08-01' },
    { id: 2, tenant_id: 1, name: 'Kopi Susu', description: '', stock_code: 'ko-001', image_url: '/media/products/1/bbbb.jpg', stock: 0, price: 15000, category_id: 1, created_at: '2026-08-01' },
    { id: 3, tenant_id: 1, name: 'Teh Kotak', description: '', stock_code: 'te-001', image_url: '/media/products/1/cccc.jpg', stock: 3, price: 4500, category_id: null, created_at: '2026-08-01' },
    { id: 4, tenant_id: 1, name: 'Beras 5kg', description: '', stock_code: 'be-001', image_url: '/media/products/1/dddd.jpg', stock: 7, price: 68000, category_id: 2, created_at: '2026-08-01' },
  ],
  count: 4,
  needs_onboarding: false,
};
const CATEGORIES = { categories: [{ id: 1, tenant_id: 1, name: 'Kopi', created_at: '' }, { id: 2, tenant_id: 1, name: 'Sembako', created_at: '' }], count: 2 };

const json = (body, status = 200) => new Response(JSON.stringify(body), { status });

function stubApi({ products = PRODUCTS, categories = CATEGORIES, autoCategorize = { status: 'ok', categorized: 3, total_uncategorized: 3 } } = {}) {
  const calls = [];
  vi.stubGlobal('fetch', vi.fn(async (url, opts = {}) => {
    const u = String(url);
    const method = opts.method || 'GET';
    calls.push({ url: u, method, body: opts.body });
    if (u === '/api/umkm/products' && method === 'GET') return json(products);
    if (u === '/api/umkm/products' && method === 'POST') return json({ id: 99, name: 'Baru' }, 201);
    if (u === '/api/umkm/products/auto-categorize') return json(autoCategorize);
    if (/\/api\/umkm\/products\/\d+\/stock$/.test(u)) return json({ id: 4 });
    if (/\/api\/umkm\/products\/\d+\/price$/.test(u)) return json({ id: 4 });
    if (/\/api\/umkm\/products\/\d+$/.test(u) && method === 'DELETE') return json({ status: 'ok', deleted: 1 });
    if (u === '/api/umkm/categories' && method === 'GET') return json(categories);
    if (u === '/api/umkm/categories' && method === 'POST') return json({ id: 9, name: 'Teh' }, 201);
    if (/\/api\/umkm\/categories\/\d+$/.test(u) && method === 'DELETE') return json({ status: 'ok', deleted: true, reassigned: 1 });
    return json({ detail: `unexpected ${method} ${u}` }, 500);
  }));
  return calls;
}

afterEach(() => vi.unstubAllGlobals());

const ui = () => render(<MemoryRouter><ProductsScreen /></MemoryRouter>);

test('list: 4 varian badge stok + badge harga + chip kategori ter-resolve', async () => {
  stubApi();
  ui();
  expect(await screen.findByText('Sabun Cuci')).toBeInTheDocument();
  expect(screen.getByText('Tak dilacak')).toBeInTheDocument();       // stock null
  expect(screen.getByText('Habis')).toBeInTheDocument();             // stock 0
  expect(screen.getByText('Menipis')).toBeInTheDocument();           // stock 3 (<=5)
  expect(screen.getByText('Stok: 7')).toBeInTheDocument();           // stock 7
  expect(screen.getByText('Harga belum diset')).toBeInTheDocument(); // price null
  expect(screen.getByText('Rp 15.000')).toBeInTheDocument();
  expect(screen.getByText('Kopi')).toBeInTheDocument();              // chip kategori (id 1)
  expect(screen.getAllByText('Tanpa kategori').length).toBeGreaterThan(0);
  expect(screen.getByText('SA-001')).toBeInTheDocument();            // kode barang uppercase
});

test('needs_onboarding: banner wajib produk tampil, "Belum ada produk." disembunyikan', async () => {
  stubApi({ products: { products: [], count: 0, needs_onboarding: true } });
  ui();
  expect(await screen.findByText(/wajib menambahkan minimal 1 produk/)).toBeInTheDocument();
  expect(screen.queryByText('Belum ada produk.')).not.toBeInTheDocument();
});

test('banner auto-kategori: muncul hanya bila ada produk tanpa kategori, klik → pesan hasil', async () => {
  const calls = stubApi();
  ui();
  expect(await screen.findByTestId('auto-categorize-banner')).toBeInTheDocument();
  expect(screen.getByText(/2 produk belum berkategori/)).toBeInTheDocument(); // p1 & p3
  fireEvent.click(screen.getByRole('button', { name: /Kelompokkan dengan AI/ }));
  expect(await screen.findByText(/AI mengelompokkan 3 produk/)).toBeInTheDocument();
  expect(calls.some((c) => c.url.endsWith('/auto-categorize'))).toBe(true);
});

test('form: validasi nama → gambar, submit valid mengirim FormData minim (tanpa stock null)', async () => {
  const calls = stubApi();
  URL.createObjectURL = vi.fn(() => 'blob:preview');
  URL.revokeObjectURL = vi.fn();
  ui();
  fireEvent.click(await screen.findByTestId('product-add-fab'));

  // 1. nama kosong
  fireEvent.click(screen.getByRole('button', { name: /SIMPAN PRODUK/ }));
  expect(await screen.findByText('Nama produk wajib diisi.')).toBeInTheDocument();

  // 2. nama ada, gambar belum
  fireEvent.change(screen.getByLabelText(/Nama produk/), { target: { value: 'Kopi Hitam' } });
  fireEvent.click(screen.getByRole('button', { name: /SIMPAN PRODUK/ }));
  expect(await screen.findByText('Gambar produk wajib dipilih.')).toBeInTheDocument();
  expect(calls.some((c) => c.method === 'POST' && c.url === '/api/umkm/products')).toBe(false);

  // 3. lengkap → FormData
  const file = new File(['x'], 'foto.png', { type: 'image/png' });
  fireEvent.change(screen.getByTestId('product-pick-image'), { target: { files: [file] } });
  fireEvent.click(screen.getByRole('button', { name: /SIMPAN PRODUK/ }));
  await waitFor(() => {
    expect(calls.some((c) => c.method === 'POST' && c.url === '/api/umkm/products')).toBe(true);
  });
  const post = calls.find((c) => c.method === 'POST' && c.url === '/api/umkm/products');
  expect(post.body).toBeInstanceOf(FormData);
  expect(post.body.get('name')).toBe('Kopi Hitam');
  expect(post.body.get('image')).toBeTruthy();
  expect(post.body.has('stock')).toBe(false);      // kosong = TIDAK dikirim (null)
  expect(post.body.has('price')).toBe(false);
  expect(post.body.has('category_id')).toBe(false);
  expect(await screen.findByText('Produk berhasil ditambahkan.')).toBeInTheDocument();
});

test('dialog stok: kosongkan field → PATCH {stock:null}; Batal → tanpa request', async () => {
  const calls = stubApi();
  ui();
  await screen.findByText('Beras 5kg');

  // Batal dulu
  fireEvent.click(screen.getByTestId('product-edit-stock-4'));
  fireEvent.click(screen.getByRole('button', { name: 'Batal' }));
  expect(calls.some((c) => c.url.includes('/stock'))).toBe(false);

  // Kosongkan → null
  fireEvent.click(screen.getByTestId('product-edit-stock-4'));
  const field = screen.getByTestId('edit-stock-field');
  expect(field.value).toBe('7');
  fireEvent.change(field, { target: { value: '' } });
  fireEvent.click(screen.getByTestId('edit-stock-save'));
  await waitFor(() => {
    const patch = calls.find((c) => c.url === '/api/umkm/products/4/stock');
    expect(patch).toBeTruthy();
    expect(JSON.parse(patch.body)).toEqual({ stock: null });
  });
});

test('dialog harga: isi nilai → PATCH {price:9000}', async () => {
  const calls = stubApi();
  ui();
  await screen.findByText('Sabun Cuci');
  fireEvent.click(screen.getByTestId('product-edit-price-1'));
  fireEvent.change(screen.getByTestId('edit-price-field'), { target: { value: '9000' } });
  fireEvent.click(screen.getByTestId('edit-price-save'));
  await waitFor(() => {
    const patch = calls.find((c) => c.url === '/api/umkm/products/1/price');
    expect(JSON.parse(patch.body)).toEqual({ price: 9000 });
  });
});

test('hapus produk: konfirmasi dulu (deviasi sadar dari Flutter), Batal = no-op', async () => {
  const calls = stubApi();
  ui();
  await screen.findByText('Sabun Cuci');

  fireEvent.click(screen.getByTestId('product-delete-1'));
  fireEvent.click(screen.getByRole('button', { name: 'Batal' }));
  expect(calls.some((c) => c.method === 'DELETE')).toBe(false);

  fireEvent.click(screen.getByTestId('product-delete-1'));
  const dialog = screen.getByRole('dialog');
  fireEvent.click(within(dialog).getByRole('button', { name: 'Hapus' }));
  await waitFor(() => {
    expect(calls.some((c) => c.method === 'DELETE' && c.url === '/api/umkm/products/1')).toBe(true);
  });
});

test('kelola kategori: tambah (trim), hapus dengan konfirmasi menyebut dampak', async () => {
  const calls = stubApi();
  ui();
  await screen.findByText('Sabun Cuci');
  fireEvent.click(screen.getByTestId('products-manage-categories'));

  // tambah — nama di-trim
  fireEvent.change(screen.getByLabelText('Nama kategori baru'), { target: { value: '  Teh  ' } });
  fireEvent.click(screen.getByRole('button', { name: 'Tambah' }));
  await waitFor(() => {
    const post = calls.find((c) => c.method === 'POST' && c.url === '/api/umkm/categories');
    expect(JSON.parse(post.body)).toEqual({ name: 'Teh' });
  });

  // hapus kategori 1 → p2 terdampak (1 produk)
  fireEvent.click(screen.getByTestId('category-delete-1'));
  expect(await screen.findByText('1 produk akan jadi tanpa kategori.')).toBeInTheDocument();
  fireEvent.click(screen.getByTestId('category-delete-confirm'));
  await waitFor(() => {
    expect(calls.some((c) => c.method === 'DELETE' && c.url === '/api/umkm/categories/1')).toBe(true);
  });
});

test('kategori: input kosong → diam (tanpa request)', async () => {
  const calls = stubApi();
  ui();
  await screen.findByText('Sabun Cuci');
  fireEvent.click(screen.getByTestId('products-manage-categories'));
  fireEvent.click(screen.getByRole('button', { name: 'Tambah' }));
  expect(calls.some((c) => c.method === 'POST' && c.url === '/api/umkm/categories')).toBe(false);
});
