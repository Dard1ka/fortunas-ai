import { render, screen } from '@testing-library/react';
import { act } from 'react';
import Button from './Button.jsx';
import Input from './Input.jsx';
import FormPane from './FormPane.jsx';

function setWidth(w) {
  Object.defineProperty(window, 'innerWidth', { configurable: true, value: w });
  act(() => window.dispatchEvent(new Event('resize')));
}

test('button disabled DISTINGUISHABLE, bukan violet redup (regresi login lama)', () => {
  const { rerender } = render(<Button>Masuk</Button>);
  const enabledBg = screen.getByRole('button').style.background;
  rerender(<Button disabled>Masuk</Button>);
  const btn = screen.getByRole('button');
  expect(btn.style.background).not.toBe(enabledBg);
  expect(btn).toBeDisabled();
  expect(btn.style.boxShadow).toBe('none');
});

test('input: label ter-asosiasi (a11y) dan pesan error tampil sebagai alert', () => {
  render(<Input id="email" label="Email" error="Format salah" />);
  expect(screen.getByLabelText('Email')).toBeInTheDocument();
  expect(screen.getByRole('alert')).toHaveTextContent('Format salah');
});

test('form pane: kartu 420px di tier medium, pass-through di compact', () => {
  setWidth(800);
  const { unmount } = render(<FormPane><p>form</p></FormPane>);
  expect(screen.getByTestId('form-pane-card')).toHaveStyle({ maxWidth: '420px' });
  unmount();
  setWidth(390);
  render(<FormPane><p>form</p></FormPane>);
  expect(screen.queryByTestId('form-pane-card')).not.toBeInTheDocument();
  expect(screen.getByText('form')).toBeInTheDocument();
});

test('register menyertakan address saat diisi (payload pass-through client)', async () => {
  const calls = [];
  vi.stubGlobal('fetch', vi.fn(async (url, opts) => {
    calls.push({ url, body: JSON.parse(opts.body) });
    return new Response(JSON.stringify({ access_token: 't', table_prefix: 'p' }), { status: 200 });
  }));
  const { api } = await import('../api/client.js');
  await api.register({
    email: 'a@b.c', password: 'x', business_name: 'Toko',
    business_profile: { jenis: 'retail' }, address: 'Jl. Kediri 1',
  });
  expect(calls[0].url).toBe('/api/auth/register');
  expect(calls[0].body.address).toBe('Jl. Kediri 1');
  vi.unstubAllGlobals();
});
