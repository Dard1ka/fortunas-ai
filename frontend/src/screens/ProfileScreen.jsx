import { useEffect, useState } from 'react';
import ScreenHeader from '../ui/ScreenHeader.jsx';
import Pill from '../ui/Pill.jsx';
import Icon from '../ui/Icon.jsx';
import { api } from '../api/client.js';

const TEAM = [
  { name: 'Gregorius Darrel Andika Setya', role: 'Backend · Frontend · Pipeline' },
  { name: 'Filo Alvian Ongky',             role: 'Tim Riset' },
  { name: 'Go Steven Sanjaya',             role: 'Tim Riset' },
  { name: 'Michael Ivan Santoso',          role: 'Tim Riset' },
];

export default function ProfileScreen() {
  const [health, setHealth] = useState(null);
  const [healthErr, setHealthErr] = useState(null);

  useEffect(() => {
    const ctrl = new AbortController();
    api.health(ctrl.signal)
      .then(setHealth)
      .catch((err) => setHealthErr(err.message));
    return () => ctrl.abort();
  }, []);

  return (
    <div style={{ minHeight: '100%' }}>
      <ScreenHeader subtitle="Pengaturan" />

      <div style={{ padding: '4px 18px 14px' }}>
        <Pill bg="var(--sky)" mono>SAYA</Pill>
        <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 22, letterSpacing: '-0.02em', margin: '10px 0 4px' }}>
          Fortunas AI · v2.0
        </h2>
        <p style={{ color: 'var(--ink-3)', fontSize: 12.5, lineHeight: 1.5 }}>
          Status engine, info tim, dan pengaturan tampilan.
        </p>
      </div>

      {/* AI engine card */}
      <Card>
        <CardKicker>AI Engine</CardKicker>
        <Row label="Model" value="Qwen3:8b · Ollama lokal" />
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
        <Row label="Audit" value="Google Sheets staging" mono />
        <Row label="Warehouse" value="BigQuery · fortunasai.fortunas_ai.online_retail" mono />
        <Row label="Vector DB" value="ChromaDB · umkm_knowledge" mono />
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

      {/* Compliance hint */}
      <div
        style={{
          margin: '0 18px 28px',
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
          <strong>Data tidak meninggalkan server.</strong> LLM berjalan lokal via Ollama. Sesuai dengan
          UU PDP No. 27/2022.
        </div>
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
