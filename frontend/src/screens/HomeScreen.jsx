import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client.js';
import useSpeechRecognition from '../voice/useSpeechRecognition.js';
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
  const [chips, setChips] = useState(EXAMPLE_QUESTIONS);
  const navigate = useNavigate();

  // Chip contoh dari registry analisis (11 intent) — label dipakai langsung
  // sebagai query tap-to-ask. Gagal fetch → chip default tetap tampil.
  useEffect(() => {
    const ctrl = new AbortController();
    api.analyses(ctrl.signal)
      .then((list) => {
        const labels = (list || []).filter((a) => a.enabled).map((a) => a.label);
        if (labels.length) setChips(labels.slice(0, 6));
      })
      .catch(() => {});
    return () => ctrl.abort();
  }, []);

  // Badge inbox: hitung pesanan 'paid' (menunggu diterima) — count dari server,
  // sekali per mount; loading/error diam-diam 0 (paritas pendingOrderCountProvider).
  const [pendingOrders, setPendingOrders] = useState(0);
  useEffect(() => {
    const ctrl = new AbortController();
    api.listOrders('paid', ctrl.signal)
      .then((r) => setPendingOrders(Number(r?.count) || 0))
      .catch(() => {});
    return () => ctrl.abort();
  }, []);

  // Voice-untuk-bertanya: dikte pertanyaan ke kotak input (BEDA dari mic bawah
  // yang membuka flow tambah transaksi). Tap mic → ngomong → tap lagi untuk stop.
  const ask = useSpeechRecognition({ lang: 'id-ID' });
  // Sinkron transkrip → input dilakukan saat render (pola resmi React untuk
  // "state dari render sebelumnya") — setState di dalam effect memicu render
  // kaskade dan ditolak react-hooks/set-state-in-effect.
  const [appliedTranscript, setAppliedTranscript] = useState('');
  if (ask.transcript !== appliedTranscript) {
    setAppliedTranscript(ask.transcript);
    if (ask.transcript) setText(ask.transcript);
  }

  const toggleVoiceAsk = () => {
    if (ask.isListening) {
      ask.stop();
    } else {
      setText('');
      ask.reset();
      ask.start();
    }
  };

  const submit = (question) => {
    const q = (question ?? text).trim();
    if (!q) return;
    if (ask.isListening) ask.stop();
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
            onClick={toggleVoiceAsk}
            aria-label={ask.isListening ? 'Berhenti mendikte' : 'Dikte pertanyaan dengan suara'}
            title="Tanya pakai suara"
            style={{
              width: 42,
              height: 42,
              flexShrink: 0,
              borderRadius: 14,
              border: '1.5px solid var(--ink)',
              background: ask.isListening ? 'var(--error)' : 'var(--violet)',
              color: '#fff',
              display: 'grid',
              placeItems: 'center',
              boxShadow: '2px 2px 0 var(--ink)',
              cursor: 'pointer',
              animation: ask.isListening ? 'fortunas-pulse 1.2s ease-in-out infinite' : 'none',
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
          {ask.isListening ? (
            <span style={{ color: 'var(--error)', fontWeight: 700 }}>
              ● Mendengar… ketuk mic lagi untuk berhenti
            </span>
          ) : (
            <>
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
              untuk bertanya pakai suara
            </>
          )}
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
          {chips.map((q) => (
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

        {/* Kasir manual multi-item (route /checkout) */}
        <button
          type="button"
          onClick={() => navigate('/checkout')}
          style={{
            width: '100%',
            marginTop: 10,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: 14,
            background: 'var(--surface)',
            color: 'var(--ink)',
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
              background: 'var(--violet-soft)',
              color: 'var(--violet-deep)',
              display: 'grid',
              placeItems: 'center',
              flexShrink: 0,
            }}
          >
            <Icon name="bag" size={20} stroke="var(--violet-deep)" strokeWidth={2.2} />
          </div>
          <div style={{ textAlign: 'left', flex: 1 }}>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 14 }}>
              Kasir
            </div>
            <div style={{ fontSize: 11, color: 'var(--ink-3)', marginTop: 2 }}>
              Multi-item · bisa tautkan pelanggan (QR)
            </div>
          </div>
          <Icon name="chevron" size={18} stroke="var(--ink)" strokeWidth={2} />
        </button>

        {/* Pesanan Masuk (inbox order online, route /orders) — badge = jumlah
            pesanan berstatus paid (menunggu diterima), sekali fetch per mount;
            TANPA polling (paritas Flutter, push notif belum ada). */}
        <button
          type="button"
          data-testid="home-orders"
          onClick={() => navigate('/orders')}
          style={{
            width: '100%',
            marginTop: 10,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: 14,
            background: 'var(--surface)',
            color: 'var(--ink)',
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
              display: 'grid',
              placeItems: 'center',
              flexShrink: 0,
            }}
          >
            <Icon name="bolt" size={20} stroke="var(--ink)" strokeWidth={2.2} />
          </div>
          <div style={{ textAlign: 'left', flex: 1 }}>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 14 }}>
              Pesanan Masuk
            </div>
            <div style={{ fontSize: 11, color: pendingOrders > 0 ? 'var(--violet-deep)' : 'var(--ink-3)', fontWeight: pendingOrders > 0 ? 700 : 400, marginTop: 2 }}>
              {pendingOrders > 0 ? `${pendingOrders} pesanan menunggu diterima` : 'Pesanan online dari pelanggan'}
            </div>
          </div>
          <Icon name="chevron" size={18} stroke="var(--ink)" strokeWidth={2} />
        </button>

        {/* Scan member (validasi QR pelanggan, route /scan) */}
        <button
          type="button"
          onClick={() => navigate('/scan')}
          style={{
            width: '100%',
            marginTop: 10,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: 14,
            background: 'var(--surface)',
            color: 'var(--ink)',
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
              background: 'var(--sky)',
              display: 'grid',
              placeItems: 'center',
              flexShrink: 0,
            }}
          >
            <Icon name="sparkle" size={20} stroke="var(--ink)" strokeWidth={2.2} />
          </div>
          <div style={{ textAlign: 'left', flex: 1 }}>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 14 }}>
              Scan Member
            </div>
            <div style={{ fontSize: 11, color: 'var(--ink-3)', marginTop: 2 }}>
              Daftarkan pelanggan dari QR/token
            </div>
          </div>
          <Icon name="chevron" size={18} stroke="var(--ink)" strokeWidth={2} />
        </button>
      </div>
    </div>
  );
}
