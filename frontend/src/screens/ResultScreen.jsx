import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import Pill from '../ui/Pill.jsx';
import Icon from '../ui/Icon.jsx';
import { api } from '../api/client.js';
import { formatLatencyRange } from '../api/latency.js';

const PHASE_LABELS = {
  query: 'Mengambil data dari BigQuery…',
  insight: 'Membuat insight dengan AI…',
};

function ResultScreenInner({ q }) {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [phase, setPhase] = useState('query');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const expected = formatLatencyRange();

  useEffect(() => {
    if (!q) {
      navigate('/');
      return undefined;
    }
    const ctrl = new AbortController();

    // Heuristic phase flip after 1.2s — backend doesn't stream from /ask.
    const phaseTimer = setTimeout(() => setPhase('insight'), 1200);

    api.ask(q, ctrl.signal)
      .then((res) => {
        clearTimeout(phaseTimer);
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        clearTimeout(phaseTimer);
        if (err.name === 'AbortError') return;
        setError(err.message);
        setLoading(false);
      });

    return () => { ctrl.abort(); clearTimeout(phaseTimer); };
  }, [q, navigate]);

  return (
    <div style={{ minHeight: '100%' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '14px 18px 8px',
        }}
      >
        <button
          type="button"
          onClick={() => navigate(-1)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            fontSize: 13,
            color: 'var(--ink-2)',
            fontWeight: 600,
          }}
        >
          <Icon name="arrowLeft" size={18} strokeWidth={2} /> Kembali
        </button>
        {data?.llm_output && (
          <Pill bg="var(--lime)" sm mono>
            ✓ {data.rows?.length || 0} BARIS
          </Pill>
        )}
      </div>

      {/* question card */}
      <div
        style={{
          margin: '4px 18px 12px',
          padding: '16px 18px',
          background: 'var(--surface)',
          border: '1.5px solid var(--ink)',
          borderRadius: 18,
          boxShadow: '2px 2px 0 var(--ink)',
        }}
      >
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            fontWeight: 600,
            color: 'var(--ink-3)',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            marginBottom: 6,
          }}
        >
          Pertanyaan
        </div>
        <div
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 15,
            fontWeight: 500,
            lineHeight: 1.4,
            letterSpacing: '-0.01em',
          }}
        >
          “{q}”
        </div>
      </div>

      {loading && (
        <div style={{ padding: '0 18px 18px' }}>
          <div
            style={{
              padding: '18px 18px',
              background: 'var(--surface)',
              border: '1.5px solid var(--ink)',
              borderRadius: 18,
              boxShadow: '2px 2px 0 var(--ink)',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <div
              style={{
                width: 24,
                height: 24,
                borderRadius: '50%',
                border: '2.5px solid var(--violet-soft)',
                borderTopColor: 'var(--violet)',
                animation: 'fortunas-spin 0.7s linear infinite',
              }}
            />
            <div>
              <div style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 14 }}>
                {PHASE_LABELS[phase]}
              </div>
              {expected && (
                <div style={{ fontSize: 11.5, color: 'var(--ink-3)', marginTop: 2 }}>
                  Estimasi {expected}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {error && !loading && (
        <div
          style={{
            margin: '0 18px 18px',
            padding: '14px 16px',
            background: 'var(--peach-soft)',
            border: '1.5px solid var(--ink)',
            borderRadius: 14,
            fontSize: 13,
            color: 'var(--ink-2)',
          }}
        >
          {error && error !== 'null' ? error : 'Terjadi kesalahan tak terduga. Coba lagi.'}
        </div>
      )}

      {/* Pertanyaan tak dikenali / tidak ada data: tampilkan pesan ramah, bukan kosong */}
      {!loading && !error && data && !data.llm_output && (
        <div style={{ padding: '0 18px 18px' }}>
          <div
            style={{
              padding: '16px 18px',
              background: 'var(--surface)',
              border: '1.5px solid var(--ink)',
              borderRadius: 18,
              boxShadow: '2px 2px 0 var(--ink)',
            }}
          >
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                fontWeight: 700,
                color: 'var(--ink-3)',
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                marginBottom: 8,
              }}
            >
              {data.status === 'success' ? 'Belum ada data' : 'Pertanyaan belum dikenali'}
            </div>
            <p style={{ fontSize: 13.5, color: 'var(--ink-2)', lineHeight: 1.55, margin: 0 }}>
              {data.message || 'Coba tanyakan tentang pelanggan loyal, jam ramai, pelanggan paling bernilai, atau produk yang sering dibeli bersama.'}
            </p>
            <div style={{ display: 'grid', gap: 8, marginTop: 12 }}>
              {[
                'Siapa pelanggan paling setia?',
                'Jam berapa toko paling rame?',
                'Produk apa yang sering dibeli bareng?',
              ].map((ex) => (
                <button
                  key={ex}
                  type="button"
                  onClick={() => navigate(`/result?q=${encodeURIComponent(ex)}`)}
                  style={{
                    textAlign: 'left',
                    padding: '10px 12px',
                    background: 'var(--surface-soft)',
                    border: '1px solid var(--border-soft)',
                    borderRadius: 10,
                    fontSize: 12.5,
                    color: 'var(--ink-2)',
                    cursor: 'pointer',
                  }}
                >
                  → {ex}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {!loading && !error && data?.llm_output && (
        <>
          {/* answer summary */}
          <div
            style={{
              margin: '0 18px 12px',
              padding: '18px 18px',
              background: 'var(--violet)',
              color: '#fff',
              border: '1.5px solid var(--ink)',
              borderRadius: 18,
              boxShadow: '2px 2px 0 var(--ink)',
            }}
          >
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                color: 'rgba(255,255,255,0.75)',
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                fontWeight: 600,
              }}
            >
              Ringkasan · {data.mapped_analysis}
            </div>
            <p
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 16,
                fontWeight: 500,
                lineHeight: 1.5,
                marginTop: 8,
                letterSpacing: '-0.01em',
              }}
            >
              {data.llm_output.summary}
            </p>
          </div>

          {!!data.llm_output.top_findings?.length && (
            <div style={{ padding: '0 18px 12px' }}>
              <div
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 10,
                  fontWeight: 600,
                  color: 'var(--ink-3)',
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  marginBottom: 8,
                }}
              >
                Temuan
              </div>
              <div style={{ display: 'grid', gap: 8 }}>
                {data.llm_output.top_findings.map((f, i) => (
                  <div
                    key={`${i}-${f.slice(0, 40)}`}
                    style={{
                      display: 'flex',
                      gap: 10,
                      padding: '10px 12px',
                      background: 'var(--surface-soft)',
                      borderRadius: 12,
                    }}
                  >
                    <span
                      style={{
                        width: 22,
                        height: 22,
                        borderRadius: 6,
                        background: 'var(--ink)',
                        color: 'var(--lime)',
                        display: 'grid',
                        placeItems: 'center',
                        fontFamily: 'var(--font-mono)',
                        fontSize: 10,
                        fontWeight: 700,
                        flexShrink: 0,
                      }}
                    >
                      {i + 1}
                    </span>
                    <span style={{ fontSize: 12.5, color: 'var(--ink-2)', lineHeight: 1.5 }}>{f}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!!data.llm_output.recommendation?.length && (
            <div
              style={{
                margin: '0 18px 12px',
                padding: '16px 18px',
                background: 'var(--lime)',
                border: '1.5px solid var(--ink)',
                borderRadius: 18,
                boxShadow: '2px 2px 0 var(--ink)',
              }}
            >
              <div
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 10,
                  fontWeight: 700,
                  color: 'var(--ink)',
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  marginBottom: 10,
                }}
              >
                Rekomendasi
              </div>
              <div style={{ display: 'grid', gap: 8 }}>
                {data.llm_output.recommendation.map((r, i) => (
                  <div
                    key={`${i}-${r.slice(0, 40)}`}
                    style={{
                      display: 'flex',
                      gap: 10,
                      padding: '10px 12px',
                      background: 'rgba(255,255,255,0.55)',
                      border: '1.5px solid var(--ink)',
                      borderRadius: 10,
                    }}
                  >
                    <span style={{ fontWeight: 700 }}>→</span>
                    <span style={{ fontSize: 12.5, fontWeight: 500 }}>{r}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// Outer wrapper: re-mounts ResultScreenInner on every `q` change via `key`,
// so initial state (loading=true, phase=query, etc.) is set during the
// render cycle, not inside an effect.
export default function ResultScreen() {
  const [params] = useSearchParams();
  const q = params.get('q') || '';
  return <ResultScreenInner key={q} q={q} />;
}
