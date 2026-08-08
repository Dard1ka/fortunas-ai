import { useCallback, useEffect, useState } from 'react';
import Card from '../ui/Card.jsx';
import Button from '../ui/Button.jsx';
import { api } from '../api/client.js';
import { formatRupiah } from '../lib/format.js';

const dateOnly = (iso) => String(iso || '').split('T')[0];

// Riwayat transaksi lintas-UMKM (BigQuery, best-effort di backend).
// Urutan & cap 50 baris ditentukan server — klien TIDAK menyortir ulang.
// Kosong ≠ gagal: tanpa kredensial BQ backend membalas [] + message — pakai
// message server sebagai empty state, fallback 'Belum ada transaksi.'
export default function CustomerHistoryScreen() {
  const [resp, setResp] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setResp(await api.customerTransactions());
    } catch (err) {
      if (err.name !== 'AbortError') setError(err.message || 'Gagal memuat riwayat.');
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const rows = resp?.transactions || [];

  return (
    <div style={{ padding: '18px 18px 24px', display: 'grid', gap: 12, alignContent: 'start' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 20 }}>Riwayat</div>
        <Button variant="text" onClick={load}>Muat ulang</Button>
      </div>

      {error && resp == null && (
        <div role="alert" style={{ padding: '12px 14px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 12, fontSize: 12.5 }}>
          {error}
        </div>
      )}

      {resp && rows.length === 0 && (
        <p style={{ fontSize: 12.5, color: 'var(--ink-3)', textAlign: 'center', padding: '24px 0' }}>
          {resp.message || 'Belum ada transaksi.'}
        </p>
      )}

      {rows.map((t, i) => {
        const sub = [
          t.tenant_name || null,
          t.Quantity != null ? `x${t.Quantity}` : null,
          t.InvoiceDate ? dateOnly(t.InvoiceDate) : null,
        ].filter(Boolean).join(' · ');
        return (
          <Card key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, padding: 14 }}>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 13.5, fontWeight: 700 }}>{t.Description || '—'}</div>
              {sub && (
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5, color: 'var(--ink-4)', marginTop: 3 }}>{sub}</div>
              )}
            </div>
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 12.5, flexShrink: 0 }}>
              {formatRupiah(t.Price)}
            </span>
          </Card>
        );
      })}
    </div>
  );
}
