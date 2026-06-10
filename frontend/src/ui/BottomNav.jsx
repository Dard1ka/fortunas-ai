import { useLocation, useNavigate } from 'react-router-dom';
import Icon from './Icon.jsx';

const ITEMS = [
  { id: 'home',      label: 'Tanya',    icon: 'chat',    path: '/' },
  { id: 'briefing',  label: 'Briefing', icon: 'chart',   path: '/briefing' },
  { id: 'voice',     label: 'Voice',    icon: 'mic',     primary: true },
  { id: 'history',   label: 'Riwayat',  icon: 'history', path: '/history' },
  { id: 'me',        label: 'Saya',     icon: 'user',    path: '/me' },
];

export default function BottomNav({ onVoice }) {
  const navigate = useNavigate();
  const { pathname } = useLocation();

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 30,
        paddingBottom: 'max(env(safe-area-inset-bottom), 16px)',
        paddingTop: 8,
        background:
          'linear-gradient(to top, rgba(250,247,240,0.98) 60%, rgba(250,247,240,0))',
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          margin: '0 12px',
          background: 'var(--surface)',
          border: '1.5px solid var(--ink)',
          borderRadius: 24,
          boxShadow: '3px 3px 0 var(--ink)',
          display: 'grid',
          gridTemplateColumns: 'repeat(5, 1fr)',
          padding: '8px 6px',
          alignItems: 'center',
          pointerEvents: 'auto',
        }}
      >
        {ITEMS.map((it) => {
          if (it.primary) {
            return (
              <button
                key={it.id}
                type="button"
                onClick={onVoice}
                aria-label="Voice"
                style={{
                  justifySelf: 'center',
                  width: 52,
                  height: 52,
                  borderRadius: 16,
                  background: 'var(--violet)',
                  color: '#fff',
                  border: '1.5px solid var(--ink)',
                  boxShadow: '3px 3px 0 var(--ink)',
                  cursor: 'pointer',
                  display: 'grid',
                  placeItems: 'center',
                  marginTop: -22,
                  animation: 'fortunas-mic-glow 2.4s ease-in-out infinite',
                }}
              >
                <Icon name="mic" size={24} stroke="#fff" strokeWidth={2} />
              </button>
            );
          }
          const active = pathname === it.path || (it.path === '/' && pathname.startsWith('/result'));
          return (
            <button
              key={it.id}
              type="button"
              onClick={() => navigate(it.path)}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 3,
                padding: '6px 0',
                border: 'none',
                background: 'transparent',
                color: active ? 'var(--ink)' : 'var(--ink-4)',
                cursor: 'pointer',
              }}
            >
              <Icon
                name={it.icon}
                size={20}
                stroke={active ? 'var(--ink)' : 'var(--ink-4)'}
                strokeWidth={active ? 2 : 1.6}
              />
              <span
                style={{
                  fontSize: 10,
                  fontWeight: active ? 700 : 500,
                  fontFamily: 'var(--font-body)',
                }}
              >
                {it.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
