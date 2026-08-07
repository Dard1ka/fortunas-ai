import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../App.jsx';
import CustomerApp from './CustomerApp.jsx';
import CustomerQrScreen from './CustomerQrScreen.jsx';
import { setCustomerToken, clearCustomerToken, getCustomerToken, clearToken } from '../api/client.js';

vi.mock('qrcode', () => ({
  toDataURL: vi.fn(async () => 'data:image/png;base64,QRDUMMY'),
}));

afterEach(() => {
  vi.unstubAllGlobals();
  clearCustomerToken();
  clearToken();
  sessionStorage.clear();
  localStorage.clear();
});

test('/customer/login bisa diakses TANPA login UMKM (bukan LoginScreen UMKM)', () => {
  render(<MemoryRouter initialEntries={['/customer/login']}><App /></MemoryRouter>);
  expect(screen.getByLabelText(/Nomor HP/i)).toBeInTheDocument();
  expect(screen.queryByText(/Daftar Bisnis/i)).not.toBeInTheDocument();
});

test('rute gated tanpa customer token → redirect ke login pelanggan', () => {
  render(<MemoryRouter initialEntries={['/customer/home']}><CustomerApp /></MemoryRouter>);
  expect(screen.getByLabelText(/Nomor HP/i)).toBeInTheDocument();
});

test('alur penuh: phone → OTP dev → profil → bootstrap dev-token → token customer tersimpan', async () => {
  const bodies = [];
  vi.stubGlobal('fetch', vi.fn(async (url, opts = {}) => {
    if (String(url).includes('/customer/auth/bootstrap')) {
      bodies.push(JSON.parse(opts.body));
      return new Response(JSON.stringify({
        access_token: 'CUST-JWT', token_type: 'bearer', role: 'customer', is_new_user: true,
        profile: { customer_user_id: 'cu-9', username: 'Sari', phone_number: '0812345678', birth_date: '2000-01-01', created_at: '' },
      }), { status: 200 });
    }
    // customerHome setelah redirect
    return new Response(JSON.stringify({ username: 'Sari', total_points: 0, memberships: [] }), { status: 200 });
  }));

  render(<MemoryRouter initialEntries={['/customer/login']}><CustomerApp /></MemoryRouter>);
  fireEvent.change(screen.getByLabelText(/Nomor HP/i), { target: { value: '0812345678' } });
  fireEvent.click(screen.getByRole('button', { name: /Kirim kode OTP/i }));
  fireEvent.change(await screen.findByLabelText(/Kode OTP/i), { target: { value: '123456' } });
  fireEvent.click(screen.getByRole('button', { name: /Lanjut/i }));
  fireEvent.change(await screen.findByLabelText(/Nama panggilan/i), { target: { value: 'Sari' } });
  fireEvent.change(screen.getByLabelText(/Tanggal lahir/i), { target: { value: '2000-01-01' } });
  fireEvent.click(screen.getByRole('button', { name: /Selesai & masuk/i }));

  await waitFor(() => expect(bodies).toHaveLength(1));
  expect(bodies[0].firebase_id_token).toBe('dev:0812345678:0812345678');
  expect(bodies[0].username).toBe('Sari');
  expect(bodies[0].birth_date).toBe('2000-01-01');
  await waitFor(() => expect(getCustomerToken()).toBe('CUST-JWT'));
});

test('QR: render dari qr_token, token string + tombol salin tampil, auto-refresh jelang kedaluwarsa', async () => {
  let calls = 0;
  vi.stubGlobal('fetch', vi.fn(async () => {
    calls += 1;
    return new Response(JSON.stringify({
      qr_token: `tok-${calls}-1234567890`, nonce: 'n', issued_at: 'i', expires_at: 'e', ttl_seconds: 90,
    }), { status: 200 });
  }));
  setCustomerToken('CUST-JWT');
  vi.useFakeTimers();
  render(<MemoryRouter initialEntries={['/customer/qr']}><CustomerQrScreen /></MemoryRouter>);
  await vi.waitFor(() => expect(screen.getByText(/tok-1-1234567890/)).toBeInTheDocument());
  expect(screen.getByRole('button', { name: /Salin token/i })).toBeInTheDocument();
  expect(screen.getByAltText(/QR identitas pelanggan/i)).toBeInTheDocument();
  // 85 detik (ttl-5) → refresh otomatis mengambil token baru
  await vi.advanceTimersByTimeAsync(86 * 1000);
  await vi.waitFor(() => expect(screen.getByText(/tok-2-1234567890/)).toBeInTheDocument());
  vi.useRealTimers();
});
