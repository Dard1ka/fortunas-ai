import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ScreenHeader from '../ui/ScreenHeader.jsx';
import Pill from '../ui/Pill.jsx';
import Icon from '../ui/Icon.jsx';
import Input from '../ui/Input.jsx';
import Button from '../ui/Button.jsx';
import { api } from '../api/client.js';
import pkg from '../../package.json';

const TEAM = [
  { name: 'Gregorius Darrel Andika Setya', role: 'Backend · Frontend · Pipeline' },
  { name: 'Filo Alvian Ongky',             role: 'Tim Riset' },
  { name: 'Go Steven Sanjaya',             role: 'Tim Riset' },
  { name: 'Michael Ivan Santoso',          role: 'Tim Riset' },
];

export default function ProfileScreen({ onLogout }) {
  const navigate = useNavigate();
  const [health, setHealth] = useState(null);
  const [healthErr, setHealthErr] = useState(null);
  const [me, setMe] = useState(null);
  const [address, setAddress] = useState('');
  const [codeBusy, setCodeBusy] = useState(false);
  const [codeErr, setCodeErr] = useState(null);
  const [newCode, setNewCode] = useState('');

  // Kode publik UMKM (mis. KDS-001) — kunci alur pesanan pelanggan. Sumber:
  // business_profile dari /auth/me; akun lama tanpa alamat bisa backfill di sini.
  const publicCode = newCode || me?.business_profile?.code || '';

  const submitAddress = async () => {
    if (!address.trim()) return;
    setCodeBusy(true);
    setCodeErr(null);
    try {
      const r = await api.updateAddress(address.trim());
      setNewCode(r.code || '');
    } catch (err) {
      setCodeErr(err.message || 'Gagal menyimpan alamat.');
    } finally {
      setCodeBusy(false);
    }
  };

  useEffect(() => {
    const ctrl = new AbortController();
    api.health(ctrl.signal)
      .then(setHealth)
      .catch((err) => { if (err.name === 'AbortError') return; setHealthErr(err.message); });
    api.me(ctrl.signal).then(setMe).catch(() => { /* abaikan */ });
    return () => ctrl.abort();
  }, []);

  return (
    <div style={{ minHeight: '100%' }}>
      <ScreenHeader subtitle="Pengaturan" />

      <div style={{ padding: '4px 18px 14px' }}>
        <Pill bg="var(--sky)" mono>SAYA</Pill>
        <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 22, letterSpacing: '-0.02em', margin: '10px 0 4px' }}>
          Fortunas AI · v{pkg.version}
        </h2>
        <p style={{ color: 'var(--ink-3)', fontSize: 12.5, lineHeight: 1.5 }}>
          Status engine, info tim, dan pengaturan tampilan.
        </p>
      </div>

      {/* Akun card */}
      <Card>
        <CardKicker>Akun</CardKicker>
        <Row label="Bisnis" value={me?.tenant_name || '—'} />
        <Row label="Email" value={me?.email || '—'} />
        <Row label="Workspace" value={me?.table_prefix || '—'} mono />
        {me?.business_profile?.jenis && <Row label="Jenis usaha" value={me.business_profile.jenis} />}
        {publicCode ? (
          <Row label="Kode publik" value={publicCode} mono />
        ) : me ? (
          <div style={{ padding: '10px 0 12px', borderTop: '1px dashed var(--border-soft)', display: 'grid', gap: 8 }}>
            <Input
              id="profile-address"
              label="Alamat usaha"
              placeholder="mis. Jl. Dhoho 12, Kediri"
              hint="Untuk membuat kode publik UMKM (mis. KDS-001) — dipakai pelanggan saat memesan."
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              error={codeErr}
            />
            <Button onClick={submitAddress} disabled={codeBusy || !address.trim()} style={{ justifySelf: 'start' }}>
              {codeBusy ? 'Menyimpan…' : 'Buat kode publik'}
            </Button>
          </div>
        ) : null}
      </Card>

      {/* Kelola Produk — pintu masuk katalog (Wave C area A; paritas tombol
          profile_products_button Flutter). */}
      <div style={{ margin: '0 18px 14px' }}>
        <Button
          variant="secondary"
          data-testid="profile-products-button"
          onClick={() => navigate('/products')}
          style={{ width: '100%' }}
        >
          Kelola Produk
        </Button>
      </div>

      {/* Pagar AI (DPA) — batasan yang wajib dipatuhi AI (MVP-5) */}
      <div style={{ margin: '0 18px 12px' }}>
        <button
          type="button"
          onClick={() => navigate('/dpa')}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '14px 16px',
            background: 'var(--surface)',
            border: '1.5px solid var(--ink)',
            borderRadius: 18,
            boxShadow: '2px 2px 0 var(--ink)',
            cursor: 'pointer',
            textAlign: 'left',
          }}
        >
          <div style={{ width: 36, height: 36, borderRadius: 10, background: 'var(--lime)', border: '1.5px solid var(--ink)', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
            <Icon name="bolt" size={17} stroke="var(--ink)" strokeWidth={2.2} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 14 }}>Pagar AI (DPA)</div>
            <div style={{ fontSize: 11, color: 'var(--ink-3)', marginTop: 2 }}>Aturan boleh/larangan yang dipatuhi AI</div>
          </div>
          <Icon name="chevron" size={16} stroke="var(--ink)" strokeWidth={2} />
        </button>
      </div>

      {/* AI engine card */}
      <Card>
        <CardKicker>AI Engine</CardKicker>
        <Row label="Model" value="Gemini 2.5 Flash (Google)" />
        <Row
          label="Status"
          value={
            healthErr
              ? <span style={{ color: 'var(--error)' }}>Offline</span>
              : health
                ? <span style={{ color: 'var(--success)' }}>Online · {health.status || 'ok'}</span>
                : 'Memeriksa…'
          }
        />
        <Row label="Bahasa" value="Bahasa Indonesia + multibahasa" />
      </Card>

      {/* Storage card */}
      <Card>
        <CardKicker>Penyimpanan Data</CardKicker>
        <Row label="Warehouse" value="BigQuery · tabel per-tenant ({prefix}_transactions)" mono />
        <Row label="Pelanggan" value="BigQuery · {prefix}_customers" mono />
        <Row label="Vector DB" value="ChromaDB · umkm_knowledge (RAG)" mono />
      </Card>

      {/* About / team */}
      <Card>
        <CardKicker>Tim Fortunas AI</CardKicker>
        {TEAM.map((m) => (
          <Row key={m.name} label={m.role} value={m.name} />
        ))}
      </Card>

      {/* Settings (placeholder) */}
      <Card>
        <CardKicker>Tampilan</CardKicker>
        <SettingsRow label="Tema gelap" hint="Akan tersedia di update berikutnya." disabled />
        <SettingsRow label="Notifikasi briefing pagi" hint="PWA notification — coming soon." disabled />
      </Card>

      {/* Info isolasi */}
      <div
        style={{
          margin: '0 18px 12px',
          padding: '14px 16px',
          background: 'var(--violet)',
          color: '#fff',
          border: '1.5px solid var(--ink)',
          borderRadius: 14,
          boxShadow: '2px 2px 0 var(--ink)',
          display: 'flex',
          gap: 12,
          alignItems: 'flex-start',
        }}
      >
        <Icon name="bolt" size={18} stroke="var(--lime)" strokeWidth={2.2} />
        <div style={{ fontSize: 11.5, lineHeight: 1.55 }}>
          <strong>Data tiap bisnis terisolasi.</strong> Tiap akun punya tabel BigQuery sendiri;
          jawaban AI hanya dari data bisnismu. Insight diproses Gemini (cloud).
        </div>
      </div>

      {/* Logout */}
      <div style={{ margin: '0 18px 28px' }}>
        <button
          type="button"
          onClick={onLogout}
          style={{
            width: '100%',
            padding: '12px',
            borderRadius: 14,
            border: '1.5px solid var(--ink)',
            background: 'var(--surface)',
            color: 'var(--error)',
            fontFamily: 'var(--font-body)',
            fontWeight: 700,
            fontSize: 13.5,
            cursor: 'pointer',
            boxShadow: '2px 2px 0 var(--ink)',
          }}
        >
          Keluar
        </button>
      </div>
    </div>
  );
}

