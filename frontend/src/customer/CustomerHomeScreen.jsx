import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../ui/Card.jsx';
import Button from '../ui/Button.jsx';
import Icon from '../ui/Icon.jsx';
import { api } from '../api/client.js';

export default function CustomerHomeScreen() {
  const navigate = useNavigate();
  const [home, setHome] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const ctrl = new AbortController();
    api.customerHome(ctrl.signal)
      .then(setHome)
      .catch((err) => { if (err.name !== 'AbortError') setError(err.message); });
    return () => ctrl.abort();
  }, []);

  return (
    <div style={{ padding: '18px 18px 24px', display: 'grid', gap: 12, alignContent: 'start' }}>
      <div>
        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 22, letterSpacing: '-0.02em' }}>
          Halo{home?.username ? `, ${home.username}` : ''} 👋
        </div>
        <p style={{ color: 'var(--ink-3)', fontSize: 12.5, marginTop: 4 }}>
          Tunjukkan QR-mu saat belanja untuk kumpulkan poin.
        </p>
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
          <div key={m.tenant_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderTop: '1px dashed var(--border-soft)' }}>
            <span style={{ fontSize: 13.5, fontWeight: 600 }}>{m.tenant_name || `Toko #${m.tenant_id}`}</span>
            {m.member_since && (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-4)' }}>sejak {m.member_since}</span>
            )}
          </div>
        ))}
      </Card>
    </div>
  );
}
