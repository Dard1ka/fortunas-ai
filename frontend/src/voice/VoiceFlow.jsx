import { useEffect, useRef, useState } from 'react';
import Icon from '../ui/Icon.jsx';
import Pill from '../ui/Pill.jsx';
import VoiceIdle from './VoiceIdle.jsx';
import VoiceListening from './VoiceListening.jsx';
import VoiceParsed from './VoiceParsed.jsx';
import VoiceSuccess from './VoiceSuccess.jsx';
import useSpeechRecognition, { isSpeechRecognitionSupported } from './useSpeechRecognition.js';
import { api } from '../api/client.js';
import { RECENT_VOICE_KEY } from '../screens/HistoryScreen.jsx';

// States: idle → listening → parsing → parsed → success
const TITLE_FOR_STATE = {
  idle:      'TAMBAH TRANSAKSI',
  listening: '● MENDENGAR…',
  parsing:   'AI MEMBACA…',
  parsed:    'KONFIRMASI',
  success:   '✓ TERSIMPAN',
};

function pushVoiceHistory(tx) {
  try {
    const prev = JSON.parse(localStorage.getItem(RECENT_VOICE_KEY) || '[]');
    const entry = { ...tx, savedAt: new Date().toISOString() };
    const next = [entry, ...prev].slice(0, 20);
    localStorage.setItem(RECENT_VOICE_KEY, JSON.stringify(next));
  } catch { /* non-fatal */ }
}

export default function VoiceFlow({ onClose }) {
  const [state, setState] = useState('idle');
  const [tx, setTx] = useState(null);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [textFallback, setTextFallback] = useState('');
  const supported = isSpeechRecognitionSupported();
  const stt = useSpeechRecognition({ lang: 'id-ID' });
  const closeTimerRef = useRef();

  const startListening = () => {
    setError(null);
    setTx(null);
    setEditing(false);
    setTextFallback('');
    stt.reset();
    if (supported) stt.start();
    setState('listening');
  };

  const stopAndParse = async () => {
    if (supported) stt.stop();
    const transcript = supported ? stt.transcript.trim() : textFallback.trim();
    if (!transcript) {
      setError('Belum ada transkrip. Coba lagi.');
      setState('idle');
      return;
    }
    setState('parsing');
    try {
      const parsed = await api.voiceParse(transcript);
      // Normalize keys (backend may return snake_case)
      setTx({
        invoice: parsed.invoice ?? '',
        product: parsed.product ?? '',
        qty: parsed.qty ?? 0,
        unit_price: parsed.unit_price ?? parsed.unitPrice ?? 0,
        total: parsed.total ?? (Number(parsed.qty || 0) * Number(parsed.unit_price || parsed.unitPrice || 0)),
        customer: parsed.customer ?? '',
        country: parsed.country ?? 'Indonesia',
        confidence: parsed.confidence ?? null,
      });
      setState('parsed');
    } catch (err) {
      setError(err.message || 'Gagal mengurai transkrip.');
      setState('listening');
    }
  };

  const confirmSave = async () => {
    if (!tx) return;
    setSubmitting(true);
    setError(null);
    try {
      const computedTotal = Number(tx.total) || Number(tx.qty) * Number(tx.unit_price);
      const payload = { ...tx, total: computedTotal };
      const res = await api.voiceTransaction(payload);
      if (res?.ok === false) {
        setError(res.reply || 'Gagal menyimpan transaksi.');
        setSubmitting(false);
        return;
      }
      pushVoiceHistory(payload);
      setSubmitting(false);
      setState('success');
      closeTimerRef.current = setTimeout(() => onClose?.(), 2200);
    } catch (err) {
      setError(err.message || 'Gagal menyimpan transaksi.');
      setSubmitting(false);
    }
  };

  const reset = () => {
    setError(null);
    setTx(null);
    setEditing(false);
    setTextFallback('');
    stt.reset();
    setState('idle');
  };

  useEffect(() => {
    return () => {
      clearTimeout(closeTimerRef.current);
      if (supported) {
        try { stt.stop(); } catch { /* ignore */ }
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Voice input transaksi"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 80,
        background: 'var(--bg)',
        display: 'flex',
        flexDirection: 'column',
        animation: 'fortunas-fade-up .25s ease-out',
        overflow: 'hidden',
        paddingTop: 'max(env(safe-area-inset-top), 12px)',
        paddingBottom: 'max(env(safe-area-inset-bottom), 12px)',
      }}
    >
      {/* header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 18px 8px',
        }}
      >
        <button
          type="button"
          onClick={onClose}
          aria-label="Tutup"
          style={{
            width: 36,
            height: 36,
            borderRadius: 12,
            background: 'var(--surface)',
            border: '1.5px solid var(--ink)',
            boxShadow: '2px 2px 0 var(--ink)',
            display: 'grid',
            placeItems: 'center',
            cursor: 'pointer',
          }}
        >
          <Icon name="close" size={16} strokeWidth={2.2} />
        </button>
        <Pill bg={state === 'success' ? 'var(--lime)' : 'var(--surface)'} sm mono>
          {TITLE_FOR_STATE[state]}
        </Pill>
        <div style={{ width: 36 }} />
      </div>

      {state === 'idle' && (
        <VoiceIdle onStart={startListening} supported={supported} />
      )}

      {(state === 'listening' || state === 'parsing') && (
        <VoiceListening
          state={state}
          transcript={supported ? stt.transcript : textFallback}
          supported={supported}
          textFallback={textFallback}
          onTextChange={setTextFallback}
          onStop={stopAndParse}
        />
      )}

      {state === 'parsed' && tx && (
        <VoiceParsed
          tx={tx}
          editing={editing}
          submitting={submitting}
          error={error}
          onEdit={() => setEditing((v) => !v)}
          onChange={(k, v) => setTx((prev) => ({ ...prev, [k]: v }))}
          onRetry={reset}
          onConfirm={confirmSave}
        />
      )}

      {state === 'success' && <VoiceSuccess tx={tx} />}
    </div>
  );
}
