// Loyalty customer (Wave C area D): poin, riwayat, promo spin wheel, home
// penuh, nav 5 tab. Flutter TIDAK punya test untuk layar-layar ini — suite ini
// ditulis dari aturan bisnis inventaris (area-loyalty-promo & riwayat).
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import CustomerApp from './CustomerApp.jsx';
import CustomerPointsScreen from './CustomerPointsScreen.jsx';
import CustomerHistoryScreen from './CustomerHistoryScreen.jsx';
import { segmentIndexForAmount } from './promoWheel.js';
import { setCustomerToken, clearCustomerToken, clearToken } from '../api/client.js';

vi.mock('qrcode', () => ({
  toDataURL: vi.fn(async () => 'data:image/png;base64,QRDUMMY'),
}));

const HOME = {
  username: 'Sari', total_points: 42,
  memberships: [{ tenant_id: 3, tenant_name: 'Warung Dhoho', member_since: '2026-07-01' }],
  last_transaction: { Invoice: 'INV-1', Description: 'Kopi Susu', Quantity: 2, Price: 15000, InvoiceDate: '2026-08-07T09:00:00', tenant_id: 3, tenant_name: 'Warung Dhoho' },
  last_promo: { promo_id: 'pr_1', tenant_id: 3, name: 'Diskon Rp25.000 untuk Kopi', code: 'FTN-A1B2C3', description: '', discount_amount: 25000, target_product: 'Kopi Susu', status: 'generated', points_cost: 30, generated_at: '2026-08-01', expires_at: '2026-08-15T00:00:00', redeemed_at: null, qr_payload: null },
};

const POINTS = {
  customer_user_id: 'cu-9', balance: 42,
  recent: [
    { event_type: 'earn', points_delta: 12, invoice: 'INV-9', promo_id: null, tenant_id: 3, created_at: '2026-08-07T10:00:00' },
    { event_type: 'redeem', points_delta: -30, invoice: null, promo_id: 'pr_1', tenant_id: 3, created_at: '2026-08-06T10:00:00' },
    { event_type: 'expire', points_delta: -2, invoice: null, promo_id: null, tenant_id: null, created_at: '2026-08-05T10:00:00' },
    { event_type: 'adjust', points_delta: 0, invoice: null, promo_id: null, tenant_id: null, created_at: '2026-08-04T10:00:00' },
  ],
};

const TXS = {
  status: 'ok', message: '',
  transactions: [
    { Invoice: 'INV-1', Description: 'Kopi Susu', Quantity: 2, Price: 15000, InvoiceDate: '2026-08-07T09:00:00', tenant_id: 3, tenant_name: 'Warung Dhoho' },
    { Invoice: 'INV-2', Description: 'Roti Bakar', Quantity: 1, Price: 8000, InvoiceDate: '2026-08-06T09:00:00', tenant_id: 3, tenant_name: 'Warung Dhoho' },
  ],
};

const PROMO_RESP = {
  promo: { promo_id: 'pr_2', tenant_id: 3, name: 'Diskon Rp50.000 buat kamu', code: 'FTN-XYZ123', description: '', discount_amount: 50000, target_product: null, status: 'generated', points_cost: 30, generated_at: '2026-08-08', expires_at: '2026-08-15T00:00:00', redeemed_at: null, qr_payload: 'jwt-promo-payload' },
  spin_result: { discount_amount: 50000, probability: 0.1 },
};

const json = (body, status = 200) => new Response(JSON.stringify(body), { status });

function stubApi({ generateStatus = 200, generateBody = PROMO_RESP } = {}) {
  const calls = [];
  vi.stubGlobal('fetch', vi.fn(async (url, opts = {}) => {
    const u = String(url);
    const method = opts.method || 'GET';
    // Browser nyata menolak signal non-AbortSignal dengan TypeError — jsdom
    // stub tidak; tiru validasinya supaya bug onClick={load} tertangkap test.
    if (opts.signal != null && !(opts.signal instanceof AbortSignal)) {
      throw new TypeError("Failed to execute 'fetch': member signal is not of type AbortSignal.");
    }
    calls.push({ url: u, method, body: opts.body });
    if (u === '/api/customer/home') return json(HOME);
    if (u === '/api/customer/points') return json(POINTS);
    if (u === '/api/customer/transactions') return json(TXS);
    if (u === '/api/customer/promos/generate') {
      return generateStatus === 200 ? json(generateBody) : json({ detail: 'Poin belum cukup: butuh 30, saldo kamu 12.' }, generateStatus);
    }
    if (u === '/api/customer/promos') return json({ promos: [] });
    return json({ detail: `unexpected ${method} ${u}` }, 500);
  }));
  return calls;
}

