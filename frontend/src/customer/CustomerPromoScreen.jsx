import { useEffect, useRef, useState } from 'react';
import { Navigate, useNavigate, useParams } from 'react-router-dom';
import Card from '../ui/Card.jsx';
import Button from '../ui/Button.jsx';
import Icon from '../ui/Icon.jsx';
import { api } from '../api/client.js';

// Spin wheel promo (paritas customer_promo_screen Flutter).
// HASIL DITENTUKAN SERVER (weighted CSPRNG di /customer/promos/generate) —
// roda hanya MENGANIMASIKAN hasil; RNG klien akan berbohong soal hasil.
import { SEGMENTS, SEG_DEG, SPIN_MS, segmentIndexForAmount } from './promoWheel.js';

const SEGMENT_LABEL = (v) => `Rp${Math.round(v / 1000)}rb`;
const SEGMENT_COLORS = ['var(--violet)', 'var(--lime)', 'var(--sky)', 'var(--peach)', 'var(--lime-deep)', 'var(--surface-hover)'];

const dateOnly = (iso) => String(iso || '').split('T')[0];

function polar(cx, cy, r, deg) {
  const rad = (deg * Math.PI) / 180;
  return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
}

function Wheel({ rotation, spinning }) {
  const cx = 130; const cy = 130; const r = 120;
  return (
    <div style={{ position: 'relative', width: 260, margin: '0 auto' }}>
      {/* pointer segitiga di jam-12 */}
      <div
        aria-hidden
        style={{
          position: 'absolute', top: -6, left: '50%', transform: 'translateX(-50%)', zIndex: 2,
          width: 0, height: 0, borderLeft: '10px solid transparent', borderRight: '10px solid transparent',
          borderTop: '16px solid var(--ink)',
        }}
      />
      <svg
        viewBox="0 0 260 260"
        width="260"
        height="260"
        data-testid="promo-wheel"
        style={{
          display: 'block',
          transform: `rotate(${rotation}deg)`,
          transition: spinning ? `transform ${SPIN_MS}ms cubic-bezier(0.33, 1, 0.68, 1)` : 'none',
        }}
      >
        {SEGMENTS.map((v, i) => {
          // Segmen i mulai di jam-12 (-90°) searah jarum jam.
          const a0 = -90 + i * SEG_DEG;
          const a1 = a0 + SEG_DEG;
          const [x0, y0] = polar(cx, cy, r, a0);
          const [x1, y1] = polar(cx, cy, r, a1);
          const mid = a0 + SEG_DEG / 2;
          const [lx, ly] = polar(cx, cy, r * 0.62, mid);
          return (
            <g key={i}>
              <path
                d={`M ${cx} ${cy} L ${x0} ${y0} A ${r} ${r} 0 0 1 ${x1} ${y1} Z`}
                fill={SEGMENT_COLORS[i]}
                stroke="var(--ink)"
                strokeWidth="2"
              />
              <text
                x={lx}
                y={ly}
                textAnchor="middle"
                dominantBaseline="middle"
                transform={`rotate(${mid + 90} ${lx} ${ly})`}
                style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 700, fill: 'var(--ink)' }}
              >
                {SEGMENT_LABEL(v)}
              </text>
            </g>
          );
        })}
        <circle cx={cx} cy={cy} r="26" fill="var(--surface)" stroke="var(--ink)" strokeWidth="2.5" />
      </svg>
    </div>
  );
}

