import { useLocation, useNavigate } from 'react-router-dom';
import Icon from './Icon.jsx';
import BrandMark from './BrandMark.jsx';

// Item nav = mirror BottomNav.jsx (satu set navigasi, dua presentasi).
const ITEMS = [
  { id: 'home',     label: 'Tanya',    icon: 'chat',    path: '/' },
  { id: 'briefing', label: 'Briefing', icon: 'chart',   path: '/briefing' },
  { id: 'voice',    label: 'Voice',    icon: 'mic',     primary: true },
  { id: 'history',  label: 'Riwayat',  icon: 'history', path: '/history' },
  { id: 'me',       label: 'Saya',     icon: 'user',    path: '/me' },
];

// Rail kiri untuk tier >= medium: 76px ikon-saja, 200px ikon+label (extended).
export default function NavRail({ extended = false, onVoice }) {
  const navigate = useNavigate();
  const { pathname } = useLocation();

  return (
    <nav
      data-testid="nav-rail"
      aria-label="Navigasi utama"
      style={{
        width: extended ? 200 : 76,
        flexShrink: 0,
        position: 'sticky',
        top: 0,
        height: '100dvh',
        boxSizing: 'border-box',
        background: 'var(--surface)',
        borderRight: '2px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: extended ? 'stretch' : 'center',
        gap: 6,
        padding: extended ? '18px 12px' : '18px 8px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: extended ? 'flex-start' : 'center', padding: extended ? '0 8px 14px' : '0 0 14px' }}>
        <BrandMark size={30} />
      </div>

      {ITEMS.map((it) => {
        if (it.primary) {
          return (
            <button
              key={it.id}
              type="button"
              onClick={onVoice}
              aria-label="Voice"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: extended ? 'flex-start' : 'center',
                gap: 10,
                margin: '6px 0',
                padding: extended ? '12px 14px' : 12,
                borderRadius: 14,
                background: 'var(--violet)',
                color: '#fff',
                border: '1.5px solid var(--ink)',
                boxShadow: 'var(--shadow-pop-sm)',
                cursor: 'pointer',
              }}
            >
              <Icon name="mic" size={20} stroke="#fff" strokeWidth={2} />
              {extended && (
                <span style={{ fontSize: 13, fontWeight: 700, fontFamily: 'var(--font-body)' }}>Voice</span>
              )}
            </button>
          );
        }
        const active = pathname === it.path || (it.path === '/' && pathname.startsWith('/result'));
        return (
          <button
            key={it.id}
            type="button"
            onClick={() => navigate(it.path)}
            aria-current={active ? 'page' : undefined}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: extended ? 'flex-start' : 'center',
              gap: 10,
              padding: extended ? '10px 14px' : 10,
              borderRadius: 12,
              border: 'none',
              background: active ? 'var(--violet-soft)' : 'transparent',
              color: active ? 'var(--violet-deep)' : 'var(--ink-4)',
              cursor: 'pointer',
              width: '100%',
              boxSizing: 'border-box',
            }}
          >
            <Icon
              name={it.icon}
              size={20}
              stroke={active ? 'var(--violet-deep)' : 'var(--ink-4)'}
              strokeWidth={active ? 2 : 1.6}
            />
            {extended && (
              <span style={{ fontSize: 13, fontWeight: active ? 700 : 500, fontFamily: 'var(--font-body)' }}>
                {it.label}
              </span>
            )}
          </button>
        );
      })}
    </nav>
  );
}
