import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import BriefingScreen from './BriefingScreen.jsx';

const KEYS = [
  'repeat_customer', 'high_value_customer', 'peak_hour', 'bundle_opportunity',
  'top_product', 'revenue_trend', 'customer_segmentation', 'churn_risk',
  'slow_moving_product', 'average_basket_size', 'demand_forecast',
];

const REPORT = {
  status: 'success',
  latest: {
    date: '2026-08-08',
    generated_at: '2026-08-08T07:00:00Z',
    executive_summary: 'Ringkasan eksekutif.',
    sections: KEYS.map((k, i) => ({
      analysis_type: k,
      label: `Label ${k}`,
      summary: `Ringkas ${k}`,
      top_findings: [`Temuan ${i + 1} angka ${i + 1}0%`],
      row_count: i + 1,
    })),
  },
  history: [],
};

test('briefing merender SEMUA 11 seksi, bukan hanya 4 tile pertama', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(REPORT), { status: 200 })));
  render(<MemoryRouter><BriefingScreen /></MemoryRouter>);
  for (const k of KEYS) {
    expect(await screen.findByText(`Label ${k}`)).toBeInTheDocument();
  }
  vi.unstubAllGlobals();
});
