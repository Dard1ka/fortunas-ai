import { useEffect, useRef, useState } from 'react';
import Icon from '../ui/Icon.jsx';
import Pill from '../ui/Pill.jsx';
import VoiceIdle from './VoiceIdle.jsx';
import VoiceListening from './VoiceListening.jsx';
import VoiceParsed from './VoiceParsed.jsx';
import VoiceSuccess from './VoiceSuccess.jsx';
import useSpeechRecognition, { isSpeechRecognitionSupported } from './useSpeechRecognition.js';
import { api, voiceHistoryKey } from '../api/client.js';
import { parseTransaction } from './transactionParser.js';

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
    const key = voiceHistoryKey();   // per-tenant
    const prev = JSON.parse(localStorage.getItem(key) || '[]');
    const entry = { ...tx, savedAt: new Date().toISOString() };
    const next = [entry, ...prev].slice(0, 20);
    localStorage.setItem(key, JSON.stringify(next));
  } catch { /* non-fatal */ }
}

export default function VoiceFlow({ onClose, parseDelayMs = 650 }) {
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
    // Parser LOKAL multi-item (Wave C area E) — tanpa jaringan, menggantikan
    // POST /voice/parse yang single-item. Jeda singkat mempertahankan UX
    // "AI MEMBACA…" (paritas delay 650ms Flutter).
    if (parseDelayMs > 0) await new Promise((r) => setTimeout(r, parseDelayMs));
    const parsed = parseTransaction(transcript);
    // Parser gagal total → SATU baris kosong yang bisa diedit manual, TETAP
    // maju ke layar konfirmasi (paritas fallback voice_flow.dart:132-136).
    const items = parsed.items.length > 0
      ? parsed.items
      : [{ product: '', qty: 1, unit_price: 0 }];
    setTx({
      invoice: parsed.invoice,
      customer: parsed.customer,
      country: parsed.country,
      items,
      confidence: parsed.confidence,
    });
    setState('parsed');
  };

  const confirmSave = async () => {
    if (!tx || tx.items.length === 0) return;
    setSubmitting(true);
    setError(null);
    try {
      const items = tx.items.map((it) => ({
        product: it.product,
        qty: Number(it.qty) || 0,
        unit_price: Number(it.unit_price) || 0,
      }));
      // K5 (ADR-0002): voice = metode input Checkout — SATU jalur tulis via
      // /checkout/confirm; kini SATU request multi-item (Flutter lama loop
      // per item — deviasi sadar, dicatat di PR).
      const res = await api.checkoutConfirm({
        items,
        ...(tx.customer ? { customer: tx.customer } : {}),
        ...(tx.invoice ? { invoice: tx.invoice } : {}),
      });
      if (res?.ok === false) {
        setError(res.reply || 'Gagal menyimpan transaksi.');
        setSubmitting(false);
        return;
      }
      // Riwayat lokal: SATU entri per item (bentuk {product, qty, total} yang
      // dibaca HistoryScreen — sejalan dengan Flutter yang menyimpan per item).
      const invoice = res?.invoice || tx.invoice;
      for (const it of items) {
        pushVoiceHistory({
          invoice,
          product: it.product,
          qty: it.qty,
          unit_price: it.unit_price,
          total: it.qty * it.unit_price,
          customer: tx.customer,
        });
      }
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
          onChangeMeta={(k, v) => setTx((prev) => ({ ...prev, [k]: v }))}
          onChangeItem={(i, k, v) => setTx((prev) => ({
            ...prev,
            items: prev.items.map((it, idx) => (idx === i ? { ...it, [k]: v } : it)),
          }))}
          onAddItem={() => setTx((prev) => ({
            ...prev,
            items: [...prev.items, { product: '', qty: 1, unit_price: 0 }],
          }))}
          onRemoveItem={(i) => setTx((prev) => ({
            ...prev,
            items: prev.items.filter((_, idx) => idx !== i),
          }))}
          onRetry={reset}
          onConfirm={confirmSave}
        />
      )}

      {state === 'success' && <VoiceSuccess tx={tx} />}
    </div>
  );
}
