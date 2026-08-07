import useShellTier from './useShellTier.js';
import { FORM_PANE_WIDTH } from './shell.js';

// >=medium: form jadi kartu 420px terpusat dua sumbu di atas --bg.
// compact: anak dirender apa adanya (HP = jalur utama, nol perubahan visual).
// Viewport pendek tetap bisa scroll (overflowY di wrapper), tidak overflow.
export default function FormPane({ children }) {
  const tier = useShellTier();
  if (tier === 'compact') return children;
  return (
    <div
      style={{
        minHeight: '100dvh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg)',
        overflowY: 'auto',
        padding: 24,
      }}
    >
      <div
        data-testid="form-pane-card"
        style={{
          width: '100%',
          maxWidth: FORM_PANE_WIDTH,
          background: 'var(--surface)',
          border: '2px solid var(--border)',
          borderRadius: 'var(--radius-xl)',
          boxShadow: 'var(--shadow-pop)',
          padding: '24px 20px 24px 24px',
        }}
      >
        {children}
      </div>
    </div>
  );
}
