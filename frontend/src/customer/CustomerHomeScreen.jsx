import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../ui/Card.jsx';
import Button from '../ui/Button.jsx';
import Icon from '../ui/Icon.jsx';
import { api } from '../api/client.js';
import { formatRupiah } from '../lib/format.js';

// Label status promo → BI (deviasi sadar spec4 #9 — Flutter membocorkan
// 'generated'/'redeemed' mentah ke UI).
const PROMO_STATUS_LABEL = { generated: 'Aktif', redeemed: 'Terpakai', expired: 'Kedaluwarsa' };
const dateOnly = (iso) => String(iso || '').split('T')[0];

export default function CustomerHomeScreen() {
  const navigate = useNavigate();
  const [home, setHome] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(async (signal) => {
    try {
      setError(null);
      setHome(await api.customerHome(signal));
    } catch (err) {
      if (err.name !== 'AbortError') setError(err.message);
    }
  }, []);

  useEffect(() => {
    const ctrl = new AbortController();
    load(ctrl.signal);
    return () => ctrl.abort();
  }, [load]);

  const lastTx = home?.last_transaction || null;
  const lastPromo = home?.last_promo || null;

  return (
    <div style={{ padding: '18px 18px 24px', display: 'grid', gap: 12, alignContent: 'start' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
        <div>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 22, letterSpacing: '-0.02em' }}>
            Halo{home?.username ? `, ${home.username}` : ''} 👋
          </div>
          <p style={{ color: 'var(--ink-3)', fontSize: 12.5, marginTop: 4 }}>
            Tunjukkan QR-mu saat belanja untuk kumpulkan poin.
          </p>
        </div>
        <Button variant="text" onClick={() => load()}>Muat ulang</Button>
      </div>

      <Card style={{ background: 'var(--ink)', color: '#fff', display: 'grid', gap: 4 }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--lime)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
          Total poin
        </div>
        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 32 }}>
          {home ? home.total_points : '—'}
        </div>
      </Card>

      <Button onClick={() => navigate('/customer/qr')} style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
        <Icon name="sparkle" size={18} stroke="#fff" strokeWidth={2} /> Tampilkan QR Saya
      </Button>

      {/* PROMO TERAKHIR (Wave C area D — paritas _PromoTile Flutter). */}
      {lastPromo && (
        <Card
          data-testid="home-last-promo"
          style={{ background: lastPromo.status === 'redeemed' ? 'var(--surface-soft)' : 'var(--peach-soft)', display: 'grid', gap: 4 }}
        >
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 700, color: 'var(--ink-3)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            Promo terakhir
          </div>
          <div style={{ fontSize: 13.5, fontWeight: 700 }}>{lastPromo.name}</div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-3)' }}>
            Kode {lastPromo.code} · {PROMO_STATUS_LABEL[lastPromo.status] || lastPromo.status}
          </div>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 16 }}>
            {formatRupiah(lastPromo.discount_amount)}
          </div>
        </Card>
      )}

      <Card style={{ display: 'grid', gap: 10 }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 700, color: 'var(--ink-3)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
          Toko yang kamu ikuti ({home?.memberships?.length ?? 0})
        </div>
        {error && <div role="alert" style={{ fontSize: 12.5, color: 'var(--error)' }}>{error}</div>}
        {home && home.memberships.length === 0 && (
          <p style={{ fontSize: 12.5, color: 'var(--ink-3)', lineHeight: 1.5 }}>
            Belum ada. Tunjukkan QR-mu ke kasir saat belanja — keanggotaan dibuat otomatis.
          </p>
        )}
        {(home?.memberships || []).map((m) => (
          <div key={m.tenant_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, padding: '8px 0', borderTop: '1px dashed var(--border-soft)' }}>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 13.5, fontWeight: 600 }}>{m.tenant_name || `Toko #${m.tenant_id}`}</div>
              {m.member_since && (
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-4)' }}>sejak {m.member_since}</div>
              )}
            </div>
            {/* Tukar poin → spin wheel per-UMKM (tenant dari URL param). */}
            <Button
              variant="secondary"
              data-testid={`home-make-promo-${m.tenant_id}`}
              onClick={() => navigate(`/customer/promo/${m.tenant_id}`)}
              style={{ minHeight: 38, fontSize: 12, padding: '0 12px', flexShrink: 0 }}
            >
              Buat Promo
            </Button>
          </div>
        ))}
      </Card>

      {/* TRANSAKSI TERAKHIR (map mentah BigQuery; best-effort — bisa null). */}
      {lastTx && (
        <Card data-testid="home-last-tx" style={{ display: 'grid', gap: 4 }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 700, color: 'var(--ink-3)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            Transaksi terakhir
          </div>
          <div style={{ fontSize: 13.5, fontWeight: 700 }}>
            {lastTx.Description || lastTx.description || '—'}
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-4)' }}>
            {[lastTx.tenant_name || null, lastTx.InvoiceDate ? dateOnly(lastTx.InvoiceDate) : null].filter(Boolean).join(' · ')}
          </div>
        </Card>
      )}
    </div>
  );
}
