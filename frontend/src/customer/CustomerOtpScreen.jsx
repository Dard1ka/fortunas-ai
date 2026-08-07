import { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import Button from '../ui/Button.jsx';
import Input from '../ui/Input.jsx';
import { CUST_PHONE_KEY } from './CustomerPhoneScreen.jsx';

export default function CustomerOtpScreen() {
  const navigate = useNavigate();
  const [otp, setOtp] = useState('');
  const [error, setError] = useState(null);
  let phone = '';
  try { phone = sessionStorage.getItem(CUST_PHONE_KEY) || ''; } catch { /* ignore */ }

  if (!phone) return <Navigate to="/customer/login" replace />;

  const submit = (e) => {
    e.preventDefault();
    if (!/^\d{6}$/.test(otp.trim())) {
      setError('Kode OTP harus 6 digit.');
      return;
    }
    navigate('/customer/profile');
  };

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 14, padding: 20 }}>
      <form onSubmit={submit} style={{ display: 'grid', gap: 12 }}>
        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 18 }}>Masukkan kode OTP</div>
        <p style={{ fontSize: 12.5, color: 'var(--ink-3)', lineHeight: 1.5 }}>
          Kode dikirim ke <strong>{phone}</strong>.
        </p>
        <Input
          id="cust-otp"
          label="Kode OTP (6 digit)"
          inputMode="numeric"
          maxLength={6}
          placeholder="••••••"
          value={otp}
          onChange={(e) => { setOtp(e.target.value); setError(null); }}
          error={error}
          required
        />
        <Button type="submit" style={{ width: '100%' }}>Lanjut</Button>
        <p style={{ fontSize: 11, color: 'var(--ink-4)', lineHeight: 1.5 }}>
          Mode pengembangan: verifikasi OTP Firebase belum aktif di server — kode 6 digit apa pun
          diterima. Nomor HP-mu tetap identitas akunmu.
        </p>
      </form>
    </div>
  );
}
