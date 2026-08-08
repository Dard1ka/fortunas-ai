// Order publik + QRIS statis (Wave C area C) — acceptance dari
// public_order_controller_test.dart (9 test) + gate /order tanpa login.
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import PublicOrderScreen from './PublicOrderScreen.jsx';
import App from '../App.jsx';

const MENU = {
  code: 'KDS-001', name: 'Warung Dhoho', city: 'Kediri', address: 'Jl. Dhoho 12',
  products: [
    { id: 1, name: 'Nasi Goreng', description: '', image_url: null, category_id: null, stock: null, price: 15000 },
    { id: 2, name: 'Es Teh', description: '', image_url: null, category_id: null, stock: 2, price: 5000 },
    { id: 3, name: 'Kopi', description: '', image_url: null, category_id: null, stock: 0, price: 8000 },
    { id: 4, name: 'Roti', description: '', image_url: null, category_id: null, stock: null, price: null },
  ],
  count: 4,
};

const ORDER_PENDING = {
  id: 9, code: 'KDS-001', customer_name: 'Budi', customer_phone: '0812',
  items: [{ product_id: 1, name: 'Nasi Goreng', qty: 2, unit_price: 15000, subtotal: 30000 }],
  total: 30000, status: 'pending_payment', payment_provider: 'qris_static',
  payment_token: null, payment_redirect_url: '/public/orders/ORD-9-abc/confirm-payment',
  payment_order_id: 'ORD-9-abc', created_at: '2026-08-08T10:00:00', updated_at: null,
};
const ORDER_PAID = { ...ORDER_PENDING, status: 'paid' };

const json = (body, status = 200) => new Response(JSON.stringify(body), { status });

function stubApi({ statusAfterConfirm = ORDER_PAID } = {}) {
  const calls = [];
  vi.stubGlobal('fetch', vi.fn(async (url, opts = {}) => {
    const u = String(url);
    const method = opts.method || 'GET';
    calls.push({ url: u, method, body: opts.body, auth: opts.headers?.Authorization || null });
    if (u.startsWith('/api/public/umkm/') && u.endsWith('/orders') && method === 'POST') return json(ORDER_PENDING, 201);
    if (u.startsWith('/api/public/umkm/')) return json(MENU);
    if (u.endsWith('/confirm-payment') && method === 'POST') return json({ ok: true, status: 'paid', order_id: 9 });
    if (u.startsWith('/api/public/orders/') && method === 'GET') return json(statusAfterConfirm);
    return json({ detail: `unexpected ${method} ${u}` }, 500);
  }));
  return calls;
}

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
});

const ui = () => render(<MemoryRouter><PublicOrderScreen /></MemoryRouter>);

async function openMenu() {
  fireEvent.change(screen.getByTestId('public-order-code'), { target: { value: 'kds-001' } });
  fireEvent.click(screen.getByRole('button', { name: 'Lihat Menu' }));
  await screen.findByText('Warung Dhoho');
}

test('kode kosong → pesan lokal TANPA fetch', async () => {
  const calls = stubApi();
  ui();
  fireEvent.click(screen.getByRole('button', { name: 'Lihat Menu' }));
  expect(await screen.findByText('Masukkan kode UMKM dulu.')).toBeInTheDocument();
  expect(calls).toHaveLength(0);
});

test('loadMenu sukses: fase menu, kode di-trim, produk tampil dengan aturan orderable', async () => {
  const calls = stubApi();
  ui();
  await openMenu();
  expect(calls[0].url).toBe('/api/public/umkm/kds-001');
  expect(calls[0].auth).toBeNull(); // TANPA Bearer di /public/*
  expect(screen.getByText('Nasi Goreng')).toBeInTheDocument();
  expect(screen.getByText('Belum ada harga')).toBeInTheDocument();          // Roti price null
  expect(screen.getByRole('button', { name: 'Belum dijual' })).toBeDisabled();
  expect(screen.getByRole('button', { name: 'Habis' })).toBeDisabled();     // Kopi stock 0
});

test('increment dibatasi stok terlacak; decrement di 1 menghapus item', async () => {
  stubApi();
  ui();
  await openMenu();
  // Es Teh stock 2 → maksimal 2
  fireEvent.click(screen.getByTestId('menu-add-2'));
  fireEvent.click(screen.getByTestId('menu-inc-2'));
  fireEvent.click(screen.getByTestId('menu-inc-2')); // dihalangi
  expect(screen.getByTestId('menu-qty-2')).toHaveTextContent('2');
  expect(screen.getByText('2 item')).toBeInTheDocument();
  // decrement 2× → item hilang, cart bar hilang
  fireEvent.click(screen.getByTestId('menu-dec-2'));
  fireEvent.click(screen.getByTestId('menu-dec-2'));
  expect(screen.queryByText(/item/)).not.toBeInTheDocument();
  expect(screen.getByTestId('menu-add-2')).toBeInTheDocument();
});

test('cartTotal dihitung dari harga menu server', async () => {
  stubApi();
  ui();
  await openMenu();
  fireEvent.click(screen.getByTestId('menu-add-1')); // Nasi 15000
  fireEvent.click(screen.getByTestId('menu-inc-1')); // 2×
  fireEvent.click(screen.getByTestId('menu-add-2')); // Es Teh 5000
  expect(screen.getByText('3 item')).toBeInTheDocument();
  expect(screen.getByText('Rp 35.000')).toBeInTheDocument();
});

