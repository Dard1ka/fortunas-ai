export default function Pill({
  children,
  bg = 'var(--lime)',
  color = 'var(--ink)',
  mono = false,
  sm = false,
  style: extra,
}) {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: sm ? '3px 8px' : '4px 10px',
        background: bg,
        color,
        border: '1.5px solid var(--ink)',
        borderRadius: 999,
        fontFamily: mono ? 'var(--font-mono)' : 'var(--font-body)',
        fontWeight: 600,
        fontSize: sm ? 10 : 11,
        letterSpacing: mono ? '0.04em' : 0,
        ...extra,
      }}
    >
      {children}
    </span>
  );
}
