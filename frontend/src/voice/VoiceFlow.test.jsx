import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import VoiceFlow from './VoiceFlow.jsx';

// jsdom tanpa Web Speech API → VoiceFlow otomatis jatuh ke jalur textFallback.
// Wave C area E: parse kini LOKAL (transactionParser.js) — TANPA panggilan
// /voice/parse; jalur tulis tetap SATU request /checkout/confirm multi-item.
const CHECKOUT_OK = {
  ok: true, status: 'saved', reply: 'Tersimpan.', invoice: 'INV-OK', item_count: 2,
  grand_total: 1040000, customer_user_id: null, is_new_member: false,
  member_since: null, points_earned: null, promo_redeemed: null,
};

function stubFetch() {
  const urls = [];
  const bodies = [];
  vi.stubGlobal('fetch', vi.fn(async (url, opts = {}) => {
    urls.push(String(url));
    if (opts.body) bodies.push(JSON.parse(opts.body));
    return new Response(JSON.stringify(CHECKOUT_OK), { status: 200 });
  }));
  return { urls, bodies };
}

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
});

async function typeAndParse(transcript) {
  fireEvent.click(screen.getByRole('button', { name: /Mulai mendengar/i }));
  fireEvent.change(screen.getByPlaceholderText(/Ketik transaksi/i), {
    target: { value: transcript },
  });
  fireEvent.click(screen.getByRole('button', { name: /Selesai bicara/i }));
  await screen.findByText(/Periksa lalu konfirmasi/);
}

test('multi-item: parser lokal memecah 2 produk, TANPA panggilan /voice/parse', async () => {
  const { urls } = stubFetch();
  render(<VoiceFlow onClose={() => {}} parseDelayMs={0} />);
  await typeAndParse('penghapus 10 dengan harga 100.000 dan pensil 2 dengan harga Rp20.000');

  expect(screen.getByText(/2 item/)).toBeInTheDocument();
  expect(screen.getByTestId('voice-item-0')).toHaveTextContent('Penghapus');
  expect(screen.getByTestId('voice-item-1')).toHaveTextContent('Pensil');
  expect(screen.getByTestId('voice-grand-total')).toHaveTextContent('Rp 1.040.000');
  expect(urls.some((u) => u.includes('/voice/parse'))).toBe(false);
});

test('konfirmasi menulis SEKALI via /checkout/confirm dengan items[] penuh', async () => {
  const { urls, bodies } = stubFetch();
  render(<VoiceFlow onClose={() => {}} parseDelayMs={0} />);
  await typeAndParse('penghapus 10 harga 100.000 dan pensil 2 harga 20.000 pelanggan budi');

  fireEvent.click(screen.getByRole('button', { name: /Konfirmasi & Simpan/i }));
  await waitFor(() => expect(urls.filter((u) => u.includes('/checkout/confirm'))).toHaveLength(1));
  expect(urls.some((u) => u.includes('/voice/transaction'))).toBe(false);
  expect(bodies[0].items).toEqual([
    { product: 'Penghapus', qty: 10, unit_price: 100000 },
    { product: 'Pensil', qty: 2, unit_price: 20000 },
  ]);
  expect(bodies[0].customer).toBe('Budi');
  expect(bodies[0].invoice).toMatch(/^INV-/);

  // riwayat lokal: SATU entri per item (bentuk yang dibaca HistoryScreen)
  await screen.findByText('Tersimpan!');
  const key = Object.keys(localStorage).find((k) => k.startsWith('fortunas_voice_'));
  const hist = JSON.parse(localStorage.getItem(key));
  expect(hist).toHaveLength(2);
  expect(hist[0]).toMatchObject({ invoice: 'INV-OK', total: hist[0].qty * hist[0].unit_price });
});

test('edit: ubah qty, hapus baris, tambah baris kosong', async () => {
  stubFetch();
  render(<VoiceFlow onClose={() => {}} parseDelayMs={0} />);
  await typeAndParse('kopi 2 harga 15000 dan roti 1 harga 8000');

  fireEvent.click(screen.getByRole('button', { name: 'Edit' }));
  fireEvent.change(screen.getByLabelText('Jumlah item 1'), { target: { value: '5' } });
  expect(screen.getByTestId('voice-grand-total')).toHaveTextContent('Rp 83.000'); // 5×15000 + 8000

  fireEvent.click(screen.getByTestId('voice-item-remove-1'));
  expect(screen.queryByTestId('voice-item-1')).not.toBeInTheDocument();
  expect(screen.getByTestId('voice-grand-total')).toHaveTextContent('Rp 75.000');

  fireEvent.click(screen.getByTestId('voice-item-add'));
  expect(screen.getByTestId('voice-item-1')).toBeInTheDocument();
  expect(within(screen.getByTestId('voice-item-1')).getByLabelText('Produk item 2')).toHaveValue('');
});

test('transkrip omong kosong tetap maju ke konfirmasi (fallback item kosong bisa diedit)', async () => {
  stubFetch();
  render(<VoiceFlow onClose={() => {}} parseDelayMs={0} />);
  // 'oke ya baik' → parser 0 item → fallback SATU baris kosong (paritas
  // voice_flow.dart) — user melengkapi manual, tidak dilempar balik.
  await typeAndParse('oke ya baik');
  expect(screen.getByText(/1 item/)).toBeInTheDocument();
  expect(screen.getByTestId('voice-item-0')).toBeInTheDocument();
});
