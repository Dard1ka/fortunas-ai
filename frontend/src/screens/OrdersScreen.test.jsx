// Inbox pesanan UMKM (Wave C area B) — acceptance dari orders_screen_test.dart
// (7 widget test) + order_controller_test.dart (5 unit test).
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import OrdersScreen from './OrdersScreen.jsx';

const ORDER_PAID = {
  id: 11, code: 'KDS-001', customer_name: 'Budi', customer_phone: '0812',
  items: [
    { product_id: 1, name: 'Kopi Susu', qty: 2, unit_price: 15000, subtotal: 30000 },
    { product_id: 2, name: 'Roti', qty: 1, unit_price: 8000, subtotal: 8000 },
  ],
  total: 38000, status: 'paid', payment_status: 'qris_manual_confirmed',
  paid_at: '2026-08-08T09:00:00', created_at: '2026-08-08T08:55:00', updated_at: null, stock_restored_at: null,
};
const ORDER_ACCEPTED = { ...ORDER_PAID, id: 12, customer_name: '', status: 'accepted' };
const ORDER_REFUNDED = { ...ORDER_PAID, id: 13, status: 'accepted', payment_status: 'refund' };

const json = (body, status = 200) => new Response(JSON.stringify(body), { status });

function stubApi(orders = [ORDER_PAID, ORDER_ACCEPTED]) {
  const calls = [];
  vi.stubGlobal('fetch', vi.fn(async (url, opts = {}) => {
    const u = String(url);
    const method = opts.method || 'GET';
    calls.push({ url: u, method });
    if (u.startsWith('/api/umkm/orders') && method === 'GET') return json({ orders, count: orders.length });
    if (/\/api\/umkm\/orders\/\d+\/(accept|reject|complete)$/.test(u)) return json({ ...ORDER_PAID, status: 'accepted' });
    return json({ detail: `unexpected ${method} ${u}` }, 500);
  }));
  return calls;
}

afterEach(() => vi.unstubAllGlobals());

const ui = () => render(<MemoryRouter><OrdersScreen /></MemoryRouter>);

test('tombol per status KETAT: paid → Terima+Tolak; accepted → Selesai saja', async () => {
  stubApi();
  ui();
  expect(await screen.findByText('Budi')).toBeInTheDocument();
  expect(screen.getByTestId('orders-accept-11')).toBeInTheDocument();
  expect(screen.getByTestId('orders-reject-11')).toBeInTheDocument();
  expect(screen.queryByTestId('orders-complete-11')).not.toBeInTheDocument();
  expect(screen.getByTestId('orders-complete-12')).toBeInTheDocument();
  expect(screen.queryByTestId('orders-accept-12')).not.toBeInTheDocument();
  // nama kosong → fallback "Pelanggan"
  expect(screen.getByText('Pelanggan')).toBeInTheDocument();
  // baris item pakai '×'
  expect(screen.getAllByText(/2× Kopi Susu/).length).toBeGreaterThan(0);
});

test('Terima → POST accept lalu reload dari server (non-optimistis)', async () => {
  const calls = stubApi();
  ui();
  await screen.findByText('Budi');
  const getsBefore = calls.filter((c) => c.method === 'GET').length;
  fireEvent.click(screen.getByTestId('orders-accept-11'));
  await waitFor(() => {
    expect(calls.some((c) => c.url === '/api/umkm/orders/11/accept')).toBe(true);
    expect(calls.filter((c) => c.method === 'GET').length).toBe(getsBefore + 1);
  });
});

test('Tolak wajib konfirmasi menyebut stok & uang manual; Batal = tanpa request', async () => {
  const calls = stubApi();
  ui();
  await screen.findByText('Budi');
  fireEvent.click(screen.getByTestId('orders-reject-11'));
  expect(await screen.findByText(/Stok 2 item akan dikembalikan otomatis/)).toBeInTheDocument();
  expect(screen.getByText(/Pengembalian uang ke pelanggan harus kamu lakukan manual/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Batal' }));
  expect(calls.some((c) => c.url.includes('/reject'))).toBe(false);

  fireEvent.click(screen.getByTestId('orders-reject-11'));
  fireEvent.click(screen.getByRole('button', { name: 'Tolak Pesanan' }));
  await waitFor(() => {
    expect(calls.some((c) => c.url === '/api/umkm/orders/11/reject')).toBe(true);
  });
});

test('peringatan refund hanya untuk payment_status refund/partial_refund/chargeback', async () => {
  stubApi([ORDER_PAID, ORDER_REFUNDED]);
  ui();
  expect(await screen.findByTestId('orders-refunded-13')).toBeInTheDocument();
  expect(screen.getByText(/Dana sudah dikembalikan ke pelanggan \(refund\)/)).toBeInTheDocument();
  expect(screen.queryByTestId('orders-refunded-11')).not.toBeInTheDocument();
});

test('empty state', async () => {
  stubApi([]);
  ui();
  expect(await screen.findByTestId('orders-empty')).toBeInTheDocument();
  expect(screen.getByText('Belum ada pesanan masuk.')).toBeInTheDocument();
  expect(screen.getByText(/Bagikan kode tokomu/)).toBeInTheDocument();
});

test('error load tampil inline', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => json({ detail: 'Server sibuk.' }, 500)));
  ui();
  expect(await screen.findByRole('alert')).toHaveTextContent('Server sibuk.');
});

test('busy per-kartu: saat satu kartu submitting, tombol kartu lain tetap aktif', async () => {
  let resolveAccept;
  const orders = [ORDER_PAID, ORDER_ACCEPTED];
  vi.stubGlobal('fetch', vi.fn(async (url, opts = {}) => {
    const u = String(url);
    if (/accept$/.test(u)) {
      await new Promise((r) => { resolveAccept = r; });
      return json(ORDER_PAID);
    }
    return json({ orders, count: 2 });
  }));
  ui();
  await screen.findByText('Budi');
  fireEvent.click(screen.getByTestId('orders-accept-11'));
  await waitFor(() => expect(screen.getByTestId('orders-accept-11')).toBeDisabled());
  expect(screen.getByTestId('orders-complete-12')).not.toBeDisabled();
  resolveAccept();
});
