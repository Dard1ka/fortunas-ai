import TypedTranscript from './TypedTranscript.jsx';
import Waveform from './Waveform.jsx';

export default function VoiceListening({ transcript, state, onStop, supported = true, textFallback, onTextChange }) {
  const parsing = state === 'parsing';

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '20px 22px 100px' }}>
      {/* live transcript card */}
      <div
        style={{
          background: 'var(--surface)',
          border: '1.5px solid var(--ink)',
          borderRadius: 18,
          padding: '18px 18px 20px',
          boxShadow: '2px 2px 0 var(--ink)',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 10,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: parsing ? 'var(--violet)' : 'var(--error)',
                animation: 'fortunas-pulse 1.2s ease-in-out infinite',
              }}
            />
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                fontWeight: 700,
                color: 'var(--ink-3)',
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
              }}
            >
              {parsing ? 'Mengurai…' : 'Live transkrip'}
            </span>
          </div>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-3)' }}>
            id-ID
          </span>
        </div>

        {supported ? (
          <TypedTranscript text={transcript} />
        ) : (
          <textarea
            value={textFallback}
            onChange={(e) => onTextChange(e.target.value)}
            placeholder="Ketik transaksi: sabun cuci, qty 10, harga 8500, pelanggan Budi"
            rows={4}
            style={{
              width: '100%',
              fontFamily: 'var(--font-body)',
              fontSize: 14,
              lineHeight: 1.5,
              color: 'var(--ink)',
              background: 'var(--surface-soft)',
              border: '1.5px solid var(--ink)',
              borderRadius: 12,
              padding: '10px 12px',
              resize: 'vertical',
              outline: 'none',
            }}
          />
        )}
      </div>

      {/* waveform */}
      {supported && (
        <div
          style={{
            marginTop: 18,
            padding: '14px 16px',
            background: 'var(--ink)',
            borderRadius: 18,
            border: '1.5px solid var(--ink)',
            boxShadow: '2px 2px 0 var(--ink)',
          }}
        >
          <Waveform active={!parsing} color="var(--lime)" />
        </div>
      )}

      {parsing && (
        <div
          style={{
            marginTop: 14,
            padding: '14px 16px',
            background: 'var(--violet-soft)',
            border: '1.5px solid var(--violet)',
            borderRadius: 14,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <div
            style={{
              width: 24,
              height: 24,
              borderRadius: '50%',
              border: '2.5px solid var(--violet-soft)',
              borderTopColor: 'var(--violet)',
              animation: 'fortunas-spin 0.7s linear infinite',
            }}
          />
          <div>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 13.5 }}>
              AI mengurai transaksi…
            </div>
            <div style={{ fontSize: 11.5, color: 'var(--ink-3)' }}>Local LLM · Qwen3:8b</div>
          </div>
        </div>
      )}

      <div style={{ flex: 1 }} />
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 14,
          paddingBottom: 14,
        }}
      >
        <button
          type="button"
          onClick={onStop}
          disabled={parsing}
          aria-label="Selesai bicara"
          style={{
            height: 56,
            width: 56,
            borderRadius: '50%',
            background: parsing ? 'var(--ink-4)' : 'var(--error)',
            color: '#fff',
            border: '2px solid var(--ink)',
            boxShadow: '3px 3px 0 var(--ink)',
            display: 'grid',
            placeItems: 'center',
            cursor: parsing ? 'default' : 'pointer',
          }}
        >
          <span style={{ width: 16, height: 16, background: '#fff', borderRadius: 3 }} />
        </button>
      </div>
      <div
        style={{
          textAlign: 'center',
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: 'var(--ink-3)',
        }}
      >
        {parsing ? 'Mohon tunggu…' : 'Ketuk tombol stop saat selesai'}
      </div>
    </div>
  );
}
