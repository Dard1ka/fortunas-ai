import { useEffect, useState } from 'react';
import { Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import Icon from '../ui/Icon.jsx';
import { getCustomerToken } from '../api/client.js';
import CustomerPhoneScreen from './CustomerPhoneScreen.jsx';
import CustomerOtpScreen from './CustomerOtpScreen.jsx';
import CustomerProfileScreen from './CustomerProfileScreen.jsx';
import CustomerHomeScreen from './CustomerHomeScreen.jsx';
import CustomerQrScreen from './CustomerQrScreen.jsx';
import CustomerMenuScreen from './CustomerMenuScreen.jsx';
import CustomerHistoryScreen from './CustomerHistoryScreen.jsx';
import CustomerPointsScreen from './CustomerPointsScreen.jsx';
import CustomerPromoScreen from './CustomerPromoScreen.jsx';

// 5 tab (paritas customer_bottom_nav Flutter): Beranda · Riwayat · QR (tengah,
// ditonjolkan) · Poin · Profil. /customer/promo SENGAJA di luar nav.
const TABS = [
  { id: 'home',    label: 'Beranda', icon: 'home',    path: '/customer/home' },
  { id: 'history', label: 'Riwayat', icon: 'history', path: '/customer/history' },
  { id: 'qr',      label: 'QR Saya', icon: 'sparkle', path: '/customer/qr' },
  { id: 'points',  label: 'Poin',    icon: 'coin',    path: '/customer/points' },
  { id: 'menu',    label: 'Profil',  icon: 'user',    path: '/customer/menu' },
];

function CustomerNav() {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  return (
    <nav
      data-testid="customer-nav"
      aria-label="Navigasi pelanggan"
      style={{
        position: 'sticky',
        bottom: 0,
        background: 'var(--surface)',
        borderTop: '2px solid var(--border)',
        display: 'grid',
        gridTemplateColumns: `repeat(${TABS.length}, 1fr)`,
        padding: '8px 6px max(env(safe-area-inset-bottom), 10px)',
      }}
    >
      {TABS.map((t) => {
        const active = pathname === t.path;
        return (
          <button
            key={t.id}
            type="button"
            onClick={() => navigate(t.path)}
            aria-current={active ? 'page' : undefined}
            style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3,
              padding: '6px 0', border: 'none', background: 'transparent',
              color: active ? 'var(--violet-deep)' : 'var(--ink-4)', cursor: 'pointer',
            }}
          >
            <Icon name={t.icon} size={20} stroke={active ? 'var(--violet-deep)' : 'var(--ink-4)'} strokeWidth={active ? 2 : 1.6} />
            <span style={{ fontSize: 10, fontWeight: active ? 700 : 500, fontFamily: 'var(--font-body)' }}>{t.label}</span>
          </button>
        );
      })}
    </nav>
  );
}

// Gate rute customer: butuh customer token (TERPISAH dari sesi UMKM).
// nav={false} untuk layar penuh tanpa bottom-nav (promo — paritas Flutter
// yang menaruh /customer/promo di luar ShellRoute).
function Gated({ children, nav = true }) {
  const [token, setTokenState] = useState(getCustomerToken());
  useEffect(() => {
    const onLogout = () => setTokenState('');
    window.addEventListener('customer:logout', onLogout);
    return () => window.removeEventListener('customer:logout', onLogout);
  }, []);
  if (!token) return <Navigate to="/customer/login" replace />;
  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 1 }}>{children}</div>
      {nav && <CustomerNav />}
    </div>
  );
}

export default function CustomerApp() {
  return (
    <Routes>
      <Route path="/customer/login"   element={<CustomerPhoneScreen />} />
      <Route path="/customer/otp"     element={<CustomerOtpScreen />} />
      <Route path="/customer/profile" element={<CustomerProfileScreen />} />
      <Route path="/customer/home"    element={<Gated><CustomerHomeScreen /></Gated>} />
      <Route path="/customer/history" element={<Gated><CustomerHistoryScreen /></Gated>} />
      <Route path="/customer/qr"      element={<Gated><CustomerQrScreen /></Gated>} />
      <Route path="/customer/points"  element={<Gated><CustomerPointsScreen /></Gated>} />
      <Route path="/customer/menu"    element={<Gated><CustomerMenuScreen /></Gated>} />
      <Route path="/customer/promo/:tenantId" element={<Gated nav={false}><CustomerPromoScreen /></Gated>} />
      <Route path="*"                 element={<Navigate to="/customer/login" replace />} />
    </Routes>
  );
}
