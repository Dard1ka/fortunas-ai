import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ProfileScreen from './ProfileScreen.jsx';
import pkg from '../../package.json';

const ME_WITH_CODE = {
  email: 'a@b.c', tenant_id: 1, tenant_name: 'Toko Sari', table_prefix: 't1',
  business_profile: { jenis: 'warung', code: 'KDS-001', address: 'Jl. Dhoho 12' },
};
const ME_NO_CODE = { ...ME_WITH_CODE, business_profile: { jenis: 'warung' } };

function stubFetch(me) {
  vi.stubGlobal('fetch', vi.fn(async (url, opts) => {
    const u = String(url);
    if (u.includes('/auth/me')) return new Response(JSON.stringify(me), { status: 200 });
    if (u.includes('/umkm/address')) {
      const body = JSON.parse(opts.body);
      return new Response(JSON.stringify({ status: 'ok', code: 'KDS-007', address: body.address }), { status: 200 });
    }
    return new Response(JSON.stringify({ status: 'ok' }), { status: 200 });
  }));
}

afterEach(() => vi.unstubAllGlobals());

test('label versi dibaca dari package.json, bukan hardcode', async () => {
  stubFetch(ME_WITH_CODE);
  render(<MemoryRouter><ProfileScreen onLogout={() => {}} /></MemoryRouter>);
  expect(await screen.findByText(`Fortunas AI · v${pkg.version}`)).toBeInTheDocument();
});

test('kode publik tampil saat ada di business_profile', async () => {
  stubFetch(ME_WITH_CODE);
  render(<MemoryRouter><ProfileScreen onLogout={() => {}} /></MemoryRouter>);
  expect(await screen.findByText('KDS-001')).toBeInTheDocument();
});

test('tanpa kode: form alamat backfill memanggil PUT /umkm/address dan menampilkan kode baru', async () => {
  stubFetch(ME_NO_CODE);
  render(<MemoryRouter><ProfileScreen onLogout={() => {}} /></MemoryRouter>);
  const input = await screen.findByLabelText(/Alamat usaha/i);
  fireEvent.change(input, { target: { value: 'Jl. Kediri 99' } });
  fireEvent.click(screen.getByRole('button', { name: /Buat kode publik/i }));
  await waitFor(() => expect(screen.getByText('KDS-007')).toBeInTheDocument());
});
