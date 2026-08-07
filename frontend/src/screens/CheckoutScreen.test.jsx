import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import CheckoutScreen from './CheckoutScreen.jsx';

// Bentuk respons PERSIS dari app/schemas.py CheckoutConfirmResponse (226-263).
const OK = {
  ok: true, status: 'saved', reply: 'Tersimpan.', invoice: 'INV-9', item_count: 2,
  grand_total: 45000, customer_user_id: 'cu-1', is_new_member: true,
  member_since: '2026-08-08', points_earned: null, promo_redeemed: null,
};
const OK_ATTACH_FAILED = {
  ...OK, customer_user_id: null, is_new_member: false, member_since: null,
  reply: 'Tersimpan. (QR sudah dipakai — poin tidak terhubung.)',
};

function stubFetch(responder) {
  vi.stubGlobal('fetch', vi.fn(responder));
}
afterEach(() => vi.unstubAllGlobals());

const noCatalog = async () => new Response(JSON.stringify({ products: [], count: 0 }), { status: 200 });

function fillOneItem() {
  fireEvent.change(screen.getByLabelText(/Produk 1/i), { target: { value: 'Kopi' } });
  fireEvent.change(screen.getByLabelText(/Jumlah 1/i), { target: { value: '2' } });
  fireEvent.change(screen.getByLabelText(/Harga satuan 1/i), { target: { value: '15000' } });
}

test('multi-item: grand total dihitung live dalam Rupiah id-ID', async () => {
  stubFetch(noCatalog);
  render(<MemoryRouter><CheckoutScreen /></MemoryRouter>);
  fillOneItem();
  fireEvent.click(screen.getByRole('button', { name: /Tambah baris/i }));
  fireEvent.change(screen.getByLabelText(/Produk 2/i), { target: { value: 'Roti' } });
  fireEvent.change(screen.getByLabelText(/Jumlah 2/i), { target: { value: '1' } });
  fireEvent.change(screen.getByLabelText(/Harga satuan 2/i), { target: { value: '15000' } });
  expect(screen.getByText(/Rp\s?45\.000/)).toBeInTheDocument();
});

test('submit mengirim customer_qr_token MENTAH + payload sesuai kontrak', async () => {
  const calls = [];
  stubFetch(async (url, opts) => {
    if (String(url).includes('/checkout/confirm')) {
      calls.push(JSON.parse(opts.body));
      return new Response(JSON.stringify(OK), { status: 200 });
    }
    return noCatalog();
  });
  render(<MemoryRouter><CheckoutScreen /></MemoryRouter>);
  fillOneItem();
  fireEvent.change(screen.getByLabelText(/Token QR customer/i), { target: { value: 'tok-abc' } });
  fireEvent.click(screen.getByRole('button', { name: /Simpan transaksi/i }));
  await waitFor(() => expect(calls).toHaveLength(1));
  expect(calls[0].items).toEqual([{ product: 'Kopi', qty: 2, unit_price: 15000 }]);
  expect(calls[0].customer_qr_token).toBe('tok-abc');
  expect(await screen.findByText(/member baru/i)).toBeInTheDocument();
});

test('attach GAGAL terlihat: ok:true tapi customer_user_id null → warning, bukan sukses penuh', async () => {
  stubFetch(async (url) => (String(url).includes('/checkout/confirm')
    ? new Response(JSON.stringify(OK_ATTACH_FAILED), { status: 200 })
    : noCatalog()));
  render(<MemoryRouter><CheckoutScreen /></MemoryRouter>);
  fillOneItem();
  fireEvent.change(screen.getByLabelText(/Token QR customer/i), { target: { value: 'tok-bekas' } });
  fireEvent.click(screen.getByRole('button', { name: /Simpan transaksi/i }));
  expect(await screen.findByRole('alert')).toHaveTextContent(/tidak terhubung/i);
});

test('error 4xx → pesan BI, form tidak reset', async () => {
  stubFetch(async (url) => (String(url).includes('/checkout/confirm')
    ? new Response(JSON.stringify({ detail: 'Item tidak valid.' }), { status: 422 })
    : noCatalog()));
  render(<MemoryRouter><CheckoutScreen /></MemoryRouter>);
  fillOneItem();
  fireEvent.click(screen.getByRole('button', { name: /Simpan transaksi/i }));
  expect(await screen.findByText(/Item tidak valid/)).toBeInTheDocument();
  expect(screen.getByLabelText(/Produk 1/i)).toHaveValue('Kopi');
});

test('autocomplete: pilih produk mengisi nama + harga', async () => {
  stubFetch(async (url) => (String(url).includes('/products/search')
    ? new Response(JSON.stringify({
        products: [{ id: 1, tenant_id: 1, name: 'Kopi Susu', stock_code: 'K1', price: 15000 }],
        count: 1,
      }), { status: 200 })
    : new Response(JSON.stringify(OK), { status: 200 })));
  render(<MemoryRouter><CheckoutScreen /></MemoryRouter>);
  fireEvent.change(screen.getByLabelText(/Produk 1/i), { target: { value: 'Kop' } });
  fireEvent.click(await screen.findByRole('option', { name: /Kopi Susu/i }));
  expect(screen.getByLabelText(/Produk 1/i)).toHaveValue('Kopi Susu');
  expect(screen.getByLabelText(/Harga satuan 1/i)).toHaveValue(15000);
});
