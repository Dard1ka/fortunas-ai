import { useEffect, useState } from 'react';
import ScreenHeader from '../ui/ScreenHeader.jsx';
import Pill from '../ui/Pill.jsx';
import Icon from '../ui/Icon.jsx';
import Button from '../ui/Button.jsx';
import Input from '../ui/Input.jsx';
import Card from '../ui/Card.jsx';
import { api } from '../api/client.js';

const kicker = {
  fontFamily: 'var(--font-mono)',
  fontSize: 10,
  fontWeight: 700,
  color: 'var(--ink-3)',
  letterSpacing: '0.08em',
  textTransform: 'uppercase',
};

function ChipList({ rules, tone }) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
      {rules.map((r) => (
        <span
          key={r}
          style={{
            padding: '6px 12px',
            borderRadius: 'var(--radius-pill)',
            border: '1.5px solid var(--ink)',
            background: tone === 'allowed' ? 'var(--lime)' : 'var(--peach-soft)',
            fontSize: 12.5,
            fontWeight: 600,
          }}
        >
          {r}
        </span>
      ))}
      {rules.length === 0 && (
        <span style={{ fontSize: 12, color: 'var(--ink-4)' }}>Belum ada aturan.</span>
      )}
    </div>
  );
}

// Editor chip lokal: daftar chip berhapus + input tambah. Dipakai untuk
// allowed & forbidden — belum diekstrak ke ui/ (YAGNI sampai ada layar lain).
function ChipEditor({ label, idBase, rules, onChange, tone }) {
  const [draft, setDraft] = useState('');
  const add = () => {
    const v = draft.trim();
    if (!v || rules.includes(v)) return;
    onChange([...rules, v]);
    setDraft('');
  };
  return (
    <div style={{ display: 'grid', gap: 8 }}>
      <div style={kicker}>{label}</div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
        {rules.map((r) => (
          <span
            key={r}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '6px 8px 6px 12px',
              borderRadius: 'var(--radius-pill)',
              border: '1.5px solid var(--ink)',
              background: tone === 'allowed' ? 'var(--lime)' : 'var(--peach-soft)',
              fontSize: 12.5,
              fontWeight: 600,
            }}
          >
            {r}
            <button
              type="button"
              aria-label={`Hapus ${r}`}
              onClick={() => onChange(rules.filter((x) => x !== r))}
              style={{ border: 'none', background: 'transparent', cursor: 'pointer', display: 'grid', placeItems: 'center', padding: 2 }}
            >
              <Icon name="close" size={12} stroke="var(--ink)" strokeWidth={2.4} />
            </button>
          </span>
        ))}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 8, alignItems: 'end' }}>
        <Input
          id={`${idBase}-add`}
          label={`Tambah aturan ${tone === 'allowed' ? 'boleh' : 'larangan'}`}
          placeholder={tone === 'allowed' ? 'mis. analisis penjualan' : 'mis. bagikan data ke pihak ketiga'}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); add(); } }}
        />
        <Button variant="secondary" onClick={add} style={{ minHeight: 46 }}>
          Tambah {tone === 'allowed' ? 'boleh' : 'larangan'}
        </Button>
      </div>
    </div>
  );
}

