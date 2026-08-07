const VARIANTS = {
  primary: {
    background: 'var(--violet)',
    color: '#FFFFFF',
    border: '2px solid var(--border)',
    boxShadow: 'var(--shadow-pop-sm)',
  },
  secondary: {
    background: 'var(--surface)',
    color: 'var(--ink)',
    border: '2px solid var(--border)',
    boxShadow: 'var(--shadow-pop-sm)',
  },
  text: {
    background: 'transparent',
    color: 'var(--violet-deep)',
    border: 'none',
    boxShadow: 'none',
  },
};

// Disabled HARUS distinguishable (surface redup + tinta pudar), BUKAN violet
// dipucatkan — regresi "tombol Masuk terlihat disabled" era lama, test-pinned.
const DISABLED = {
  background: 'var(--surface-hover)',
  color: 'var(--ink-4)',
  border: '2px solid var(--border-soft)',
  boxShadow: 'none',
  cursor: 'not-allowed',
};

export default function Button({
  variant = 'primary',
  disabled = false,
  type = 'button',
  style,
  children,
  ...rest
}) {
  return (
    <button
      type={type}
      disabled={disabled}
      style={{
        fontFamily: 'var(--font-body)',
        fontWeight: 700,
        fontSize: 14,
        minHeight: variant === 'text' ? 44 : 48,
        padding: '0 18px',
        borderRadius: 'var(--radius-md)',
        cursor: 'pointer',
        ...VARIANTS[variant],
        ...(disabled ? DISABLED : {}),
        ...style,
      }}
      {...rest}
    >
      {children}
    </button>
  );
}
