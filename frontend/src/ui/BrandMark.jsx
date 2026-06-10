export default function BrandMark({ size = 36 }) {
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: size * 0.32,
        background: 'var(--ink)',
        color: 'var(--lime)',
        display: 'grid',
        placeItems: 'center',
        fontFamily: 'var(--font-display)',
        fontWeight: 700,
        fontSize: size * 0.5,
        transform: 'rotate(-4deg)',
        boxShadow: '2px 2px 0 var(--ink)',
        flexShrink: 0,
      }}
    >
      F
    </div>
  );
}
