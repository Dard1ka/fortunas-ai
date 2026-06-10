import Icon from '../ui/Icon.jsx';

export default function BigMicButton({ state = 'idle', onClick, ariaLabel }) {
  const isListening = state === 'listening';
  const size = isListening ? 120 : 104;
  const bg = isListening ? 'var(--ink)' : 'var(--violet)';
  const ring = isListening ? 'var(--violet)' : 'var(--lime)';

  return (
    <div style={{ position: 'relative', width: 160, height: 160, display: 'grid', placeItems: 'center' }}>
      {isListening && [0, 0.6, 1.2].map((d, i) => (
        <span
          key={i}
          style={{
            position: 'absolute',
            inset: 20,
            borderRadius: '50%',
            border: `2px solid ${ring}`,
            animation: `fortunas-pulse 1.8s ease-out ${d}s infinite`,
          }}
        />
      ))}
      <button
        type="button"
        onClick={onClick}
        aria-label={ariaLabel || (isListening ? 'Berhenti mendengar' : 'Mulai mendengar')}
        style={{
          width: size,
          height: size,
          borderRadius: '50%',
          background: bg,
          color: isListening ? 'var(--lime)' : '#fff',
          border: '2px solid var(--ink)',
          boxShadow: '4px 4px 0 var(--ink)',
          cursor: 'pointer',
          display: 'grid',
          placeItems: 'center',
          transition: 'width .25s, height .25s, background .25s',
          animation: state === 'idle' ? 'fortunas-mic-glow 2.6s ease-in-out infinite' : 'none',
        }}
      >
        <Icon
          name="micFilled"
          size={size * 0.42}
          stroke={isListening ? 'var(--lime)' : '#fff'}
          strokeWidth={2}
        />
      </button>
    </div>
  );
}
