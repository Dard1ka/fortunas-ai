import { useState } from 'react';
import ScreenHeader from '../ui/ScreenHeader.jsx';
import Pill from '../ui/Pill.jsx';
import Icon from '../ui/Icon.jsx';
import Button from '../ui/Button.jsx';
import Input from '../ui/Input.jsx';
import Card from '../ui/Card.jsx';
import { api } from '../api/client.js';

// Alasan kegagalan dari backend (schemas.QRValidateResponse.reason) → BI.
const REASON_ID = {
  expired: 'QR kedaluwarsa (berlaku 90 detik) — minta pelanggan perbarui QR-nya.',
  replayed: 'QR sudah pernah dipakai — QR sekali pakai, minta pelanggan tampilkan QR baru.',
  tampered: 'QR tidak valid — pastikan token disalin utuh dari HP pelanggan.',
};

export default function ScanScreen() {
  const [token, setToken] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const validate = async () => {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const r = await api.scanValidate(token.trim());
      setResult(r);
      if (r.valid) setToken('');
    } catch (err) {
      setError(err.message || 'Gagal memvalidasi token.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ minHeight: '100%' }}>
      <ScreenHeader subtitle="Scan Member" />

      <div style={{ padding: '4px 18px 12px' }}>
        <Pill bg="var(--sky)" mono>SCAN MEMBER</Pill>
        <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 22, letterSpacing: '-0.02em', margin: '10px 0 4px' }}>
          Daftarkan pelanggan
        </h2>
        <p style={{ color: 'var(--ink-3)', fontSize: 12.5, lineHeight: 1.5 }}>
          Tempel token dari QR pelanggan — keanggotaan dibuat otomatis. (Scan kamera menyusul;
          untuk saat ini pelanggan bisa menyalin token dari layar QR-nya.)
        </p>
      </div>

      <div style={{ padding: '0 18px 24px', display: 'grid', gap: 12 }}>
        <Card style={{ display: 'grid', gap: 10 }}>
          <Input
            id="scan-token"
            label="Token QR pelanggan"
            placeholder="tempel token di sini"
            hint="Token sekali pakai & kedaluwarsa 90 detik."
            value={token}
            onChange={(e) => setToken(e.target.value)}
            autoComplete="off"
          />
          <Button onClick={validate} disabled={busy || token.trim().length < 10} style={{ justifySelf: 'start' }}>
            {busy ? 'Memvalidasi…' : 'Validasi'}
          </Button>
        </Card>

        {error && (
          <div role="alert" style={{ padding: '12px 14px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 12, fontSize: 12.5 }}>
            {error}
          </div>
        )}

        {result && (result.valid ? (
          <Card style={{ display: 'grid', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 34, height: 34, borderRadius: 10, background: 'var(--lime)', border: '1.5px solid var(--ink)', display: 'grid', placeItems: 'center' }}>
                <Icon name="check" size={18} stroke="var(--success)" strokeWidth={2.6} />
              </div>
              <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 15 }}>
                {result.username || 'Pelanggan'} terdaftar sebagai member
              </div>
            </div>
            <div style={{ fontSize: 12.5, color: 'var(--ink-3)' }}>
              {result.is_new_member
                ? 'Member baru 🎉 — keanggotaan dibuat otomatis.'
                : `Sudah member${result.member_since ? ` sejak ${result.member_since}` : ''}.`}
            </div>
          </Card>
        ) : (
          <div role="alert" style={{ padding: '12px 14px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 12, fontSize: 12.5, lineHeight: 1.5 }}>
            {REASON_ID[result.reason] || 'QR tidak valid.'}
          </div>
        ))}
      </div>
    </div>
  );
}
