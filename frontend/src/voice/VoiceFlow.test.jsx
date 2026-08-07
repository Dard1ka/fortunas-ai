import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import VoiceFlow from './VoiceFlow.jsx';

// jsdom tanpa Web Speech API → VoiceFlow otomatis jatuh ke jalur textFallback.
const PARSED = {
  invoice: 'INV-5', product: 'Kopi', qty: 2, unit_price: 15000, total: 30000,
  customer: 'Budi', country: 'Indonesia', confidence: 0.9, source: 'regex',
};
const CHECKOUT_OK = {
  ok: true, status: 'saved', reply: 'Tersimpan.', invoice: 'INV-5', item_count: 1,
  grand_total: 30000, customer_user_id: null, is_new_member: false,
  member_since: null, points_earned: null, promo_redeemed: null,
};

afterEach(() => vi.unstubAllGlobals());

test('konfirmasi voice menulis via /checkout/confirm (K5), bukan /voice/transaction', async () => {
  const urls = [];
  const bodies = [];
  vi.stubGlobal('fetch', vi.fn(async (url, opts) => {
    urls.push(String(url));
    if (String(url).includes('/voice/parse')) {
      return new Response(JSON.stringify(PARSED), { status: 200 });
    }
    bodies.push(JSON.parse(opts.body));
    return new Response(JSON.stringify(CHECKOUT_OK), { status: 200 });
  }));

  render(<VoiceFlow onClose={() => {}} />);
  fireEvent.click(screen.getByRole('button', { name: /Mulai mendengar/i }));
  fireEvent.change(screen.getByPlaceholderText(/Ketik transaksi/i), {
    target: { value: 'jual kopi 2 lima belas ribu pelanggan Budi' },
  });
  fireEvent.click(screen.getByRole('button', { name: /Selesai bicara/i }));
  fireEvent.click(await screen.findByRole('button', { name: /Konfirmasi & Simpan/i }));

  await waitFor(() => expect(urls.some((u) => u.includes('/checkout/confirm'))).toBe(true));
  expect(urls.some((u) => u.includes('/voice/transaction'))).toBe(false);
  expect(bodies[0].items).toEqual([{ product: 'Kopi', qty: 2, unit_price: 15000 }]);
  expect(bodies[0].customer).toBe('Budi');
  expect(bodies[0].invoice).toBe('INV-5');
});
