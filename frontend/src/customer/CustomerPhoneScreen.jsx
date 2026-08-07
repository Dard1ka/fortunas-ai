import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BrandMark from '../ui/BrandMark.jsx';
import Button from '../ui/Button.jsx';
import Input from '../ui/Input.jsx';

export const CUST_PHONE_KEY = 'fortunas_cust_phone';

export default function CustomerPhoneScreen() {
  const navigate = useNavigate();
  const [phone, setPhone] = useState('');
  const [error, setError] = useState(null);

  const digits = phone.replace(/\D/g, '');
  const submit = (e) => {
    e.preventDefault();
    if (digits.length < 9) {
      setError('Nomor HP minimal 9 digit.');
      return;
    }
    try { sessionStorage.setItem(CUST_PHONE_KEY, phone.trim()); } catch { /* ignore */ }
    navigate('/customer/otp');
  };

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 18, padding: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <BrandMark size={40} />
        <div>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 20 }}>
            Fortunas <span style={{ color: 'var(--violet)' }}>AI</span>
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-3)', letterSpacing: '0.08em' }}>
            AREA PELANGGAN
          </div>
        </div>
      </div>

      <form onSubmit={submit} style={{ display: 'grid', gap: 12 }}>
        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 18 }}>Masuk pelanggan</div>
        <p style={{ fontSize: 12.5, color: 'var(--ink-3)', lineHeight: 1.5 }}>
          Kumpulkan poin & tunjukkan QR-mu saat belanja di UMKM favorit.
        </p>
        <Input
          id="cust-phone"
          label="Nomor HP"
          type="tel"
          inputMode="tel"
          placeholder="mis. 0812xxxxxxx"
          value={phone}
          onChange={(e) => { setPhone(e.target.value); setError(null); }}
          error={error}
          required
        />
        <Button type="submit" style={{ width: '100%' }}>Kirim kode OTP</Button>
      </form>
    </div>
  );
}
