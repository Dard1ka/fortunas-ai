import Icon from '../ui/Icon.jsx';

const formatRp = (n) => 'Rp ' + new Intl.NumberFormat('id-ID').format(Number(n) || 0);

export default function VoiceSuccess({ tx }) {
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
      <div
        style={{
          width: 96,
          height: 96,
          borderRadius: '50%',
          background: 'var(--lime)',
          border: '2.5px solid var(--ink)',
          boxShadow: '4px 4px 0 var(--ink)',
          display: 'grid',
          placeItems: 'center',
          animation: 'fortunas-pop .4s cubic-bezier(.2,.7,.3,1.4)',
        }}
      >
        <svg
          width="46"
          height="46"
          viewBox="0 0 24 24"
          fill="none"
          stroke="var(--ink)"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path
            d="M5 12l4.5 4.5L19 7"
            style={{ strokeDasharray: 30, animation: 'fortunas-check .5s ease-out .2s forwards' }}
          />
        </svg>
      </div>

      <h2
        style={{
          fontFamily: 'var(--font-display)',
          fontWeight: 700,
          fontSize: 24,
          letterSpacing: '-0.02em',
          marginTop: 18,
        }}
      >
        Tersimpan!
      </h2>
      <p style={{ fontSize: 13.5, color: 'var(--ink-3)', marginTop: 6, maxWidth: 280, lineHeight: 1.5 }}>
        {tx?.invoice ? `${tx.invoice} · ${formatRp(tx.total)} ` : ''}
        sudah tercatat di Google Sheets dan BigQuery.
      </p>

      <div
        style={{
          marginTop: 22,
          padding: '12px 16px',
          background: 'var(--violet)',
          color: '#fff',
          border: '1.5px solid var(--ink)',
          borderRadius: 14,
          boxShadow: '2px 2px 0 var(--ink)',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          maxWidth: 320,
        }}
      >
        <Icon name="bolt" size={20} stroke="var(--lime)" strokeWidth={2.2} />
        <div style={{ textAlign: 'left' }}>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 13.5, fontWeight: 600 }}>
            +18 detik dihemat
          </div>
          <div style={{ fontSize: 11, opacity: 0.75 }}>vs input manual via keyboard</div>
        </div>
      </div>
    </div>
  );
}
