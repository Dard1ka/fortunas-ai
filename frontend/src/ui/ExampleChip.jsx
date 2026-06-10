export default function ExampleChip({ children, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        textAlign: 'left',
        padding: '12px 14px',
        background: 'var(--surface)',
        border: '1.5px solid var(--ink)',
        borderRadius: 14,
        fontFamily: 'var(--font-body)',
        fontSize: 13,
        fontWeight: 500,
        color: 'var(--ink)',
        cursor: 'pointer',
        boxShadow: '2px 2px 0 var(--ink)',
        lineHeight: 1.4,
        display: 'flex',
        alignItems: 'flex-start',
        gap: 8,
        width: '100%',
      }}
    >
      <span style={{ color: 'var(--ink-4)' }}>→</span>
      <span>{children}</span>
    </button>
  );
}