function Card({ children }) {
  return (
    <div
      style={{
        margin: '0 18px 12px',
        background: 'var(--surface)',
        border: '1.5px solid var(--ink)',
        borderRadius: 18,
        boxShadow: '2px 2px 0 var(--ink)',
        padding: '14px 16px 6px',
      }}
    >
      {children}
    </div>
  );
}

function CardKicker({ children }) {
  return (
    <div
      style={{
        fontFamily: 'var(--font-mono)',
        fontSize: 10,
        fontWeight: 700,
        color: 'var(--ink-3)',
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        marginBottom: 10,
      }}
    >
      {children}
    </div>
  );
}

function Row({ label, value, mono }) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '110px 1fr',
        gap: 10,
        padding: '8px 0',
        borderTop: '1px dashed var(--border-soft)',
      }}
    >
      <div
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 10.5,
          color: 'var(--ink-3)',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
          fontWeight: 600,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontFamily: mono ? 'var(--font-mono)' : 'var(--font-body)',
          fontSize: 12.5,
          color: 'var(--ink-2)',
          lineHeight: 1.5,
        }}
      >
        {value}
      </div>
    </div>
  );
}

function SettingsRow({ label, hint, disabled }) {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: 12,
        padding: '10px 0',
        borderTop: '1px dashed var(--border-soft)',
        opacity: disabled ? 0.65 : 1,
      }}
    >
      <div>
        <div style={{ fontSize: 13, fontWeight: 600 }}>{label}</div>
        {hint && <div style={{ fontSize: 11, color: 'var(--ink-3)', marginTop: 2 }}>{hint}</div>}
      </div>
      <div
        aria-hidden="true"
        style={{
          width: 38,
          height: 22,
          borderRadius: 999,
          background: 'var(--surface-hover)',
          border: '1.5px solid var(--ink)',
          position: 'relative',
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: 1,
            left: 1,
            width: 16,
            height: 16,
            borderRadius: '50%',
            background: 'var(--ink-4)',
          }}
        />
      </div>
    </div>
  );
}