export default function DpaScreen() {
  const [dpa, setDpa] = useState(null);
  const [loadErr, setLoadErr] = useState(null);
  const [mode, setMode] = useState('view');
  const [draft, setDraft] = useState({ raw_text: '', allowed: [], forbidden: [] });
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const ctrl = new AbortController();
    api.getDpa(ctrl.signal)
      .then(setDpa)
      .catch((err) => { if (err.name !== 'AbortError') setLoadErr(err.message); });
    return () => ctrl.abort();
  }, []);

  const startEdit = () => {
    setDraft({
      raw_text: dpa?.raw_text || '',
      allowed: dpa?.allowed_rules || [],
      forbidden: dpa?.forbidden_rules || [],
    });
    setPassword('');
    setError(null);
    setMode('edit');
  };

  const save = async () => {
    setBusy(true);
    setError(null);
    try {
      const updated = await api.putDpa({
        raw_text: draft.raw_text,
        allowed_rules: draft.allowed,
        forbidden_rules: draft.forbidden,
        password,
      });
      setDpa(updated);
      setPassword('');
      setMode('view');
    } catch (err) {
      // 403 = password salah — draft dipertahankan supaya tidak hilang.
      setError(err.message || 'Gagal menyimpan aturan.');
    } finally {
      setBusy(false);
    }
  };

  const isEmpty = dpa && !dpa.raw_text && dpa.version === 0;

  return (
    <div style={{ minHeight: '100%' }}>
      <ScreenHeader subtitle="Pagar AI" />

      <div style={{ padding: '4px 18px 12px' }}>
        <Pill bg="var(--lime)" mono>PAGAR AI · DPA</Pill>
        <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 22, letterSpacing: '-0.02em', margin: '10px 0 4px' }}>
          Aturan untuk AI-mu
        </h2>
        <p style={{ color: 'var(--ink-3)', fontSize: 12.5, lineHeight: 1.5 }}>
          Batasan yang WAJIB dipatuhi AI saat menjawab dari data bisnismu — berlaku di /ask dan briefing.
        </p>
      </div>

      <div style={{ padding: '0 18px 24px', display: 'grid', gap: 12 }}>
        {!dpa && !loadErr && <Card>Memuat…</Card>}
        {loadErr && <div role="alert" style={{ padding: '12px 14px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 12, fontSize: 12.5 }}>{loadErr}</div>}

        {dpa && mode === 'view' && (isEmpty ? (
          <Card style={{ display: 'grid', gap: 10 }}>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 15 }}>
              Belum ada pagar AI.
            </div>
            <p style={{ fontSize: 12.5, color: 'var(--ink-3)', lineHeight: 1.5 }}>
              Tulis perjanjian data (DPA) dan aturan boleh/larangan — AI hanya akan menjawab di
              dalam pagar ini.
            </p>
            <Button onClick={startEdit} style={{ justifySelf: 'start' }}>Isi pagar AI</Button>
          </Card>
        ) : (
          <>
            <Card style={{ display: 'grid', gap: 8 }}>
              <div style={kicker}>Perjanjian</div>
              <p style={{ fontSize: 13, lineHeight: 1.6, color: 'var(--ink-2)' }}>{dpa.raw_text}</p>
              {dpa.policy_summary && (
                <p style={{ fontSize: 12, color: 'var(--ink-3)', lineHeight: 1.5 }}>{dpa.policy_summary}</p>
              )}
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5, color: 'var(--ink-4)' }}>
                v{dpa.version}{dpa.updated_at ? ` · diperbarui ${dpa.updated_at}` : ''}
              </div>
            </Card>
            <Card style={{ display: 'grid', gap: 10 }}>
              <div style={kicker}>AI boleh</div>
              <ChipList rules={dpa.allowed_rules} tone="allowed" />
            </Card>
            <Card style={{ display: 'grid', gap: 10 }}>
              <div style={kicker}>AI tidak boleh</div>
              <ChipList rules={dpa.forbidden_rules} tone="forbidden" />
            </Card>
            <Button onClick={startEdit} style={{ justifySelf: 'start' }}>Ubah aturan</Button>
          </>
        ))}

        {dpa && mode === 'edit' && (
          <>
            <Card style={{ display: 'grid', gap: 8 }}>
              <label htmlFor="dpa-raw" style={{ ...kicker }}>Teks perjanjian (DPA)</label>
              <textarea
                id="dpa-raw"
                rows={5}
                value={draft.raw_text}
                onChange={(e) => setDraft((d) => ({ ...d, raw_text: e.target.value }))}
                placeholder="mis. Data transaksi hanya untuk analisis internal toko…"
                style={{
                  fontFamily: 'var(--font-body)', fontSize: 13.5, lineHeight: 1.5, color: 'var(--ink)',
                  background: 'var(--surface)', padding: 14, border: '1.5px solid var(--border)',
                  borderRadius: 'var(--radius-md)', outline: 'none', resize: 'vertical', width: '100%', boxSizing: 'border-box',
                }}
              />
            </Card>
            <Card><ChipEditor label="AI boleh" idBase="allowed" tone="allowed" rules={draft.allowed} onChange={(allowed) => setDraft((d) => ({ ...d, allowed }))} /></Card>
            <Card><ChipEditor label="AI tidak boleh" idBase="forbidden" tone="forbidden" rules={draft.forbidden} onChange={(forbidden) => setDraft((d) => ({ ...d, forbidden }))} /></Card>
            <Card style={{ display: 'grid', gap: 10 }}>
              <Input
                id="dpa-password"
                label="Konfirmasi password"
                type="password"
                hint="Perubahan pagar AI butuh password akunmu (pengganti OTP email di MVP)."
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />
              {error && (
                <div role="alert" style={{ padding: '10px 12px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 10, fontSize: 12.5 }}>
                  {error}
                </div>
              )}
              <div style={{ display: 'flex', gap: 10 }}>
                <Button onClick={save} disabled={busy || !password.trim() || !draft.raw_text.trim()}>
                  {busy ? 'Menyimpan…' : 'Simpan'}
                </Button>
                <Button variant="text" onClick={() => { setMode('view'); setError(null); }}>Batal</Button>
              </div>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
