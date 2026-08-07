import { useState } from 'react';

// Input boxed (bukan underline). Fokus = DUA sinyal: border violet DAN lebih
// tebal (terbaca juga oleh mata yang tak membedakan violet vs ink).
export default function Input({ id, label, error, hint, style, ...rest }) {
  const [focus, setFocus] = useState(false);
  const borderColor = error ? 'var(--error)' : focus ? 'var(--violet)' : 'var(--border)';
  return (
    <div style={{ display: 'grid', gap: 6 }}>
      {label && (
        <label
          htmlFor={id}
          style={{
            fontSize: 13,
            fontWeight: 600,
            color: focus ? 'var(--violet-deep)' : 'var(--ink-3)',
          }}
        >
          {label}
        </label>
      )}
      <input
        id={id}
        onFocus={() => setFocus(true)}
        onBlur={() => setFocus(false)}
        style={{
          fontFamily: 'var(--font-body)',
          fontSize: 14,
          color: 'var(--ink)',
          background: 'var(--surface)',
          padding: 14,
          border: `${focus || error ? 2 : 1.5}px solid ${borderColor}`,
          borderRadius: 'var(--radius-md)',
          outline: 'none',
          width: '100%',
          boxSizing: 'border-box',
          ...style,
        }}
        {...rest}
      />
      {error ? (
        <span role="alert" style={{ fontSize: 11.5, color: 'var(--error)' }}>
          {error}
        </span>
      ) : hint ? (
        <span style={{ fontSize: 12, color: 'var(--ink-4)' }}>{hint}</span>
      ) : null}
    </div>
  );
}
