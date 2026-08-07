import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ScanScreen from './ScanScreen.jsx';

function stubScan(body) {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(body), { status: 200 })));
}
afterEach(() => vi.unstubAllGlobals());

async function submitToken() {
  fireEvent.change(screen.getByLabelText(/Token QR pelanggan/i), { target: { value: 'tok-1234567890' } });
  fireEvent.click(screen.getByRole('button', { name: /Validasi/i }));
}

test('valid member baru: nama + varian member baru', async () => {
  stubScan({ valid: true, customer_user_id: 'cu-1', username: 'Sari', is_new_member: true, member_since: null, reason: null });
  render(<MemoryRouter><ScanScreen /></MemoryRouter>);
  await submitToken();
  expect(await screen.findByText(/Sari terdaftar sebagai member/i)).toBeInTheDocument();
  expect(screen.getByText(/Member baru/i)).toBeInTheDocument();
});

test('valid member lama: varian member sejak', async () => {
  stubScan({ valid: true, customer_user_id: 'cu-1', username: 'Budi', is_new_member: false, member_since: '2026-07-01', reason: null });
  render(<MemoryRouter><ScanScreen /></MemoryRouter>);
  await submitToken();
  expect(await screen.findByText(/Sudah member sejak 2026-07-01/i)).toBeInTheDocument();
});

test('invalid expired & replayed: pesan BI spesifik per reason', async () => {
  stubScan({ valid: false, reason: 'expired' });
  const { unmount } = render(<MemoryRouter><ScanScreen /></MemoryRouter>);
  await submitToken();
  expect(await screen.findByRole('alert')).toHaveTextContent(/kedaluwarsa/i);
  unmount();
  stubScan({ valid: false, reason: 'replayed' });
  render(<MemoryRouter><ScanScreen /></MemoryRouter>);
  await submitToken();
  expect(await screen.findByRole('alert')).toHaveTextContent(/sudah pernah dipakai/i);
});
