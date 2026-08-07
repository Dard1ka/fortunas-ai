import { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import Button from '../ui/Button.jsx';
import Input from '../ui/Input.jsx';
import { api, setCustomerToken } from '../api/client.js';
import { CUST_PHONE_KEY } from './CustomerPhoneScreen.jsx';

export const CUST_PROFILE_KEY = 'fortunas_customer_profile';

export default function CustomerProfileScreen() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [birthDate, setBirthDate] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  let phone = '';
  try { phone = sessionStorage.getItem(CUST_PHONE_KEY) || ''; } catch { /* ignore */ }

  if (!phone) return <Navigate to="/customer/login" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const digits = phone.replace(/\D/g, '');
      // Jalur dev-token (FORTUNAS_DEV_AUTH di server): "dev:<uid>:<phone>".
      // Saat Firebase Phone Auth aktif, token ini diganti ID token asli.
      const res = await api.customerBootstrap({
        firebase_id_token: `dev:${digits}:${phone}`,
        username: username.trim(),
        birth_date: birthDate,
      });
      setCustomerToken(res.access_token);
      try { localStorage.setItem(CUST_PROFILE_KEY, JSON.stringify(res.profile)); } catch { /* ignore */ }
      navigate('/customer/home');
    } catch (err) {
      setError(err.status === 503
        ? 'Login pelanggan belum dikonfigurasi di server. Hubungi pemilik toko.'
        : err.message || 'Gagal membuat akun.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 14, padding: 20 }}>
      <form onSubmit={submit} style={{ display: 'grid', gap: 12 }}>
        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 18 }}>Lengkapi profilmu</div>
        <Input
          id="cust-username"
          label="Nama panggilan"
          placeholder="mis. Sari"
          minLength={2}
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <Input
          id="cust-birth"
          label="Tanggal lahir"
          type="date"
          value={birthDate}
          onChange={(e) => setBirthDate(e.target.value)}
          required
        />
        {error && (
          <div role="alert" style={{ padding: '10px 12px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 10, fontSize: 12.5 }}>
            {error}
          </div>
        )}
        <Button type="submit" disabled={busy || username.trim().length < 2 || !birthDate} style={{ width: '100%' }}>
          {busy ? 'Membuat akun…' : 'Selesai & masuk'}
        </Button>
      </form>
    </div>
  );
}
