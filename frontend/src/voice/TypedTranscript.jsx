// Live transcript renderer. Unlike the mockup version (which animates a
// hardcoded string char-by-char), this just shows whatever string is passed in
// — the Web Speech API stream already arrives incrementally.

export default function TypedTranscript({ text, placeholder = 'Sebut transaksi…' }) {
  const empty = !text || text.length === 0;
  return (
    <div
      style={{
        fontFamily: 'var(--font-display)',
        fontSize: 18,
        fontWeight: 500,
        lineHeight: 1.45,
        letterSpacing: '-0.01em',
        color: empty ? 'var(--ink-3)' : 'var(--ink)',
        minHeight: 84,
      }}
    >
      {empty ? placeholder : text}
      <span
        style={{
          display: 'inline-block',
          width: 2,
          height: 18,
          background: 'var(--violet)',
          marginLeft: 2,
          verticalAlign: 'middle',
          animation: 'fortunas-caret 1s steps(1) infinite',
        }}
      />
    </div>
  );
}