export default function CustomerPromoScreen() {
  const navigate = useNavigate();
  const { tenantId } = useParams();
  const tid = Number.parseInt(tenantId, 10);

  const [membership, setMembership] = useState(null);
  const [lookupDone, setLookupDone] = useState(false);
  const [rotation, setRotation] = useState(0);
  const [spinning, setSpinning] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [won, setWon] = useState(null); // PromoInstance + spin amount server
  const [qrDataUrl, setQrDataUrl] = useState('');
  const [error, setError] = useState(null);
  const doneTimer = useRef();

  // Nama tenant di-lookup dari /customer/home (param URL tahan reload PWA —
  // pengganti GoRouter `extra` Flutter). Tenant tak dikenal → balik ke home.
  useEffect(() => {
    let alive = true;
    api.customerHome()
      .then((h) => {
        if (!alive) return;
        setMembership((h.memberships || []).find((m) => m.tenant_id === tid) || null);
        setLookupDone(true);
      })
      .catch(() => { if (alive) setLookupDone(true); });
    return () => { alive = false; clearTimeout(doneTimer.current); };
  }, [tid]);

  const finishSpin = async (promo) => {
    setSpinning(false);
    setWon(promo);
    if (promo?.qr_payload) {
      try {
        const { toDataURL } = await import('qrcode');
        setQrDataUrl(await toDataURL(promo.qr_payload, { width: 180, margin: 1 }));
      } catch { /* QR gagal render → kode teks tetap tampil */ }
    }
  };

  const spin = async () => {
    if (spinning || generating) return; // guard re-entrancy
    setGenerating(true);
    setError(null);
    try {
      const r = await api.customerGeneratePromo(tid);
      setGenerating(false);
      const amount = r?.spin_result?.discount_amount ?? r?.promo?.discount_amount ?? 0;
      const idx = segmentIndexForAmount(amount);
      const reduceMotion = typeof window.matchMedia === 'function'
        && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (!reduceMotion && typeof window.matchMedia === 'function') {
        // 5 putaran penuh + berhenti di TENGAH segmen hasil (pointer jam-12).
        const target = 5 * 360 + (360 - (idx * SEG_DEG + SEG_DEG / 2));
        setSpinning(true);
        setRotation((prev) => prev - (prev % 360) + target);
        doneTimer.current = setTimeout(() => finishSpin(r.promo), SPIN_MS);
      } else {
        setRotation(360 - (idx * SEG_DEG + SEG_DEG / 2));
        await finishSpin(r.promo);
      }
    } catch (err) {
      setGenerating(false);
      // 422 eligibility: pesan server BI sudah menjelaskan (butuh N poin, dsb).
      setError(err.message || 'Gagal membuat promo.');
    }
  };

  if (lookupDone && membership == null) {
    // Tenant tak dikenal / bukan member → kembali diam-diam (paritas fallback
    // app.dart Flutter yang merender home).
    return <Navigate to="/customer/home" replace />;
  }

  return (
    <div style={{ padding: '18px 18px 24px', display: 'grid', gap: 14, alignContent: 'start' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <button
          type="button"
          aria-label="Kembali"
          onClick={() => navigate('/customer/home')}
          style={{ width: 36, height: 36, borderRadius: 12, background: 'var(--surface)', border: '1.5px solid var(--ink)', boxShadow: '2px 2px 0 var(--ink)', display: 'grid', placeItems: 'center', cursor: 'pointer' }}
        >
          <Icon name="arrowLeft" size={16} strokeWidth={2.2} />
        </button>
        <div>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 18 }}>Putar & Menang</div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-3)' }}>
            {membership?.tenant_name || '…'}
          </div>
        </div>
      </div>

      <Wheel rotation={rotation} spinning={spinning} />

      {error && !won && (
        <div role="alert" style={{ padding: '12px 14px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 12, fontSize: 12.5 }}>
          {error}
        </div>
      )}

      {won ? (
        <Card data-testid="promo-won-card" style={{ display: 'grid', gap: 8, textAlign: 'center', justifyItems: 'center' }}>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 20 }}>🎉 SELAMAT!</div>
          <div style={{ fontSize: 14, fontWeight: 700 }}>{won.name}</div>
          {won.target_product && (
            <div style={{ fontSize: 12.5, color: 'var(--ink-3)' }}>Untuk produk favoritmu: {won.target_product}</div>
          )}
          {qrDataUrl && (
            <img src={qrDataUrl} alt="QR promo" width="180" height="180" style={{ background: '#fff', borderRadius: 12, border: '1.5px solid var(--ink)' }} />
          )}
          <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 15 }}>Kode: {won.code}</div>
          {won.expires_at && (
            <div style={{ fontSize: 11.5, color: 'var(--ink-4)' }}>berlaku s/d {dateOnly(won.expires_at)}</div>
          )}
          <p style={{ fontSize: 11.5, color: 'var(--ink-3)', margin: 0 }}>
            Tunjukkan QR/kode ini ke kasir untuk memakai promo.
          </p>
        </Card>
      ) : (
        <Button data-testid="promo-spin" onClick={spin} disabled={spinning || generating}>
          {generating ? 'Mengundi…' : spinning ? 'Berputar…' : 'PUTAR SEKARANG'}
        </Button>
      )}
    </div>
  );
}
