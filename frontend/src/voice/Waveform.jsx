export default function Waveform({ active = true, color = 'var(--violet)', count = 28 }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 5,
        height: 80,
      }}
    >
      {Array.from({ length: count }).map((_, i) => {
        const seed = (Math.sin(i * 1.27) + 1) * 0.5;
        const dur = 0.7 + seed * 0.6;
        const delay = (i % 7) * 0.08 + seed * 0.2;
        const tall = 18 + Math.abs(Math.sin(i * 0.7)) * 56;
        return (
          <span
            key={i}
            style={{
              width: 4,
              height: tall,
              borderRadius: 999,
              background: color,
              display: 'inline-block',
              transformOrigin: 'center',
              animation: active ? `fortunas-bar ${dur}s ease-in-out ${delay}s infinite` : 'none',
              opacity: active ? 1 : 0.35,
            }}
          />
        );
      })}
    </div>
  );
}
