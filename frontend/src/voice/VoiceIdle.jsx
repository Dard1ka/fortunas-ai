import Pill from '../ui/Pill.jsx';
import Icon from '../ui/Icon.jsx';
import BigMicButton from './BigMicButton.jsx';

export default function VoiceIdle({ onStart, supported = true }) {
  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px 24px 80px',
        textAlign: 'center',
      }}
    >
      <Pill bg="var(--lime)" mono>
        <Icon name="sparkle" size={12} strokeWidth={2.2} /> NEW · VOICE INPUT
      </Pill>

      <h2
        style={{
          fontFamily: 'var(--font-display)',
          fontWeight: 700,
          fontSize: 26,
          letterSpacing: '-0.03em',
          lineHeight: 1.1,
          marginTop: 14,
        }}
      >
        Catat transaksi{' '}
        <em style={{ fontStyle: 'normal', color: 'var(--violet)' }}>tanpa ngetik.</em>
      </h2>

      <p style={{ fontSize: 13.5, color: 'var(--ink-3)', marginTop: 8, maxWidth: 280, lineHeight: 1.5 }}>
        Sebut nomor invoice, produk, jumlah, dan harga. AI akan memformat sendiri.
      </p>

      <div style={{ marginTop: 28 }}>
        <BigMicButton state="idle" onClick={onStart} />
      </div>

      <div
        style={{
          marginTop: 16,
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: 'var(--ink-3)',
          letterSpacing: '0.04em',
        }}
      >
        Ketuk tombol untuk mulai
      </div>

      {!supported && (
        <div
          style={{
            marginTop: 16,
            padding: '10px 14px',
            background: 'var(--peach-soft)',
            border: '1.5px solid var(--ink)',
            borderRadius: 12,
            fontSize: 11.5,
            maxWidth: 320,
            color: 'var(--ink-2)',
            lineHeight: 1.45,
          }}
        >
          Browser kamu belum support voice. Pakai Chrome / Edge / Safari (HTTPS). Atau ketuk mic
          dan input transaksi via text di langkah berikutnya.
        </div>
      )}

      {/* sample phrasing helper */}
      <div
        style={{
          marginTop: 28,
          padding: '14px 16px',
          background: 'var(--surface)',
          border: '1.5px dashed var(--border-soft)',
          borderRadius: 16,
          maxWidth: 320,
          textAlign: 'left',
        }}
      >
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 9.5,
            fontWeight: 700,
            color: 'var(--ink-3)',
            letterSpacing: '0.08em',
            marginBottom: 6,
          }}
        >
          CONTOH UCAPAN
        </div>
        <div style={{ fontSize: 12.5, color: 'var(--ink-2)', lineHeight: 1.55 }}>
          “<span style={{ background: 'var(--lime)', padding: '0 3px' }}>Invoice INV-2024</span>,{' '}
          <span style={{ background: 'var(--peach-soft)', padding: '0 3px' }}>sabun cuci</span>, qty{' '}
          <span style={{ background: 'var(--violet-soft)', padding: '0 3px' }}>10</span>, harga{' '}
          <span style={{ background: 'var(--violet-soft)', padding: '0 3px' }}>delapan ribu lima ratus</span>.”
        </div>
      </div>
    </div>
  );
}
