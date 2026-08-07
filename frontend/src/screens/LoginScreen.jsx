import { useState } from 'react';
import { api, setPrefix, setToken } from '../api/client.js';
import BrandMark from '../ui/BrandMark.jsx';
import Button from '../ui/Button.jsx';
import Input from '../ui/Input.jsx';
import { FORM_PANE_WIDTH } from '../ui/shell.js';

// Layar auth sederhana (untuk coba-coba via web sebelum mobile).
// onAuthed(result) dipanggil setelah login/register sukses.
export default function LoginScreen({ onAuthed }) {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [bizName, setBizName] = useState('');
  const [bizType, setBizType] = useState('');
  const [address, setAddress] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result =
        mode === 'register'
          ? await api.register({
              email,
              password,
              business_name: bizName,
              business_profile: bizType ? { jenis: bizType } : {},
              // Alamat opsional → backend menerbitkan kode publik UMKM
              // (mis. KDS-001) untuk alur pesanan pelanggan. Jangan kirim
              // key kosong.
              ...(address.trim() ? { address: address.trim() } : {}),
            })
          : await api.login({ email, password });
      setToken(result.access_token);
      setPrefix(result.table_prefix);
      onAuthed?.(result);
    } catch (err) {
      setError(err.message || 'Gagal. Coba lagi.');
    } finally {
      setLoading(false);
    }
  };

  const card = {
    background: 'var(--surface)',
    border: '2px solid var(--ink)',
    borderRadius: 20,
    boxShadow: 'var(--shadow-pop)',
    padding: 22,
    width: '100%',
    maxWidth: FORM_PANE_WIDTH,
    display: 'grid',
    gap: 10,
  };

  return (
    <div
      style={{
        minHeight: '100dvh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 18,
        padding: 20,
        background: 'var(--bg)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <BrandMark size={40} />
        <div>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 20 }}>
            Fortunas <span style={{ color: 'var(--violet)' }}>AI</span>
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-3)', letterSpacing: '0.08em' }}>
            UMKM ANALYTICS
          </div>
        </div>
      </div>

      <form style={card} onSubmit={submit}>
        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 18, marginBottom: 4 }}>
          {mode === 'login' ? 'Masuk' : 'Daftar Bisnis'}
        </div>
        <div style={{ fontSize: 12.5, color: 'var(--ink-3)', lineHeight: 1.5 }}>
          {mode === 'login'
            ? 'Masuk ke akun bisnismu.'
            : 'Buat akun + workspace data untuk bisnismu.'}
        </div>

        {mode === 'register' && (
          <>
            <Input id="biz-name" label="Nama bisnis" placeholder="mis. Toko Sembako Sari" value={bizName} onChange={(e) => setBizName(e.target.value)} required />
            <Input id="biz-type" label="Jenis usaha (opsional)" placeholder="mis. warung sembako" value={bizType} onChange={(e) => setBizType(e.target.value)} />
            <Input
              id="address"
              label="Alamat usaha (opsional)"
              placeholder="mis. Jl. Dhoho 12, Kediri"
              hint="Dipakai membuat kode publik UMKM (mis. KDS-001) untuk fitur pesanan pelanggan."
              value={address}
              onChange={(e) => setAddress(e.target.value)}
            />
          </>
        )}
        <Input id="email" label="Email" type="email" placeholder="nama@usaha.id" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <Input id="password" label="Password" type="password" placeholder="min 6 karakter" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} />

        {error && (
          <div style={{ marginTop: 10, padding: '8px 10px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 10, fontSize: 12.5 }}>
            {error}
          </div>
        )}

        <Button type="submit" disabled={loading} style={{ width: '100%', marginTop: 6 }}>
          {loading ? 'Memproses…' : mode === 'login' ? 'Masuk' : 'Daftar'}
        </Button>

        <div style={{ marginTop: 6, textAlign: 'center' }}>
          <a href="/customer/login" style={{ fontSize: 12, color: 'var(--violet-deep)', fontWeight: 600, textDecoration: 'none' }}>
            Masuk sebagai pelanggan →
          </a>
        </div>

        <div style={{ marginTop: 12, textAlign: 'center', fontSize: 12.5, color: 'var(--ink-3)' }}>
          {mode === 'login' ? 'Belum punya akun?' : 'Sudah punya akun?'}{' '}
          <button
            type="button"
            onClick={() => { setError(null); setMode(mode === 'login' ? 'register' : 'login'); }}
            style={{ background: 'none', border: 'none', color: 'var(--violet)', fontWeight: 700, cursor: 'pointer', fontSize: 12.5 }}
          >
            {mode === 'login' ? 'Daftar' : 'Masuk'}
          </button>
        </div>
      </form>
    </div>
  );
}
