import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import HistoryScreen from './HistoryScreen.jsx';

// Bentuk respons PERSIS dari app/api/routes/transactions.py + schemas.py:
// UmkmTransactionsResponse { transactions: UmkmTransaction[], count, source }
const TXS = {
  transactions: [
    {
      invoice: 'INV-1001',
      customer: 'Sari (18103)',
      country: 'Indonesia',
      invoice_date: '2026-08-01 10:00:00',
      total: 30000,
      items: [{ product: 'Kopi Susu', stock_code: '', qty: 2, unit_price: 15000, total: 30000 }],
    },
  ],
  count: 1,
  source: 'bigquery',
};

function stubFetch(txBody) {
  vi.stubGlobal('fetch', vi.fn(async (url) => {
    if (String(url).includes('/umkm/transactions')) {
      return new Response(JSON.stringify(txBody), { status: 200 });
    }
    // reportDaily untuk seksi briefing
    return new Response(JSON.stringify({ status: 'empty', latest: null, history: [] }), { status: 200 });
  }));
}

test('seksi transaksi BigQuery: render invoice + Rupiah id-ID', async () => {
  stubFetch(TXS);
  render(<MemoryRouter><HistoryScreen /></MemoryRouter>);
  expect(await screen.findByText(/INV-1001/)).toBeInTheDocument();
  expect(screen.getByText(/Kopi Susu/)).toBeInTheDocument();
  expect(screen.getByText(/Rp\s?30\.000/)).toBeInTheDocument();
  vi.unstubAllGlobals();
});

test('seksi transaksi kosong: empty state BI, bukan error', async () => {
  stubFetch({ transactions: [], count: 0, source: '' });
  render(<MemoryRouter><HistoryScreen /></MemoryRouter>);
  expect(await screen.findByText(/Belum ada transaksi tersimpan/i)).toBeInTheDocument();
  vi.unstubAllGlobals();
});
