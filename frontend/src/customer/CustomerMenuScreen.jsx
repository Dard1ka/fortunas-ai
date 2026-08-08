import { useNavigate } from 'react-router-dom';
import Card from '../ui/Card.jsx';
import Button from '../ui/Button.jsx';
import { clearCustomerToken } from '../api/client.js';
import { CUST_PROFILE_KEY } from './CustomerProfileScreen.jsx';

export default function CustomerMenuScreen() {
  const navigate = useNavigate();
  let profile = null;
  try { profile = JSON.parse(localStorage.getItem(CUST_PROFILE_KEY) || 'null'); } catch { /* ignore */ }

  const logout = () => {
    clearCustomerToken();
    try { localStorage.removeItem(CUST_PROFILE_KEY); } catch { /* ignore */ }
    navigate('/customer/login', { replace: true });
  };

  return (
    <div style={{ padding: '18px 18px 24px', display: 'grid', gap: 12, alignContent: 'start' }}>
      <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 20 }}>Menu</div>
      <Card style={{ display: 'grid', gap: 6 }}>
        <div style={{ fontSize: 14, fontWeight: 700 }}>{profile?.username || 'Pelanggan'}</div>
        {profile?.phone_number && (
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11.5, color: 'var(--ink-3)' }}>{profile.phone_number}</div>
        )}
        {profile?.customer_user_id && (
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-4)' }}>ID: {profile.customer_user_id}</div>
        )}
      </Card>
      {/* Tile navigasi (paritas customer_menu_screen Flutter). */}
      <Card style={{ display: 'grid', gap: 0, padding: 8 }}>
        <button type="button" data-testid="menu-tile-qr" onClick={() => navigate('/customer/qr')} style={tile}>
          QR Identitas Saya
        </button>
        <button type="button" data-testid="menu-tile-points" onClick={() => navigate('/customer/points')} style={{ ...tile, borderTop: '1px dashed var(--border-soft)' }}>
          Poin & Promo
        </button>
      </Card>

      <Button variant="secondary" onClick={logout} style={{ color: 'var(--error)' }}>Keluar</Button>
    </div>
  );
}

const tile = {
  display: 'block', width: '100%', textAlign: 'left', padding: '13px 10px',
  background: 'transparent', border: 'none', cursor: 'pointer',
  fontFamily: 'var(--font-body)', fontSize: 13.5, fontWeight: 600, color: 'var(--ink)',
};
