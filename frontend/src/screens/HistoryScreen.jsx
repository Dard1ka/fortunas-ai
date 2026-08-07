import { useEffect, useState } from 'react';
import ScreenHeader from '../ui/ScreenHeader.jsx';
import Pill from '../ui/Pill.jsx';
import Icon from '../ui/Icon.jsx';
import { api, voiceHistoryKey } from '../api/client.js';

function readVoiceHistory() {
  try {
    return JSON.parse(localStorage.getItem(voiceHistoryKey()) || '[]');
  } catch { return []; }
}

function rupiah(n) {
  return 'Rp ' + new Intl.NumberFormat('id-ID').format(Number(n) || 0);
}

export default function HistoryScreen() {
  const [voiceTx] = useState(readVoiceHistory);
  const [briefings, setBriefings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const ctrl = new AbortController();
    api.reportDaily(ctrl.signal)
      .then((data) => {
        setBriefings(data?.history || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
    return () => ctrl.abort();
  }, []);

  return (
    <div style={{ minHeight: '100%' }}>
      <ScreenHeader subtitle="Riwayat" />

      <div style={{ padding: '4px 18px 14px' }}>
        <Pill bg="var(--peach)" mono>RIWAYAT</Pill>
        <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 22, letterSpacing: '-0.02em', margin: '10px 0 4px' }}>
          Aktivitas terakhir
        </h2>
        <p style={{ color: 'var(--ink-3)', fontSize: 12.5, lineHeight: 1.5 }}>
          Transaksi voice + briefing harian yang tersimpan.
        </p>
      </div>

      {/* Voice transactions */}
      <div style={{ padding: '0 18px 18px' }}>
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            fontWeight: 600,
            color: 'var(--ink-3)',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            marginBottom: 10,
          }}
        >
          Transaksi voice ({voiceTx.length})
        </div>
        {voiceTx.length === 0 ? (
          <EmptyHint>Belum ada transaksi voice. Tekan tombol mic di bawah untuk mulai.</EmptyHint>
        ) : (
          <div style={{ display: 'grid', gap: 8 }}>
            {voiceTx.slice(0, 10).map((tx, i) => (
              <div
                key={`${tx.invoice}-${i}`}
                style={{
                  background: 'var(--surface)',
                  border: '1.5px solid var(--ink)',
                  borderRadius: 14,
                  padding: '12px 14px',
                  boxShadow: '2px 2px 0 var(--ink)',
                  display: 'grid',
                  gridTemplateColumns: '36px 1fr auto',
                  gap: 12,
                  alignItems: 'center',
                }}
              >
                <div
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: 10,
                    background: 'var(--violet-soft)',
                    border: '1.5px solid var(--ink)',
                    display: 'grid',
                    placeItems: 'center',
                  }}
                >
                  <Icon name="mic" size={16} stroke="var(--violet-deep)" strokeWidth={2} />
                </div>
                <div>
                  <div style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 13.5 }}>
                    {tx.product} · {tx.qty}×
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5, color: 'var(--ink-3)', marginTop: 2 }}>
                    {tx.invoice} · {tx.savedAt ? new Date(tx.savedAt).toLocaleString('id-ID') : '—'}
                  </div>
                </div>
                <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 13, color: 'var(--violet)' }}>
                  {rupiah(tx.total)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Briefing history */}
      <div style={{ padding: '0 18px 24px' }}>
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            fontWeight: 600,
            color: 'var(--ink-3)',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            marginBottom: 10,
          }}
        >
          Briefing harian ({briefings.length})
        </div>
        {loading ? (
          <EmptyHint>Memuat…</EmptyHint>
        ) : briefings.length === 0 ? (
          <EmptyHint>Belum ada briefing tersimpan. Jalankan dari layar Briefing.</EmptyHint>
        ) : (
          <div style={{ display: 'grid', gap: 8 }}>
            {briefings.map((b) => (
              <div
                key={b.generated_at}
                style={{
                  background: 'var(--surface)',
                  border: '1.5px solid var(--ink)',
                  borderRadius: 14,
                  padding: '12px 14px',
                  boxShadow: '2px 2px 0 var(--ink)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 14 }}>
                    {b.date}
                  </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-3)' }}>
                    {b.sections?.length || 0} analisis
                  </span>
                </div>
                <p style={{ fontSize: 12.5, color: 'var(--ink-2)', marginTop: 6, lineHeight: 1.45 }}>
                  {b.executive_summary?.slice(0, 220)}
                  {b.executive_summary?.length > 220 ? '…' : ''}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function EmptyHint({ children }) {
  return (
    <div
      style={{
        padding: '14px 16px',
        background: 'var(--surface-soft)',
        border: '1.5px dashed var(--border-soft)',
        borderRadius: 12,
        color: 'var(--ink-3)',
        fontSize: 12.5,
        lineHeight: 1.5,
      }}
    >
      {children}
    </div>
  );
}
