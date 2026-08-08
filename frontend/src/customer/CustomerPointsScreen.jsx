import { useCallback, useEffect, useState } from 'react';
import Card from '../ui/Card.jsx';
import Button from '../ui/Button.jsx';
import { api } from '../api/client.js';

// Label event_type ledger → Bahasa Indonesia (paritas customer_points_screen
// Flutter; 'adjust' & nilai tak dikenal jatuh ke 'Penyesuaian').
const LEDGER_LABEL = {
  earn: 'Poin dari transaksi',
  redeem: 'Tukar untuk promo',
  expire: 'Poin kedaluwarsa',
};

const dateOnly = (iso) => String(iso || '').split('T')[0];

export default function CustomerPointsScreen() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  // Gaya promise: setState hanya di callback .then/.catch — pola yang lolos
  // lint react-hooks/set-state-in-effect (setState async, bukan sinkron).
  const load = useCallback((signal) => api.customerPoints(signal)
    .then((r) => { setData(r); setError(null); })
    .catch((err) => {
      if (err.name !== 'AbortError') setError(err.message || 'Gagal memuat poin.');
    }), []);

  useEffect(() => { load(); }, [load]);

  return (
    <div style={{ padding: '18px 18px 24px', display: 'grid', gap: 12, alignContent: 'start' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 20 }}>Poin Saya</div>
        <Button variant="text" onClick={load}>Muat ulang</Button>
      </div>

      {/* Data basi menang: error hanya menggantikan konten bila data masih null. */}
      {error && data == null && (
        <div role="alert" style={{ padding: '12px 14px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 12, fontSize: 12.5 }}>
          {error}
        </div>
      )}

      <Card style={{ background: 'var(--lime)', display: 'grid', gap: 4 }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--ink-2)' }}>
          Saldo poin
        </div>
        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 48, lineHeight: 1 }}>
          {data ? data.balance : '—'}
        </div>
      </Card>

      <Card style={{ display: 'grid', gap: 10 }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 700, color: 'var(--ink-3)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
          Riwayat poin
        </div>
        {data && (data.recent || []).length === 0 && (
          <p style={{ fontSize: 12.5, color: 'var(--ink-3)' }}>Belum ada aktivitas poin.</p>
        )}
        {(data?.recent || []).map((e, i) => {
          const earn = (e.points_delta ?? 0) >= 0; // nol dihitung earn
          return (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderTop: '1px dashed var(--border-soft)' }}>
              <div
                aria-hidden
                style={{
                  width: 30, height: 30, borderRadius: 9, flexShrink: 0,
                  background: earn ? 'var(--lime-deep)' : 'var(--peach)',
                  border: '1.5px solid var(--ink)',
                  display: 'grid', placeItems: 'center', fontWeight: 700, fontSize: 15,
                }}
              >
                {earn ? '+' : '−'}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{LEDGER_LABEL[e.event_type] || 'Penyesuaian'}</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5, color: 'var(--ink-4)', marginTop: 2 }}>
                  {[e.invoice ? `Invoice ${e.invoice}` : null, dateOnly(e.created_at)].filter(Boolean).join(' · ')}
                </div>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 13, color: earn ? 'var(--success)' : 'var(--error)' }}>
                {earn ? `+${e.points_delta}` : `${e.points_delta}`}
              </span>
            </div>
          );
        })}
      </Card>
    </div>
  );
}
