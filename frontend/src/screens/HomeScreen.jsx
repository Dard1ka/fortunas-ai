import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ScreenHeader from '../ui/ScreenHeader.jsx';
import Pill from '../ui/Pill.jsx';
import ModeTabs from '../ui/ModeTabs.jsx';
import ExampleChip from '../ui/ExampleChip.jsx';
import Icon from '../ui/Icon.jsx';

const EXAMPLE_QUESTIONS = [
  'Siapa pelanggan paling setia bulan ini?',
  'Jam berapa toko paling rame?',
  'Produk apa yang sering dibeli bareng?',
];

export default function HomeScreen({ onVoice }) {
  const [tab, setTab] = useState('tanya');
  const [text, setText] = useState('');
  const navigate = useNavigate();

  const submit = (question) => {
    const q = (question ?? text).trim();
    if (!q) return;
    navigate(`/result?q=${encodeURIComponent(q)}`);
  };

  return (
    <div style={{ minHeight: '100%', position: 'relative' }}>
      <ScreenHeader />

      {/* hero */}
      <div style={{ padding: '4px 18px 14px' }}>
        <Pill bg="var(--lime)"><span>✦</span> Analytics tanpa ribet</Pill>
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontWeight: 700,
            fontSize: 26,
            lineHeight: 1.08,
            letterSpacing: '-0.03em',
            margin: '12px 0 8px',
          }}
        >
          Pahami bisnismu,{' '}
          <em
            style={{
              fontStyle: 'normal',
              background: 'linear-gradient(120deg, var(--violet), var(--violet-deep))',
              WebkitBackgroundClip: 'text',
              backgroundClip: 'text',
              color: 'transparent',
            }}
          >
            bukan cuma buka tokonya.
          </em>
        </h1>
        <p style={{ color: 'var(--ink-3)', fontSize: 13, lineHeight: 1.5 }}>
          Tanya pakai suara atau ketik — AI lokal langsung kasih jawaban + rekomendasi.
        </p>
      </div>

      {/* tabs */}
      <ModeTabs
        value={tab}
        onChange={setTab}
        tabs={[
          { id: 'tanya', label: 'Tanya' },
          { id: 'briefing', label: 'Briefing' },
          { id: 'harian', label: 'Harian' },
        ]}
      />

      {/* input row with voice + send */}
      <form
        onSubmit={(e) => { e.preventDefault(); submit(); }}
        style={{ padding: '18px 18px 0' }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            background: 'var(--surface)',
            border: '2px solid var(--ink)',
            borderRadius: 20,
            padding: 6,
            boxShadow: 'var(--shadow-pop)',
          }}
        >
          <button
            type="button"
            onClick={onVoice}
            aria-label="Mulai voice"
            style={{
              width: 42,
              height: 42,
              flexShrink: 0,
              borderRadius: 14,
              border: '1.5px solid var(--ink)',
              background: 'var(--violet)',
              color: '#fff',
              display: 'grid',
              placeItems: 'center',
              boxShadow: '2px 2px 0 var(--ink)',
              cursor: 'pointer',
            }}
          >
            <Icon name="mic" size={20} stroke="#fff" strokeWidth={2} />
          </button>
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Tanya apa aja soal bisnismu..."
            style={{
              flex: 1,
              border: 'none',
              outline: 'none',
              background: 'transparent',
              fontFamily: 'var(--font-body)',
              fontSize: 14,
              color: 'var(--ink)',
              padding: '8px 4px',
              minWidth: 0,
            }}
          />
          <button
            type="submit"
            aria-label="Kirim"
            style={{
              padding: '10px 14px',
              borderRadius: 14,
              border: '1.5px solid var(--ink)',
              background: 'var(--violet)',
              color: '#fff',
              fontWeight: 600,
              fontSize: 12,
              cursor: 'pointer',
              boxShadow: '2px 2px 0 var(--ink)',
            }}
          >
            <Icon name="arrowRight" size={16} stroke="#fff" strokeWidth={2.2} />
          </button>
        </div>
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--ink-3)',
            marginTop: 8,
            letterSpacing: '0.04em',
          }}
        >
          TIP · Tekan{' '}
          <span
            style={{
              background: 'var(--surface)',
              padding: '1px 6px',
              border: '1px solid var(--border-soft)',
              borderRadius: 4,
            }}
          >
            🎤
          </span>{' '}
          untuk pakai suara
        </div>
      </form>

      {/* examples */}
      <div style={{ padding: '18px 18px 0' }}>
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            fontWeight: 600,
            color: 'var(--ink-3)',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            marginBottom: 10,
          }}
        >
          Contoh pertanyaan
        </div>
        <div style={{ display: 'grid', gap: 8 }}>
          {EXAMPLE_QUESTIONS.map((q) => (
            <ExampleChip key={q} onClick={() => submit(q)}>{q}</ExampleChip>
          ))}
        </div>
      </div>

      {/* quick action: tambah transaksi */}
      <div style={{ padding: '18px 18px 0' }}>
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            fontWeight: 600,
            color: 'var(--ink-3)',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            marginBottom: 10,
          }}
        >
          Aksi cepat
        </div>
        <button
          type="button"
          onClick={onVoice}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: 14,
            background: 'var(--ink)',
            color: '#fff',
            border: '1.5px solid var(--ink)',
            borderRadius: 18,
            boxShadow: 'var(--shadow-pop-sm)',
            cursor: 'pointer',
          }}
        >
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 12,
              background: 'var(--lime)',
              color: 'var(--ink)',
              display: 'grid',
              placeItems: 'center',
              flexShrink: 0,
            }}
          >
            <Icon name="plus" size={22} stroke="var(--ink)" strokeWidth={2.4} />
          </div>
          <div style={{ textAlign: 'left', flex: 1 }}>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 14 }}>
              Tambah Transaksi
            </div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)', marginTop: 2 }}>
              Voice langsung aktif · Hands-free
            </div>
          </div>
          <Icon name="chevron" size={18} stroke="#fff" strokeWidth={2} />
        </button>
      </div>
    </div>
  );
}
