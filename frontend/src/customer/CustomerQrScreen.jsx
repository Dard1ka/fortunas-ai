import { useCallback, useEffect, useRef, useState } from 'react';
import Card from '../ui/Card.jsx';
import Button from '../ui/Button.jsx';
import { api } from '../api/client.js';

// QR identitas: token bertanda-tangan, SEKALI PAKAI, TTL 90 detik —
// auto-refresh 5 detik sebelum kedaluwarsa (paritas layar Flutter PR #16).
export default function CustomerQrScreen() {
  const [session, setSession] = useState(null);
  const [dataUrl, setDataUrl] = useState('');
  const [left, setLeft] = useState(0);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const timerRef = useRef();
  const tickRef = useRef();

  const refresh = useCallback(async () => {
    clearTimeout(timerRef.current);
    clearInterval(tickRef.current);
    setError(null);
    setCopied(false);
    try {
      const s = await api.customerQrSession();
      setSession(s);
      const ttl = s.ttl_seconds || 90;
      setLeft(ttl);
      const { toDataURL } = await import('qrcode');
      setDataUrl(await toDataURL(s.qr_token, { width: 240, margin: 1 }));
      tickRef.current = setInterval(() => setLeft((v) => Math.max(0, v - 1)), 1000);
      timerRef.current = setTimeout(refresh, Math.max(1, ttl - 5) * 1000);
    } catch (err) {
      setError(err.message || 'Gagal membuat QR.');
    }
  }, []);

  useEffect(() => {
    refresh();
    return () => { clearTimeout(timerRef.current); clearInterval(tickRef.current); };
  }, [refresh]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(session?.qr_token || '');
      setCopied(true);
    } catch { /* clipboard tak tersedia */ }
  };

  return (
    <div style={{ padding: '18px 18px 24px', display: 'grid', gap: 12, alignContent: 'start', textAlign: 'center' }}>
      <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 20 }}>QR Saya</div>
      <p style={{ color: 'var(--ink-3)', fontSize: 12.5, lineHeight: 1.5 }}>
        Tunjukkan ke kasir saat belanja. QR sekali pakai — diperbarui otomatis tiap 90 detik.
      </p>

      {error ? (
        <div role="alert" style={{ padding: '12px 14px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 12, fontSize: 12.5 }}>
          {error} <Button variant="text" onClick={refresh}>Coba lagi</Button>
        </div>
      ) : (
        <Card style={{ display: 'grid', gap: 10, justifyItems: 'center' }}>
          {dataUrl
            ? <img src={dataUrl} alt="QR identitas pelanggan" width={240} height={240} />
            : <div style={{ width: 240, height: 240, display: 'grid', placeItems: 'center', color: 'var(--ink-4)', fontSize: 12.5 }}>Membuat QR…</div>}
          <div aria-live="polite" style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: left <= 10 ? 'var(--error)' : 'var(--ink-3)' }}>
            berlaku {left} detik lagi
          </div>
          {session && (
            <>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9.5, color: 'var(--ink-4)', wordBreak: 'break-all', lineHeight: 1.5 }}>
                {session.qr_token}
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <Button variant="secondary" onClick={copy}>{copied ? 'Tersalin ✓' : 'Salin token'}</Button>
                <Button variant="text" onClick={refresh}>Perbarui</Button>
              </div>
              <p style={{ fontSize: 10.5, color: 'var(--ink-4)', lineHeight: 1.5 }}>
                Kasir tanpa kamera? Salin token ini dan kirimkan — bisa ditempel manual di layar Kasir/Scan.
              </p>
            </>
          )}
        </Card>
      )}
    </div>
  );
}