test('filter search: nama saja, empty state menyebut query', async () => {
  stubApi();
  ui();
  await openMenu();
  fireEvent.change(screen.getByTestId('public-order-search'), { target: { value: 'es' } });
  expect(screen.getByText('Es Teh')).toBeInTheDocument();
  expect(screen.queryByText('Roti')).not.toBeInTheDocument();
  fireEvent.change(screen.getByTestId('public-order-search'), { target: { value: 'zzz' } });
  expect(screen.getByText('Menu "zzz" tak ditemukan.')).toBeInTheDocument();
});

test('checkout: validasi nama & HP wajib, payload benar, fase order + QRIS', async () => {
  const calls = stubApi();
  ui();
  await openMenu();
  fireEvent.click(screen.getByTestId('menu-add-1'));
  fireEvent.click(screen.getByTestId('menu-inc-1'));
  fireEvent.click(screen.getByTestId('public-order-checkout'));

  // kosong → dua pesan validasi, tanpa POST
  fireEvent.click(screen.getByRole('button', { name: 'Buat pesanan & bayar' }));
  expect(await screen.findByText('Nama wajib diisi')).toBeInTheDocument();
  expect(screen.getByText('No. HP wajib diisi')).toBeInTheDocument();
  expect(calls.some((c) => c.method === 'POST')).toBe(false);

  fireEvent.change(screen.getByTestId('checkout-name'), { target: { value: '  Budi  ' } });
  fireEvent.change(screen.getByTestId('checkout-phone'), { target: { value: ' 0812 ' } });
  fireEvent.click(screen.getByRole('button', { name: 'Buat pesanan & bayar' }));

  await screen.findByText('Menunggu bayar');
  const post = calls.find((c) => c.method === 'POST');
  expect(post.url).toBe('/api/public/umkm/KDS-001/orders'); // kode dari state umkm, bukan input
  expect(JSON.parse(post.body)).toEqual({
    customer_name: 'Budi', customer_phone: '0812',
    items: [{ product_id: 1, qty: 2 }],
  });
  // blok QRIS hanya saat pending_payment
  expect(screen.getByText('Scan QRIS untuk bayar')).toBeInTheDocument();
  expect(screen.getByText(/Penjual akan memverifikasi pembayaran sebelum memproses pesanan/)).toBeInTheDocument();
  expect(screen.getByTestId('public-order-confirm-pay')).toBeInTheDocument();
});

test('Saya sudah bayar: POST confirm lalu GET status — state dari GET', async () => {
  const calls = stubApi();
  ui();
  await openMenu();
  fireEvent.click(screen.getByTestId('menu-add-1'));
  fireEvent.click(screen.getByTestId('public-order-checkout'));
  fireEvent.change(screen.getByTestId('checkout-name'), { target: { value: 'Budi' } });
  fireEvent.change(screen.getByTestId('checkout-phone'), { target: { value: '0812' } });
  fireEvent.click(screen.getByRole('button', { name: 'Buat pesanan & bayar' }));
  await screen.findByText('Menunggu bayar');

  fireEvent.click(screen.getByTestId('public-order-confirm-pay'));
  await screen.findByText('Sudah dibayar');
  expect(calls.some((c) => c.url === '/api/public/orders/ORD-9-abc/confirm-payment' && c.method === 'POST')).toBe(true);
  expect(calls.some((c) => c.url === '/api/public/orders/ORD-9-abc' && c.method === 'GET')).toBe(true);
  // QRIS hilang, tombol refresh muncul
  expect(screen.queryByText('Scan QRIS untuk bayar')).not.toBeInTheDocument();
  expect(screen.getByTestId('public-order-refresh')).toBeInTheDocument();
});

test('Pesan lagi di toko ini: kembali ke menu, keranjang kosong', async () => {
  stubApi();
  ui();
  await openMenu();
  fireEvent.click(screen.getByTestId('menu-add-1'));
  fireEvent.click(screen.getByTestId('public-order-checkout'));
  fireEvent.change(screen.getByTestId('checkout-name'), { target: { value: 'Budi' } });
  fireEvent.change(screen.getByTestId('checkout-phone'), { target: { value: '0812' } });
  fireEvent.click(screen.getByRole('button', { name: 'Buat pesanan & bayar' }));
  await screen.findByText('Menunggu bayar');

  fireEvent.click(screen.getByTestId('public-order-again'));
  expect(await screen.findByText('Warung Dhoho')).toBeInTheDocument();
  expect(screen.queryByText(/^\d+ item$/)).not.toBeInTheDocument();
});

test('gate App: /order terbuka TANPA token UMKM (tidak dilempar ke login)', async () => {
  stubApi();
  window.history.pushState({}, '', '/');
  render(
    <MemoryRouter initialEntries={['/order']}>
      <App />
    </MemoryRouter>,
  );
  expect(await screen.findByText('Masukkan kode UMKM')).toBeInTheDocument();
  expect(screen.queryByLabelText(/Email/i)).not.toBeInTheDocument();
});
