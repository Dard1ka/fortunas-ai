export default function Card({ style, children, ...rest }) {
  return (
    <div
      style={{
        background: 'var(--surface)',
        border: '2px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        padding: 20,
        ...style,
      }}
      {...rest}
    >
      {children}
    </div>
  );
}
