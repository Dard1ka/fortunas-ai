import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import HomeScreen from './HomeScreen.jsx';

const ANALYSES = Array.from({ length: 11 }, (_, i) => ({
  key: `a${i}`, label: `Analisis ${i}`, description: `desc ${i}`, enabled: true,
}));

test('chip contoh dibangun dari GET /analyses (registry 11 intent)', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(ANALYSES), { status: 200 })));
  render(<MemoryRouter><HomeScreen onVoice={() => {}} /></MemoryRouter>);
  expect(await screen.findByText('Analisis 5')).toBeInTheDocument();
  vi.unstubAllGlobals();
});

test('fallback saat /analyses gagal: chip default tetap ada', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => { throw new Error('net'); }));
  render(<MemoryRouter><HomeScreen onVoice={() => {}} /></MemoryRouter>);
  expect(await screen.findByText(/pelanggan paling setia/i)).toBeInTheDocument();
  vi.unstubAllGlobals();
});

// Kartu inbox pesanan (Wave C area B) — badge dari count GET /umkm/orders?status=paid.
function stubHomeFetch(pendingCount) {
  vi.stubGlobal('fetch', vi.fn(async (url) => {
    const u = String(url);
    if (u.includes('/umkm/orders')) {
      return new Response(JSON.stringify({ orders: [], count: pendingCount }), { status: 200 });
    }
    return new Response(JSON.stringify(ANALYSES), { status: 200 });
  }));
}

test('kartu Pesanan Masuk: badge "{n} pesanan menunggu diterima" saat ada pesanan paid', async () => {
  stubHomeFetch(2);
  render(<MemoryRouter><HomeScreen onVoice={() => {}} /></MemoryRouter>);
  expect(await screen.findByText('2 pesanan menunggu diterima')).toBeInTheDocument();
  vi.unstubAllGlobals();
});

test('kartu Pesanan Masuk: tanpa badge saat 0 pesanan', async () => {
  stubHomeFetch(0);
  render(<MemoryRouter><HomeScreen onVoice={() => {}} /></MemoryRouter>);
  expect(await screen.findByTestId('home-orders')).toBeInTheDocument();
  expect(screen.getByText('Pesanan online dari pelanggan')).toBeInTheDocument();
  expect(screen.queryByText(/pesanan menunggu diterima/)).not.toBeInTheDocument();
  vi.unstubAllGlobals();
});
