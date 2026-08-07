import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import DpaScreen from './DpaScreen.jsx';

// Bentuk PERSIS dari app/schemas.py DPAPayload (268-275).
const DPA = {
  raw_text: 'Data hanya untuk analisis internal.',
  allowed_rules: ['analisis penjualan', 'rekomendasi produk'],
  forbidden_rules: ['bagikan data ke pihak ketiga'],
  policy_summary: null,
  version: 3,
  verified_at: null,
  updated_at: '2026-08-01 10:00:00',
};
const EMPTY = {
  raw_text: '', allowed_rules: [], forbidden_rules: [],
  policy_summary: null, version: 0, verified_at: null, updated_at: null,
};

function stubFetch({ get = DPA, put = null, putStatus = 200 }) {
  const bodies = [];
  vi.stubGlobal('fetch', vi.fn(async (url, opts = {}) => {
    if ((opts.method || 'GET') === 'PUT') {
      bodies.push(JSON.parse(opts.body));
      if (putStatus !== 200) {
        return new Response(JSON.stringify({ detail: 'Konfirmasi password salah.' }), { status: putStatus });
      }
      return new Response(JSON.stringify(put), { status: 200 });
    }
    return new Response(JSON.stringify(get), { status: 200 });
  }));
  return bodies;
}
afterEach(() => vi.unstubAllGlobals());

const ui = () => render(<MemoryRouter><DpaScreen /></MemoryRouter>);

test('view: raw_text + chips allowed/forbidden + versi tampil', async () => {
  stubFetch({});
  ui();
  expect(await screen.findByText(/Data hanya untuk analisis internal/)).toBeInTheDocument();
  expect(screen.getByText('analisis penjualan')).toBeInTheDocument();
  expect(screen.getByText('bagikan data ke pihak ketiga')).toBeInTheDocument();
  expect(screen.getByText(/v3/)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Ubah aturan/i })).toBeInTheDocument();
});

test('empty state: ajakan mengisi pagar AI', async () => {
  stubFetch({ get: EMPTY });
  ui();
  expect(await screen.findByText(/Belum ada pagar AI/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Isi pagar AI/i })).toBeInTheDocument();
});

test('edit + simpan: payload PUT lengkap termasuk chip baru & password', async () => {
  const bodies = stubFetch({ put: { ...DPA, allowed_rules: [...DPA.allowed_rules, 'promo musiman'], version: 4 } });
  ui();
  fireEvent.click(await screen.findByRole('button', { name: /Ubah aturan/i }));
  fireEvent.change(screen.getByLabelText(/Tambah aturan boleh/i), { target: { value: 'promo musiman' } });
  fireEvent.click(screen.getByRole('button', { name: /^Tambah boleh$/i }));
  fireEvent.change(screen.getByLabelText(/Konfirmasi password/i), { target: { value: 'rahasia1' } });
  fireEvent.click(screen.getByRole('button', { name: /^Simpan$/i }));
  await waitFor(() => expect(bodies).toHaveLength(1));
  expect(bodies[0]).toEqual({
    raw_text: DPA.raw_text,
    allowed_rules: [...DPA.allowed_rules, 'promo musiman'],
    forbidden_rules: DPA.forbidden_rules,
    password: 'rahasia1',
  });
  expect(await screen.findByText(/v4/)).toBeInTheDocument(); // kembali ke view, data baru
});

test('403: pesan backend tampil, draft TIDAK reset', async () => {
  stubFetch({ putStatus: 403 });
  ui();
  fireEvent.click(await screen.findByRole('button', { name: /Ubah aturan/i }));
  fireEvent.change(screen.getByLabelText(/Konfirmasi password/i), { target: { value: 'salah' } });
  fireEvent.click(screen.getByRole('button', { name: /^Simpan$/i }));
  expect(await screen.findByRole('alert')).toHaveTextContent(/Konfirmasi password salah/);
  expect(screen.getByLabelText(/Teks perjanjian/i)).toHaveValue(DPA.raw_text);
});

test('hapus chip: hilang dari daftar', async () => {
  stubFetch({});
  ui();
  fireEvent.click(await screen.findByRole('button', { name: /Ubah aturan/i }));
  fireEvent.click(screen.getByRole('button', { name: /Hapus rekomendasi produk/i }));
  expect(screen.queryByText('rekomendasi produk')).not.toBeInTheDocument();
});