beforeEach(() => setCustomerToken('CUST-JWT'));
afterEach(() => {
  vi.unstubAllGlobals();
  clearCustomerToken();
  clearToken();
  localStorage.clear();
});

test('poin: saldo, 4 label event BI, tanda +/− (nol = earn), tanggal YYYY-MM-DD', async () => {
  stubApi();
  render(<MemoryRouter><CustomerPointsScreen /></MemoryRouter>);
  expect(await screen.findByText('42')).toBeInTheDocument();
  expect(screen.getByText('Poin dari transaksi')).toBeInTheDocument();
  expect(screen.getByText('Tukar untuk promo')).toBeInTheDocument();
  expect(screen.getByText('Poin kedaluwarsa')).toBeInTheDocument();
  expect(screen.getByText('Penyesuaian')).toBeInTheDocument(); // adjust → default
  expect(screen.getByText('+12')).toBeInTheDocument();
  expect(screen.getByText('-30')).toBeInTheDocument();  // negatif bawa tanda sendiri
  expect(screen.getByText('+0')).toBeInTheDocument();    // nol dihitung earn
  expect(screen.getByText(/Invoice INV-9 · 2026-08-07/)).toBeInTheDocument();
});

test('poin: ledger kosong → "Belum ada aktivitas poin."', async () => {
  stubApi();
  vi.stubGlobal('fetch', vi.fn(async () => json({ ...POINTS, recent: [] })));
  render(<MemoryRouter><CustomerPointsScreen /></MemoryRouter>);
  expect(await screen.findByText('Belum ada aktivitas poin.')).toBeInTheDocument();
});

test('riwayat: baris render apa adanya + subjudul join " · "', async () => {
  stubApi();
  render(<MemoryRouter><CustomerHistoryScreen /></MemoryRouter>);
  expect(await screen.findByText('Kopi Susu')).toBeInTheDocument();
  expect(screen.getByText('Warung Dhoho · x2 · 2026-08-07')).toBeInTheDocument();
  expect(screen.getByText('Rp 15.000')).toBeInTheDocument();
  expect(screen.getByText('Roti Bakar')).toBeInTheDocument();
});

test('riwayat kosong: pakai message server dulu (BQ best-effort ≠ gagal)', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => json({ status: 'ok', message: 'Belum ada transaksi (atau data belum tersedia).', transactions: [] })));
  render(<MemoryRouter><CustomerHistoryScreen /></MemoryRouter>);
  expect(await screen.findByText('Belum ada transaksi (atau data belum tersedia).')).toBeInTheDocument();
});

test('home penuh: promo terakhir (label BI), transaksi terakhir, tombol Buat Promo → spin wheel', async () => {
  stubApi();
  render(<MemoryRouter initialEntries={['/customer/home']}><CustomerApp /></MemoryRouter>);
  expect(await screen.findByTestId('home-last-promo')).toBeInTheDocument();
  expect(screen.getByText(/Kode FTN-A1B2C3 · Aktif/)).toBeInTheDocument(); // BUKAN 'generated' mentah
  expect(screen.getByText('Rp 25.000')).toBeInTheDocument();
  expect(screen.getByTestId('home-last-tx')).toBeInTheDocument();

  fireEvent.click(screen.getByTestId('home-make-promo-3'));
  expect(await screen.findByTestId('promo-spin')).toBeInTheDocument();
  expect(await screen.findByText('Warung Dhoho')).toBeInTheDocument();
});

