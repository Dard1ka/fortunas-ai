import { useLocation } from 'react-router-dom';
import useShellTier from './useShellTier.js';
import {
  isPhoneOnlyRoute,
  MEDIUM_CONTENT_WIDTH,
  EXPANDED_CONTENT_WIDTH,
  PHONE_ONLY_FRAME_WIDTH,
} from './shell.js';
import BottomNav from './BottomNav.jsx';
import NavRail from './NavRail.jsx';

export default function AppShell({ onVoice, children }) {
  const tier = useShellTier();
  const { pathname } = useLocation();

  // Alur customer/order selalu dari HP — di layar lebar tampil sebagai kolom
  // HP di atas backdrop, tanpa navigasi UMKM (mekanisme ter-test).
  if (isPhoneOnlyRoute(pathname)) {
    return (
      <div
        style={{
          minHeight: '100dvh',
          background: 'var(--backdrop-phone)',
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <div
          data-testid="phone-frame"
          style={{ width: '100%', maxWidth: PHONE_ONLY_FRAME_WIDTH, background: 'var(--bg)' }}
        >
          {children}
        </div>
      </div>
    );
  }

  if (tier === 'compact') {
    return (
      <div style={{ minHeight: '100dvh', position: 'relative' }}>
        {/* 120 = clearance bottom-nav mengambang; HANYA di compact */}
        <div style={{ paddingBottom: 120 }}>{children}</div>
        <BottomNav onVoice={onVoice} />
      </div>
    );
  }

  const contentMax = tier === 'expanded' ? EXPANDED_CONTENT_WIDTH : MEDIUM_CONTENT_WIDTH;
  return (
    <div style={{ minHeight: '100dvh', display: 'flex' }}>
      <NavRail extended={tier === 'expanded'} onVoice={onVoice} />
      <main style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
        <div
          data-testid="shell-content"
          style={{ width: '100%', maxWidth: contentMax, paddingBottom: 24 }}
        >
          {children}
        </div>
      </main>
    </div>
  );
}
