export default function ModeTabs({ value, onChange, tabs }) {
  return (
    <div
      style={{
        display: 'inline-flex',
        background: 'var(--surface)',
        border: '1.5px solid var(--ink)',
        borderRadius: 999,
        padding: 3,
        boxShadow: '2px 2px 0 var(--ink)',
        margin: '0 18px',
        gap: 2,
      }}
    >
      {tabs.map((t) => {
        const active = value === t.id;
        return (
          <button
            key={t.id}
            type="button"
            onClick={() => onChange(t.id)}
            style={{
              padding: '8px 14px',
              border: 'none',
              borderRadius: 999,
              background: active ? 'var(--ink)' : 'transparent',
              color: active ? 'var(--lime)' : 'var(--ink-3)',
              fontFamily: 'var(--font-body)',
              fontWeight: 600,
              fontSize: 12,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'background .18s, color .18s',
            }}
          >
            {t.label}
          </button>
        );
      })}
    </div>
  );
}