test('spin: hasil dari server, kartu menang menampilkan kode + QR + expiry; klik dobel = satu POST', async () => {
  const calls = stubApi();
  render(<MemoryRouter initialEntries={['/customer/promo/3']}><CustomerApp /></MemoryRouter>);
  const btn = await screen.findByTestId('promo-spin');
  fireEvent.click(btn);
  fireEvent.click(btn); // guard re-entrancy

  expect(await screen.findByTestId('promo-won-card')).toBeInTheDocument();
  expect(screen.getByText('Diskon Rp50.000 buat kamu')).toBeInTheDocument();
  expect(screen.getByText('Kode: FTN-XYZ123')).toBeInTheDocument();
  expect(screen.getByText(/berlaku s\/d 2026-08-15/)).toBeInTheDocument();
  await waitFor(() => expect(screen.getByAltText('QR promo')).toBeInTheDocument());

  const posts = calls.filter((c) => c.url === '/api/customer/promos/generate' && c.method === 'POST');
  expect(posts).toHaveLength(1);
  expect(JSON.parse(posts[0].body)).toEqual({ tenant_id: 3 });
  // tombol putar DIGANTI kartu hadiah — tidak ada spin kedua
  expect(screen.queryByTestId('promo-spin')).not.toBeInTheDocument();
});

test('spin gagal 422: detail server tampil apa adanya, tombol aktif lagi', async () => {
  stubApi({ generateStatus: 422 });
  render(<MemoryRouter initialEntries={['/customer/promo/3']}><CustomerApp /></MemoryRouter>);
  fireEvent.click(await screen.findByTestId('promo-spin'));
  expect(await screen.findByText('Poin belum cukup: butuh 30, saldo kamu 12.')).toBeInTheDocument();
  expect(screen.getByTestId('promo-spin')).not.toBeDisabled();
});

test('promo tenant tak dikenal → redirect diam ke home', async () => {
  stubApi();
  render(<MemoryRouter initialEntries={['/customer/promo/999']}><CustomerApp /></MemoryRouter>);
  expect(await screen.findByText(/Toko yang kamu ikuti/)).toBeInTheDocument();
});

test('nav 5 tab: Beranda · Riwayat · QR Saya · Poin · Profil', async () => {
  stubApi();
  render(<MemoryRouter initialEntries={['/customer/home']}><CustomerApp /></MemoryRouter>);
  const nav = await screen.findByTestId('customer-nav');
  for (const label of ['Beranda', 'Riwayat', 'QR Saya', 'Poin', 'Profil']) {
    expect(nav).toHaveTextContent(label);
  }
});

test('menu: tile QR + Poin & Promo ada, kalimat placeholder lama HILANG', async () => {
  stubApi();
  render(<MemoryRouter initialEntries={['/customer/menu']}><CustomerApp /></MemoryRouter>);
  expect(await screen.findByTestId('menu-tile-qr')).toBeInTheDocument();
  expect(screen.getByTestId('menu-tile-points')).toBeInTheDocument();
  expect(screen.queryByText(/menyusul di pembaruan berikutnya/)).not.toBeInTheDocument();
});

test('tombol Muat ulang poin & riwayat memicu fetch ULANG yang valid (regresi onClick={load})', async () => {
  const calls = stubApi();
  render(<MemoryRouter><CustomerPointsScreen /></MemoryRouter>);
  await screen.findByText('42');
  const before = calls.filter((c) => c.url === '/api/customer/points').length;
  fireEvent.click(screen.getByRole('button', { name: 'Muat ulang' }));
  await waitFor(() => {
    expect(calls.filter((c) => c.url === '/api/customer/points').length).toBe(before + 1);
  });

  const calls2 = stubApi();
  render(<MemoryRouter><CustomerHistoryScreen /></MemoryRouter>);
  await screen.findByText('Kopi Susu');
  const before2 = calls2.filter((c) => c.url === '/api/customer/transactions').length;
  fireEvent.click(screen.getAllByRole('button', { name: 'Muat ulang' }).at(-1));
  await waitFor(() => {
    expect(calls2.filter((c) => c.url === '/api/customer/transactions').length).toBe(before2 + 1);
  });
});

test('pemetaan segmen roda: nilai persis, duplikat, dan nilai di luar daftar', () => {
  expect(segmentIndexForAmount(100000)).toBe(0);
  expect(segmentIndexForAmount(50000)).toBe(1);
  expect(segmentIndexForAmount(25000)).toBe(2);  // duplikat → kecocokan pertama
  expect(segmentIndexForAmount(10000)).toBe(3);
  expect(segmentIndexForAmount(15000)).toBe(3);  // terdekat: 10000 (idx 3)
  expect(segmentIndexForAmount(75000)).toBe(0);  // seri 100rb/50rb → segmen pertama yang dipindai
  expect(segmentIndexForAmount(60000)).toBe(1);  // terdekat: 50000
});
