import { useState } from 'react';
import { api, setPrefix, setToken } from '../api/client.js';
import BrandMark from '../ui/BrandMark.jsx';

// Layar auth sederhana (untuk coba-coba via web sebelum mobile).
// onAuthed(result) dipanggil setelah login/register sukses.
export default function LoginScreen({ onAuthed }) {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [bizName, setBizName] = useState('');
  const [bizType, setBizType] = useState('');
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
    maxWidth: 380,
  };
  const input = {
    width: '100%',
    padding: '11px 12px',
    borderRadius: 12,
    border: '1.5px solid var(--ink)',
    background: 'var(--surface-soft)',
    fontFamily: 'var(--font-body)',
    fontSize: 14,
    marginTop: 8,
    outline: 'none',
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
            <input style={input} placeholder="Nama bisnis (mis. Toko Sembako Sari)" value={bizName} onChange={(e) => setBizName(e.target.value)} required />
            <input style={input} placeholder="Jenis usaha (opsional, mis. warung sembako)" value={bizType} onChange={(e) => setBizType(e.target.value)} />
          </>
        )}
        <input style={input} type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input style={input} type="password" placeholder="Password (min 6 karakter)" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} />

        {error && (
          <div style={{ marginTop: 10, padding: '8px 10px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 10, fontSize: 12.5 }}>
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            width: '100%',
            marginTop: 14,
            padding: '12px',
            borderRadius: 12,
            border: '1.5px solid var(--ink)',
            background: 'var(--ink)',
            color: 'var(--lime)',
            fontFamily: 'var(--font-body)',
            fontWeight: 700,
            fontSize: 14,
            cursor: loading ? 'default' : 'pointer',
            boxShadow: 'var(--shadow-pop)',
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? 'Memproses…' : mode === 'login' ? 'Masuk' : 'Daftar'}
        </button>

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
