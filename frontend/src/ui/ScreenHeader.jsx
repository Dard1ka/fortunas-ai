import BrandMark from './BrandMark.jsx';

export default function ScreenHeader({ subtitle = 'UMKM Analytics', online = true, right }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '14px 18px 12px',
        gap: 12,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <BrandMark size={36} />
        <div>
          <div
            style={{
              fontFamily: 'var(--font-display)',
              fontWeight: 700,
              fontSize: 17,
              letterSpacing: '-0.02em',
              lineHeight: 1,
            }}
          >
            Fortunas <span style={{ color: 'var(--violet)' }}>AI</span>
          </div>
          <div
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 9,
              color: 'var(--ink-3)',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              marginTop: 3,
            }}
          >
            {subtitle}
          </div>
        </div>
      </div>
      {right || (
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '6px 10px',
            background: 'var(--surface)',
            border: '1.5px solid var(--ink)',
            borderRadius: 999,
            fontSize: 10,
            fontWeight: 600,
            boxShadow: '2px 2px 0 var(--ink)',
          }}
        >
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: online ? 'var(--success)' : 'var(--ink-4)',
            }}
          />
          AI online
        </div>
      )}
    </div>
  );
}
