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
