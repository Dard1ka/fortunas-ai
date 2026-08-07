import { useState, useRef, useEffect, useCallback } from 'react'
import './App.css'

const EXAMPLE_QUESTIONS = [
  'Siapa pelanggan paling setia bulan ini?',
  'Jam berapa toko paling rame?',
  'Produk apa yang sering dibeli bareng?',
  'Siapa customer yang spending paling gede?',
]

const ANALYSIS_META = {
  high_value_customer: { short: 'HV' },
  repeat_customer: { short: 'RC' },
  peak_hour: { short: 'PH' },
  bundle_opportunity: { short: 'BO' },
  executive_summary: { short: 'ES' },
}

const PHASE_LABELS = {
  query: 'Mengambil data dari BigQuery...',
  insight: 'Membuat insight dengan AI...',
}

const STORAGE = {
  latencies: 'fortunas.latencies.v1',
  lastAsk: 'fortunas.lastAsk.v1',
  lastBriefing: 'fortunas.lastBriefing.v1',
}

const CANCEL_OFFER_MS = 90_000
const MAX_LATENCY_SAMPLES = 5

/* ════════════════════════════════════════════════════ */
/*  Helpers                                             */
/* ════════════════════════════════════════════════════ */
function readJSON(key, fallback = null) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

function writeJSON(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    /* quota or disabled — non-fatal */
  }
}

function recordLatency(ms) {
  const arr = readJSON(STORAGE.latencies, [])
  const next = [...arr, ms].slice(-MAX_LATENCY_SAMPLES)
  writeJSON(STORAGE.latencies, next)
  return next
}

function formatLatencyRange(samples) {
  if (!samples || samples.length === 0) return null
  const avg = samples.reduce((a, b) => a + b, 0) / samples.length
  const seconds = Math.round(avg / 1000)
  if (seconds <= 0) return null
  return `~${seconds} detik`
}

function humanizeError(err, status) {
  if (err?.name === 'AbortError') return null
  if (status >= 500) return 'Server sedang bermasalah. Coba lagi sebentar lagi.'
  if (status === 429) return 'Terlalu banyak permintaan. Tunggu beberapa detik, lalu coba lagi.'
  if (status === 408 || status === 504) return 'Permintaan memakan waktu terlalu lama. Coba sederhanakan pertanyaan.'
  if (status === 404) return 'Endpoint tidak ditemukan. Pastikan backend berjalan.'
  if (status >= 400) return 'Permintaan tidak dapat diproses. Periksa kembali pertanyaan Anda.'
  if (err?.message?.includes('Failed to fetch') || err?.message?.includes('NetworkError')) {
    return 'Tidak dapat terhubung ke server. Periksa koneksi atau pastikan backend menyala.'
  }
  return err?.message || 'Terjadi kesalahan yang tidak terduga.'
}

function confidenceInfo(level, rowCount) {
  const count = typeof rowCount === 'number' ? rowCount : null
  const weakByRows = count !== null && count < 3
  if (level === 'high' && !weakByRows) return { label: 'Data Kuat', tone: 'strong' }
  if (level === 'medium' && !weakByRows) return { label: 'Cukup', tone: 'medium' }
  if (level === 'low' || weakByRows) return { label: 'Terbatas', tone: 'weak' }
  return { label: 'Cukup', tone: 'medium' }
}

function buildAskText(data) {
  const lines = []
  lines.push(`FORTUNAS AI — Hasil Analisis`)
  lines.push(`Pertanyaan: ${data.question}`)
  lines.push(`Status: ${data.status}`)
  lines.push('')
  if (data.llm_output?.summary) {
    lines.push('RINGKASAN')
    lines.push(humanizeFieldNames(data.llm_output.summary))
    lines.push('')
  }
  const findings = (data.llm_output?.top_findings || []).filter(Boolean)
  if (findings.length) {
    lines.push('TEMUAN UTAMA')
    findings.forEach((f, i) => lines.push(`${i + 1}. ${humanizeFieldNames(f)}`))
    lines.push('')
  }
  const recs = (data.llm_output?.recommendation || []).filter(Boolean)
  if (recs.length) {
    lines.push('REKOMENDASI')
    recs.forEach((r) => lines.push(`- ${humanizeFieldNames(r)}`))
    lines.push('')
  }
  const sources = (data.llm_output?.rag_sources || []).filter(Boolean)
  if (sources.length) {
    lines.push('REFERENSI PENGETAHUAN')
    sources.forEach((s) => lines.push(`- ${s}`))
  }
  return lines.join('\n')
}

function buildBriefingText(data) {
  const lines = []
  lines.push(`FORTUNAS AI — Briefing Bisnis`)
  lines.push('')
  if (data.executive_summary) {
    lines.push('EXECUTIVE SUMMARY')
    lines.push(humanizeFieldNames(data.executive_summary))
    lines.push('')
  }
  data.sections?.forEach((s) => {
    lines.push(`[${s.label}] — ${s.status}`)
    if (s.summary) lines.push(humanizeFieldNames(s.summary))
    const findings = (s.top_findings || []).filter(Boolean)
    if (findings.length) {
      lines.push('Temuan:')
      findings.forEach((f, i) => lines.push(`  ${i + 1}. ${humanizeFieldNames(f)}`))
    }
    const recs = (s.recommendation || []).filter(Boolean)
    if (recs.length) {
      lines.push('Rekomendasi:')
      recs.forEach((r) => lines.push(`  - ${humanizeFieldNames(r)}`))
    }
    const sources = (s.rag_sources || []).filter(Boolean)
    if (sources.length) {
      lines.push('Referensi:')
      sources.forEach((src) => lines.push(`  - ${src}`))
    }
    lines.push('')
  })
  return lines.join('\n')
}

function downloadText(filename, content) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}

const FIELD_NAME_MAP = {
  total_orders: 'jumlah pesanan',
  total_spent: 'total belanja',
  total_qty: 'jumlah kuantitas',
  avg_order_value: 'rata-rata nilai pesanan',
  bundle_frequency: 'frekuensi dibeli bersama',
  purchase_hour: 'jam pembelian',
  invoice_date: 'tanggal transaksi',
  customer_id: 'ID pelanggan',
  product_A: 'produk A',
  product_B: 'produk B',
  top_products: 'produk teratas',
  data_confidence: 'tingkat keyakinan data',
  row_count: 'jumlah baris data',
}

/** Replaces backend snake_case column names with natural Indonesian
 *  so LLM output reads like business prose, not database dump. */
function humanizeFieldNames(text) {
  if (!text) return text
  return String(text).replace(/\b([A-Za-z]+(?:_[A-Za-z0-9]+)+)\b/g, (match) => {
    if (FIELD_NAME_MAP[match]) return FIELD_NAME_MAP[match]
    const lower = match.toLowerCase()
    if (FIELD_NAME_MAP[lower]) return FIELD_NAME_MAP[lower]
    return match.replace(/_/g, ' ')
  })
}

/* ════════════════════════════════════════════════════ */
/*  App                                                 */
/* ════════════════════════════════════════════════════ */
function App() {
  const [mode, setMode] = useState('ask')
  const [question, setQuestion] = useState('')
  const [askLoading, setAskLoading] = useState(false)
  const [briefLoading, setBriefLoading] = useState(false)
  const [result, setResult] = useState(() => readJSON(STORAGE.lastAsk))
  const [briefing, setBriefing] = useState(() => readJSON(STORAGE.lastBriefing))
  const [askError, setAskError] = useState(null)
  const [briefError, setBriefError] = useState(null)
  const [streamState, setStreamState] = useState(null)

  const [dailyData, setDailyData] = useState(null)
  const [dailyLoading, setDailyLoading] = useState(false)
  const [dailyError, setDailyError] = useState(null)
  const [dailyRunning, setDailyRunning] = useState(false)

  const [latencies, setLatencies] = useState(() => readJSON(STORAGE.latencies, []))
  const [elapsed, setElapsed] = useState(0)
  const [copyFeedback, setCopyFeedback] = useState('')

  const inputRef = useRef(null)
  const abortRef = useRef(null)
  const eventSourceRef = useRef(null)
  const elapsedTimerRef = useRef(null)
  const startTimeRef = useRef(0)

  useEffect(() => {
    if (mode === 'ask') inputRef.current?.focus()
  }, [mode])

  useEffect(() => {
    if (mode === 'daily' && !dailyData && !dailyLoading) {
      loadDailyReport()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode])

  useEffect(() => {
    const loading = askLoading || briefLoading
    if (loading) {
      startTimeRef.current = Date.now()
      setElapsed(0)
      elapsedTimerRef.current = setInterval(() => {
        setElapsed(Date.now() - startTimeRef.current)
      }, 500)
    } else {
      clearInterval(elapsedTimerRef.current)
    }
    return () => clearInterval(elapsedTimerRef.current)
  }, [askLoading, briefLoading])

  useEffect(() => {
    if (!copyFeedback) return
    const t = setTimeout(() => setCopyFeedback(''), 2000)
    return () => clearTimeout(t)
  }, [copyFeedback])

  function cancelInflight() {
    abortRef.current?.abort()
    abortRef.current = null
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setAskLoading(false)
    setBriefLoading(false)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const q = question.trim()
    if (!q || askLoading) return

    cancelInflight()
    const controller = new AbortController()
    abortRef.current = controller
    const start = Date.now()

    setAskLoading(true)
    setAskError(null)
    setResult(null)

    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q }),
        signal: controller.signal,
      })
      if (!res.ok) {
        const msg = humanizeError(new Error(`HTTP ${res.status}`), res.status)
        throw Object.assign(new Error(msg), { _handled: true })
      }
      const data = await res.json()
      setResult(data)
      writeJSON(STORAGE.lastAsk, data)
      setLatencies(recordLatency(Date.now() - start))
    } catch (err) {
      if (err.name === 'AbortError') return
      setAskError(err._handled ? err.message : humanizeError(err))
    } finally {
      setAskLoading(false)
    }
  }

  function handleBriefing() {
    if (briefLoading) return
    cancelInflight()

    const start = Date.now()
    setBriefLoading(true)
    setBriefError(null)
    setBriefing(null)
    setStreamState({ steps: [], sections: [], currentStep: null })

    const es = new EventSource('/api/briefing/stream')
    eventSourceRef.current = es

    es.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.event === 'step') {
        setStreamState((prev) => (prev ? { ...prev, currentStep: data } : prev))
      }

      if (data.event === 'section') {
        setStreamState((prev) =>
          prev ? { ...prev, sections: [...prev.sections, data.section], currentStep: null } : prev
        )
      }

      if (data.event === 'done') {
        es.close()
        eventSourceRef.current = null
        setStreamState((prev) => {
          if (prev) {
            const finalBriefing = {
              executive_summary: data.executive_summary,
              sections: prev.sections,
              agent_trace: [],
            }
            setBriefing(finalBriefing)
            writeJSON(STORAGE.lastBriefing, finalBriefing)
          }
          return null
        })
        setBriefLoading(false)
        setLatencies(recordLatency(Date.now() - start))
      }
    }

    es.onerror = () => {
      es.close()
      eventSourceRef.current = null
      setBriefError('Koneksi streaming terputus. Coba jalankan ulang briefing.')
      setStreamState(null)
      setBriefLoading(false)
    }
  }

  async function loadDailyReport() {
    setDailyLoading(true)
    setDailyError(null)
    try {
      const res = await fetch('/api/report/daily')
      if (!res.ok) throw Object.assign(new Error(humanizeError(new Error(), res.status)), { _handled: true })
      setDailyData(await res.json())
    } catch (err) {
      setDailyError(err._handled ? err.message : humanizeError(err))
    } finally {
      setDailyLoading(false)
    }
  }

  async function deleteDailyEntry(generatedAt) {
    if (!generatedAt) return
    if (!window.confirm(`Hapus history briefing "${generatedAt}"? Tindakan ini tidak bisa dibatalkan.`)) return
    try {
      const res = await fetch(`/api/report/daily?generated_at=${encodeURIComponent(generatedAt)}`, {
        method: 'DELETE',
      })
      if (!res.ok) throw Object.assign(new Error(humanizeError(new Error(), res.status)), { _handled: true })
      setDailyData(await res.json())
    } catch (err) {
      setDailyError(err._handled ? err.message : humanizeError(err))
    }
  }

  async function clearDailyHistory() {
    if (!window.confirm('Hapus SEMUA history briefing harian? Tindakan ini tidak bisa dibatalkan.')) return
    try {
      const res = await fetch('/api/report/daily?all=true', { method: 'DELETE' })
      if (!res.ok) throw Object.assign(new Error(humanizeError(new Error(), res.status)), { _handled: true })
      setDailyData(await res.json())
    } catch (err) {
      setDailyError(err._handled ? err.message : humanizeError(err))
    }
  }

  async function runDailyReport() {
    if (dailyRunning) return
    setDailyRunning(true)
    setDailyError(null)
    try {
      const res = await fetch('/api/report/daily/run', { method: 'POST' })
      if (!res.ok) throw Object.assign(new Error(humanizeError(new Error(), res.status)), { _handled: true })
      setDailyData(await res.json())
    } catch (err) {
      setDailyError(err._handled ? err.message : humanizeError(err))
    } finally {
      setDailyRunning(false)
    }
  }

  function handleExampleClick(q) {
    setQuestion(q)
    setResult(null)
    setAskError(null)
    inputRef.current?.focus()
  }

  function handleResetAsk() {
    cancelInflight()
    setQuestion('')
    setResult(null)
    setAskError(null)
    try { localStorage.removeItem(STORAGE.lastAsk) } catch { /* ignore */ }
    inputRef.current?.focus()
  }

  function handleResetBriefing() {
    cancelInflight()
    setBriefing(null)
    setStreamState(null)
    setBriefError(null)
    try { localStorage.removeItem(STORAGE.lastBriefing) } catch { /* ignore */ }
  }

  function switchMode(m) {
    if (m === mode) return
    cancelInflight()
    setMode(m)
  }

  const handleCopyResult = useCallback(async (text) => {
    const ok = await copyText(text)
    setCopyFeedback(ok ? 'Tersalin' : 'Gagal menyalin')
  }, [])

  const avgLabel = formatLatencyRange(latencies)
  const canOfferCancel = (askLoading || briefLoading) && elapsed > CANCEL_OFFER_MS

  return (
    <div className="app">
      <header className="header">
        <div className="header__brand">
          <div className="header__logo" aria-hidden="true">F</div>
          <div>
            <h1 className="header__title">
              <span className="header__initial">Fortunas</span>
              <span className="header__accent"> AI</span>
            </h1>
            <p className="header__subtitle">UMKM Analytics</p>
          </div>
        </div>
        <div className="header__status" aria-label="Status sistem">
          <span className="header__status-dot" aria-hidden="true" />
          <span>AI online</span>
        </div>
      </header>

      <main className="main">
        <section className="hero">
          <span className="hero__badge">
            <span aria-hidden="true">✦</span> Analytics tanpa ribet
          </span>
          <h2 className="hero__title">
            Pahami bisnismu, <em>bukan cuma buka tokonya.</em>
          </h2>
          <p className="hero__sub">
            Tanya apa aja soal penjualan, pelanggan, dan tren — AI lokal bakal kasih jawaban cepat plus rekomendasi yang bisa langsung kamu jalanin.
          </p>
        </section>

        <nav className="mode-toggle" role="tablist" aria-label="Mode analisis">
          <button
            role="tab"
            aria-selected={mode === 'ask'}
            className={`mode-toggle__btn ${mode === 'ask' ? 'mode-toggle__btn--active' : ''}`}
            onClick={() => switchMode('ask')}
          >
            Tanya AI
          </button>
          <button
            role="tab"
            aria-selected={mode === 'briefing'}
            className={`mode-toggle__btn ${mode === 'briefing' ? 'mode-toggle__btn--active' : ''}`}
            onClick={() => switchMode('briefing')}
          >
            Briefing
          </button>
          <button
            role="tab"
            aria-selected={mode === 'daily'}
            className={`mode-toggle__btn ${mode === 'daily' ? 'mode-toggle__btn--active' : ''}`}
            onClick={() => switchMode('daily')}
          >
            Harian
          </button>
          <button
            role="tab"
            aria-selected={mode === 'upload'}
            className={`mode-toggle__btn ${mode === 'upload' ? 'mode-toggle__btn--active' : ''}`}
            onClick={() => switchMode('upload')}
          >
            Upload Data
          </button>
          <button
            role="tab"
            aria-selected={mode === 'wa'}
            className={`mode-toggle__btn ${mode === 'wa' ? 'mode-toggle__btn--active' : ''}`}
            onClick={() => switchMode('wa')}
          >
            WA Bot
          </button>
        </nav>

        {/* ═══ ASK MODE ═══ */}
        {mode === 'ask' && (
          <>
            <form className="input-section" onSubmit={handleSubmit} role="search">
              <div className="input-wrapper">
                <input
                  ref={inputRef}
                  className="input-field"
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Tanya apa aja soal bisnismu..."
                  disabled={askLoading}
                  aria-label="Pertanyaan bisnis"
                />
                <button
                  className="submit-btn"
                  type="submit"
                  disabled={askLoading || !question.trim()}
                  aria-label="Kirim pertanyaan"
                >
                  <span className="submit-btn__icon" aria-hidden="true">&rarr;</span>
                  <span className="submit-btn__label">Analisis</span>
                </button>
              </div>
              {avgLabel && !askLoading && (
                <p className="input-hint">Rata-rata waktu respons: {avgLabel}</p>
              )}
            </form>

            {!askLoading && !result && !askError && (
              <div className="examples">
                <p className="examples__label">Contoh pertanyaan</p>
                <div className="examples__grid">
                  {EXAMPLE_QUESTIONS.map((q) => (
                    <button key={q} className="example-chip" onClick={() => handleExampleClick(q)}>
                      <span aria-hidden="true" style={{ opacity: 0.5, marginRight: 6 }}>→</span>{q}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* ═══ BRIEFING MODE — idle ═══ */}
        {mode === 'briefing' && !briefLoading && !briefing && !streamState && (
          <div className="briefing-idle">
            <p className="briefing-idle__desc">
              Sekali klik, AI auto-analisis 4 aspek bisnismu dan nyusun executive summary yang siap kamu pamerin.
            </p>

            <div className="briefing-preview">
              <BriefingPreviewItem short="RC" title="Repeat Customer" sub="Pelanggan yang paling sering bertransaksi" />
              <BriefingPreviewItem short="PH" title="Peak Hour" sub="Jam transaksi paling ramai" />
              <BriefingPreviewItem short="BO" title="Bundle Opportunity" sub="Produk yang sering dibeli bersama" />
              <BriefingPreviewItem short="HV" title="High Value Customer" sub="Pelanggan dengan belanja tertinggi" />
            </div>

            <button className="briefing-start primary-btn" onClick={handleBriefing} disabled={briefLoading}>
              Mulai Briefing <span aria-hidden="true">&rarr;</span>
            </button>
            {avgLabel && <p className="input-hint">Rata-rata durasi: {avgLabel}</p>}
          </div>
        )}

        {/* ═══ BRIEFING MODE — streaming progress ═══ */}
        {mode === 'briefing' && streamState && (
          <BriefingStream state={streamState} />
        )}

        {/* Loading (ask mode) */}
        <div aria-live="polite" aria-atomic="true">
          {mode === 'ask' && askLoading && (
            <AskPipeline
              elapsed={elapsed}
              avgLabel={avgLabel}
              canCancel={canOfferCancel}
              onCancel={cancelInflight}
            />
          )}
          {mode === 'briefing' && briefLoading && canOfferCancel && (
            <div className="pipeline__status-line">
              <span>Proses memakan waktu lebih lama dari biasanya...</span>
              <button className="pipeline__cancel ghost-btn" onClick={cancelInflight}>Batalkan</button>
            </div>
          )}
        </div>

        {/* Errors */}
        {mode === 'ask' && askError && <HumaneError message={askError} />}
        {mode === 'briefing' && briefError && <HumaneError message={briefError} />}

        {/* Ask Result */}
        {mode === 'ask' && result && (
          <ResultView
            data={result}
            onReset={handleResetAsk}
            onCopy={() => handleCopyResult(buildAskText(result))}
            onDownload={() => downloadText(`fortunas-ask-${Date.now()}.txt`, buildAskText(result))}
            copyFeedback={copyFeedback}
          />
        )}

        {/* Briefing Result */}
        {mode === 'briefing' && briefing && (
          <BriefingView
            data={briefing}
            onReset={handleResetBriefing}
            onCopy={() => handleCopyResult(buildBriefingText(briefing))}
            onDownload={() => downloadText(`fortunas-briefing-${Date.now()}.txt`, buildBriefingText(briefing))}
            copyFeedback={copyFeedback}
          />
        )}

        {/* ═══ DAILY MODE ═══ */}
        {mode === 'daily' && (
          <DailyPanel
            data={dailyData}
            loading={dailyLoading}
            running={dailyRunning}
            error={dailyError}
            onRefresh={loadDailyReport}
            onRun={runDailyReport}
            onDelete={deleteDailyEntry}
            onClearAll={clearDailyHistory}
          />
        )}

        {/* ═══ UPLOAD MODE ═══ */}
        {mode === 'upload' && <UploadPanel />}

        {/* ═══ WA BOT MODE ═══ */}
        {mode === 'wa' && <WaPanel />}
      </main>

      <footer className="footer">
        <div className="footer__tech">
          <span className="footer__tag">FastAPI</span>
          <span className="footer__tag">BigQuery</span>
          <span className="footer__tag">Ollama</span>
          <span className="footer__tag">React</span>
        </div>
        <p className="footer__text">Made for UMKM Indonesia · Powered by Local LLM &amp; BigQuery</p>
      </footer>
    </div>
  )
}

/* ════════════════════════════════════════════════════ */
/*  Sub-components                                      */
/* ════════════════════════════════════════════════════ */

function BriefingPreviewItem({ short, title, sub }) {
  return (
    <div className="briefing-preview__item">
      <span className="briefing-preview__mono">{short}</span>
      <div>
        <p className="briefing-preview__title">{title}</p>
        <p className="briefing-preview__sub">{sub}</p>
      </div>
    </div>
  )
}

function HumaneError({ message }) {
  return (
    <div className="humane-error error-card" role="alert">
      <div className="error-card__header">Terjadi kesalahan</div>
      <p className="error-card__message">{message}</p>
    </div>
  )
}

function ConfidenceBadge({ confidence, rowCount }) {
  const info = confidenceInfo(confidence, rowCount)
  const meta = typeof rowCount === 'number' ? `${rowCount} data` : null
  return (
    <span className={`confidence-badge confidence-badge--${info.tone}`} title="Tingkat keyakinan berdasarkan data">
      <span className="confidence-badge__dot" aria-hidden="true" />
      <span>{info.label}</span>
      {meta && <span className="confidence-badge__meta">&middot; {meta}</span>}
    </span>
  )
}

function KnowledgeCard({ sources }) {
  const clean = (sources || []).filter(Boolean)
  if (clean.length === 0) return null
  return (
    <div className="result-card knowledge-card">
      <div className="result-card__label">Referensi Pengetahuan</div>
      <ul className="knowledge-list">
        {clean.map((s, i) => (
          <li key={i} className="knowledge-item">
            <span className="source-tag">{String(i + 1).padStart(2, '0')}</span>
            <span className="knowledge-item__text">{s}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function InlineSources({ sources }) {
  const clean = (sources || []).filter(Boolean)
  if (clean.length === 0) return null
  return (
    <div className="inline-sources">
      <span className="inline-sources__label">Referensi:</span>
      <div className="inline-sources__tags">
        {clean.map((s, i) => (
          <span key={i} className="source-tag source-tag--inline">{s}</span>
        ))}
      </div>
    </div>
  )
}

function ActionBar({ onCopy, onDownload, onReset, resetLabel, feedback }) {
  return (
    <div className="action-bar">
      <div className="action-bar__primary">
        <button className="ghost-btn" onClick={onCopy}>Salin ringkasan</button>
        <button className="ghost-btn" onClick={onDownload}>Unduh teks</button>
        {feedback && <span className="action-bar__feedback">{feedback}</span>}
      </div>
      <button className="ghost-btn action-bar__reset" onClick={onReset}>
        <span aria-hidden="true">&larr;</span> {resetLabel}
      </button>
    </div>
  )
}

function EmptyState({ title, description, action }) {
  return (
    <div className="empty-state">
      <svg
        className="empty-state__icon"
        viewBox="0 0 64 64"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.2"
        aria-hidden="true"
      >
        <rect x="14" y="10" width="36" height="44" rx="3" />
        <line x1="22" y1="22" x2="42" y2="22" />
        <line x1="22" y1="30" x2="42" y2="30" />
        <line x1="22" y1="38" x2="36" y2="38" />
        <circle cx="32" cy="48" r="1.5" fill="currentColor" />
      </svg>
      <h3 className="empty-state__title">{title}</h3>
      <p className="empty-state__desc">{description}</p>
      {action}
    </div>
  )
}

/* ─────── ResultView (single question) ─────── */
function ResultView({ data, onReset, onCopy, onDownload, copyFeedback }) {
  const { question, status, agent_trace, llm_output, message, rows } = data
  const statusClass =
    status === 'success' ? 'success' : status === 'partial_success' ? 'partial' : 'failed'
  const rowCount = Array.isArray(rows) ? rows.length : undefined

  return (
    <div className="result">
      <div className="result-card">
        <div className="result-card__label-row">
          <span className="result-card__label">Pertanyaan</span>
          {llm_output && (
            <ConfidenceBadge confidence={llm_output.data_confidence} rowCount={rowCount} />
          )}
        </div>
        <p className="result-card__question">&ldquo;{question}&rdquo;</p>
        <div className="result-card__meta-row">
          <span className={`status-badge status-badge--${statusClass}`}>
            {status === 'success' ? '\u2713 Berhasil' : status === 'partial_success' ? '\u26A0 Sebagian Berhasil' : '\u2717 Gagal'}
          </span>
        </div>
      </div>

      {llm_output?.summary && (
        <div className="result-card result-card--summary">
          <div className="result-card__label result-card__label--gold">Ringkasan</div>
          <p className="result-card__summary">{humanizeFieldNames(llm_output.summary)}</p>
        </div>
      )}

      {llm_output?.top_findings?.filter(Boolean).length > 0 && (
        <div className="result-card result-card--findings">
          <div className="result-card__label">Temuan Utama</div>
          <ol className="findings-list">
            {llm_output.top_findings.filter(Boolean).map((f, i) => (
              <li key={i} className="finding-item">
                <span className="finding-item__number">{i + 1}</span>
                <span className="finding-item__text">{humanizeFieldNames(f)}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {llm_output?.recommendation?.filter(Boolean).length > 0 && (
        <div className="result-card result-card--recommendations">
          <div className="result-card__label result-card__label--gold">Rekomendasi</div>
          <ul className="rec-list">
            {llm_output.recommendation.filter(Boolean).map((r, i) => (
              <li key={i} className="rec-item">
                <span className="rec-item__icon">&rarr;</span>
                <span className="rec-item__text">{humanizeFieldNames(r)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {llm_output?.rag_sources && <KnowledgeCard sources={llm_output.rag_sources} />}

      {!llm_output && message && (
        <div className="result-card">
          <div className="result-card__label">Pesan</div>
          <p className="finding-item__text">{message}</p>
        </div>
      )}

      {agent_trace?.length > 0 && <TraceCard trace={agent_trace} delay="0.35s" />}

      <ActionBar
        onCopy={onCopy}
        onDownload={onDownload}
        onReset={onReset}
        resetLabel="Tanya pertanyaan baru"
        feedback={copyFeedback}
      />
    </div>
  )
}

/* ─────── BriefingView (all analyses) ─────── */
function BriefingView({ data, onReset, onCopy, onDownload, copyFeedback }) {
  const { executive_summary, sections, agent_trace } = data
  const [openSections, setOpenSections] = useState(() => {
    const initial = {}
    sections.forEach((s) => {
      if (s.status === 'success') initial[s.analysis_type] = true
    })
    return initial
  })

  function toggleSection(key) {
    setOpenSections((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  return (
    <div className="briefing">
      {executive_summary && (
        <div className="briefing__exec">
          <div className="briefing__exec-label">Executive Summary</div>
          <p className="briefing__exec-text">{humanizeFieldNames(executive_summary)}</p>
        </div>
      )}

      {sections.map((section) => {
        const isOpen = openSections[section.analysis_type]
        const meta = ANALYSIS_META[section.analysis_type] || { short: '?' }

        return (
          <div key={section.analysis_type} className="briefing__section">
            <div
              className="briefing__section-header"
              onClick={() => toggleSection(section.analysis_type)}
            >
              <div className="briefing__section-title">
                <span className="briefing__section-monogram">{meta.short}</span>
                {section.label}
                {section.status === 'success' && (
                  <span className="briefing__section-badge">{section.row_count} data</span>
                )}
              </div>
              <span
                className={`briefing__section-chevron ${isOpen ? 'briefing__section-chevron--open' : ''}`}
              >
                &#9660;
              </span>
            </div>

            {isOpen && section.status === 'success' && (
              <div className="briefing__section-body">
                <p className="briefing__section-summary">{humanizeFieldNames(section.summary)}</p>

                {section.top_findings?.filter(Boolean).length > 0 && (
                  <div>
                    <div className="result-card__label">Temuan</div>
                    <ol className="findings-list">
                      {section.top_findings.filter(Boolean).map((f, i) => (
                        <li key={i} className="finding-item">
                          <span className="finding-item__number">{i + 1}</span>
                          <span className="finding-item__text">{humanizeFieldNames(f)}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}

                {section.recommendation?.filter(Boolean).length > 0 && (
                  <div>
                    <div className="result-card__label result-card__label--gold">Rekomendasi</div>
                    <ul className="rec-list">
                      {section.recommendation.filter(Boolean).map((r, i) => (
                        <li key={i} className="rec-item">
                          <span className="rec-item__icon">&rarr;</span>
                          <span className="rec-item__text">{humanizeFieldNames(r)}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <InlineSources sources={section.rag_sources} />
              </div>
            )}

            {isOpen && section.status !== 'success' && (
              <div className="briefing__section-body">
                <p className="briefing__section-summary">{humanizeFieldNames(section.summary)}</p>
              </div>
            )}
          </div>
        )
      })}

      {agent_trace?.length > 0 && <TraceCard trace={agent_trace} delay="0.5s" />}

      <ActionBar
        onCopy={onCopy}
        onDownload={onDownload}
        onReset={onReset}
        resetLabel="Mulai briefing baru"
        feedback={copyFeedback}
      />
    </div>
  )
}

/* ─────── Step pipelines (per-mode) ─────── */
const PIPELINE_STEPS = [
  { label: 'Memahami pertanyaan', desc: 'Intent mapping dari bahasa natural', time: 500 },
  { label: 'Membuat query SQL', desc: 'Menyusun query untuk BigQuery', time: 2000 },
  { label: 'Mengambil data', desc: 'Menjalankan query ke BigQuery', time: 6000 },
  { label: 'Menganalisis dengan AI', desc: 'Local LLM membuat insight', time: 12000 },
]

const DAILY_STEPS = [
  { label: 'Menarik data BigQuery', desc: 'Query 4 analisis dasar', time: 4000 },
  { label: 'Analisis High Value Customer', desc: 'Cari pelanggan paling bernilai', time: 6000 },
  { label: 'Analisis Repeat Customer', desc: 'Cari pelanggan paling loyal', time: 6000 },
  { label: 'Analisis Peak Hour', desc: 'Cari jam transaksi tersibuk', time: 5000 },
  { label: 'Analisis Bundle Opportunity', desc: 'Cari pasangan produk populer', time: 8000 },
  { label: 'Menyusun executive summary', desc: 'AI merangkum temuan jadi narasi', time: 8000 },
  { label: 'Menyimpan ke history', desc: 'Briefing siap dipakai', time: 1000 },
]

const UPLOAD_VALIDATE_STEPS = [
  { label: 'Membaca file', desc: 'Parse Excel/CSV ke memori', time: 600 },
  { label: 'Mengecek kolom wajib', desc: 'Cocokkan header dengan schema BigQuery', time: 500 },
  { label: 'Validasi tipe data', desc: 'Cek tiap baris sesuai tipe kolom', time: 1400 },
  { label: 'Menyiapkan preview', desc: 'Rangkum hasil validasi', time: 500 },
]

const UPLOAD_SEND_STEPS = [
  { label: 'Membaca & memvalidasi ulang', desc: 'Pastikan data masih aman dikirim', time: 1200 },
  { label: 'Streaming ke BigQuery', desc: 'Insert per batch 500 baris', time: 3500 },
  { label: 'Konfirmasi dari BigQuery', desc: 'Verifikasi tidak ada row gagal', time: 1200 },
  { label: 'Finalisasi', desc: 'Laporan upload siap', time: 400 },
]

/* ─────── StepProgress (reusable) ─────── */
function StepProgress({ steps, done = false, title }) {
  const [activeStep, setActiveStep] = useState(0)

  useEffect(() => {
    if (done) {
      setActiveStep(steps.length)
      return undefined
    }
    setActiveStep(0)
    let cumulative = 0
    const timers = steps.map((step, i) => {
      cumulative += step.time
      return setTimeout(() => setActiveStep(i + 1), cumulative)
    })
    // Jangan pernah auto-finish step terakhir; biarkan "done" prop yang memutuskan
    const last = timers.pop()
    if (last) clearTimeout(last)
    return () => timers.forEach(clearTimeout)
  }, [steps, done])

  return (
    <div className="pipeline pipeline--compact">
      {title && <p className="pipeline__title">{title}</p>}
      {steps.map((step, i) => {
        const isDone = done || i < activeStep
        const isActive = !done && i === activeStep
        const isPending = !done && i > activeStep
        return (
          <div
            key={i}
            className={`pipeline__step ${isDone ? 'pipeline__step--done' : ''} ${isActive ? 'pipeline__step--active' : ''} ${isPending ? 'pipeline__step--pending' : ''}`}
          >
            <div className="pipeline__indicator">
              {isDone && <span className="pipeline__check">{'\u2713'}</span>}
              {isActive && <span className="pipeline__spinner" />}
              {isPending && <span className="pipeline__dot" />}
            </div>
            <div className="pipeline__text">
              <span className="pipeline__label">{step.label}</span>
              {(isActive || isDone) && <span className="pipeline__desc">{step.desc}</span>}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function AskPipeline({ elapsed, avgLabel, canCancel, onCancel }) {
  const [activeStep, setActiveStep] = useState(0)

  useEffect(() => {
    let cumulative = 0
    const timers = PIPELINE_STEPS.map((step, i) => {
      cumulative += step.time
      return setTimeout(() => setActiveStep(i + 1), cumulative)
    })
    return () => timers.forEach(clearTimeout)
  }, [])

  const seconds = Math.floor(elapsed / 1000)

  return (
    <div className="pipeline">
      {PIPELINE_STEPS.map((step, i) => {
        const isDone = i < activeStep
        const isActive = i === activeStep
        const isPending = i > activeStep
        return (
          <div
            key={i}
            className={`pipeline__step ${isDone ? 'pipeline__step--done' : ''} ${isActive ? 'pipeline__step--active' : ''} ${isPending ? 'pipeline__step--pending' : ''}`}
          >
            <div className="pipeline__indicator">
              {isDone && <span className="pipeline__check">{'\u2713'}</span>}
              {isActive && <span className="pipeline__spinner" />}
              {isPending && <span className="pipeline__dot" />}
            </div>
            <div className="pipeline__text">
              <span className="pipeline__label">{step.label}</span>
              {(isActive || isDone) && <span className="pipeline__desc">{step.desc}</span>}
            </div>
          </div>
        )
      })}

      <div className="pipeline__status-line">
        <span>
          {seconds}s berlalu{avgLabel ? ` · biasanya ${avgLabel}` : ''}
        </span>
        {canCancel && (
          <button className="pipeline__cancel ghost-btn" onClick={onCancel}>
            Batalkan
          </button>
        )}
      </div>
    </div>
  )
}

/* ─────── BriefingStream ─────── */
function BriefingStream({ state }) {
  const { sections, currentStep } = state

  return (
    <div className="briefing-stream">
      {sections.map((section) => {
        const meta = ANALYSIS_META[section.analysis_type] || { short: '?' }
        return (
          <div key={section.analysis_type} className="stream-section">
            <div className="stream-section__header">
              <span className="stream-section__monogram stream-section__monogram--done">
                {meta.short}
              </span>
              <span className="stream-section__label">{section.label}</span>
              <span className={`stream-section__status stream-section__status--${section.status}`}>
                {section.status === 'success' ? '\u2713' : '\u2717'}
              </span>
            </div>
            {section.status === 'success' && (
              <>
                <p className="stream-section__summary">{humanizeFieldNames(section.summary)}</p>
                <InlineSources sources={section.rag_sources} />
              </>
            )}
          </div>
        )
      })}

      {currentStep && (
        <div className="stream-section stream-section--active">
          <div className="stream-section__header">
            <span className="stream-section__monogram stream-section__monogram--active">
              {(ANALYSIS_META[currentStep.analysis] || { short: '?' }).short}
            </span>
            <span className="stream-section__label">{currentStep.label}</span>
            <span className="stream-section__spinner" aria-hidden="true" />
          </div>
          <p className="stream-section__phase">
            {PHASE_LABELS[currentStep.phase] || 'Memproses...'}
          </p>
        </div>
      )}

      {currentStep &&
        Array.from({ length: Math.max(0, currentStep.total - currentStep.index - 1) }).map((_, i) => (
          <div key={`pending-${i}`} className="stream-section stream-section--pending">
            <div className="stream-section__header">
              <span className="stream-section__monogram">--</span>
              <span className="stream-section__label-pending">Menunggu...</span>
            </div>
          </div>
        ))}
    </div>
  )
}

/* ─────── DailyPanel ─────── */
function DailyPanel({ data, loading, running, error, onRefresh, onRun, onDelete, onClearAll }) {
  if (loading && !data) {
    return (
      <div className="daily-panel">
        <p className="input-hint">Memuat briefing harian...</p>
      </div>
    )
  }

  const hasLatest = data?.latest
  const history = (data?.history || []).filter((e) => e?.date !== data?.latest?.date)

  return (
    <div className="daily-panel">
      <div className="daily-panel__header">
        <div>
          <p className="daily-panel__title">Briefing Harian</p>
          <p className="daily-panel__desc">
            Ringkasan otomatis yang dijalankan sesuai jadwal dan tersimpan setiap hari.
          </p>
        </div>
        <div className="daily-panel__actions">
          <button className="ghost-btn" onClick={onRefresh} disabled={loading}>
            Muat ulang
          </button>
          <button className="primary-btn" onClick={onRun} disabled={running}>
            {running ? 'Menjalankan...' : 'Jalankan hari ini'}
          </button>
        </div>
      </div>

      {error && <HumaneError message={error} />}

      {running && (
        <StepProgress
          key="daily-run"
          steps={DAILY_STEPS}
          title="Menjalankan briefing harian..."
        />
      )}

      {!hasLatest && !error && !running && (
        <EmptyState
          title="Belum ada briefing tersimpan"
          description="Jalankan briefing hari ini untuk mulai membangun riwayat harian bisnis Anda."
          action={
            <button className="primary-btn" onClick={onRun} disabled={running}>
              {running ? 'Menjalankan...' : 'Jalankan sekarang'}
            </button>
          }
        />
      )}

      {hasLatest && (
        <DailyEntry entry={data.latest} heading="Terbaru" highlighted onDelete={onDelete} />
      )}

      {history.length > 0 && (
        <div className="daily-history">
          <div className="daily-history__head">
            <p className="daily-history__label">Riwayat</p>
            {onClearAll && (
              <button className="danger-btn danger-btn--sm" onClick={onClearAll}>
                Hapus semua
              </button>
            )}
          </div>
          <div className="daily-history__list">
            {history.map((entry) => (
              <DailyEntry key={entry.generated_at} entry={entry} onDelete={onDelete} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function DailyEntry({ entry, heading, highlighted, onDelete }) {
  const [expanded, setExpanded] = useState(!!highlighted)

  return (
    <div className={`daily-entry ${highlighted ? 'daily-entry--latest' : ''}`}>
      <div
        className="daily-entry__header"
        onClick={() => setExpanded((v) => !v)}
        role="button"
        tabIndex={0}
      >
        <div>
          {heading && <p className="daily-entry__tag">{heading}</p>}
          <p className="daily-entry__date">{entry.date}</p>
          <p className="daily-entry__time">Dibuat {entry.generated_at}</p>
        </div>
        <div className="daily-entry__controls">
          {onDelete && (
            <button
              className="danger-btn danger-btn--sm"
              onClick={(e) => {
                e.stopPropagation()
                onDelete(entry.generated_at)
              }}
              title="Hapus history ini"
            >
              Hapus
            </button>
          )}
          <span className={`briefing__section-chevron ${expanded ? 'briefing__section-chevron--open' : ''}`}>
            &#9660;
          </span>
        </div>
      </div>

      {expanded && (
        <div className="daily-entry__body">
          {entry.executive_summary && (
            <p className="daily-entry__summary">{humanizeFieldNames(entry.executive_summary)}</p>
          )}
          {entry.sections?.map((section) => {
            const meta = ANALYSIS_META[section.analysis_type] || { short: '?' }
            return (
              <div key={section.analysis_type} className="daily-entry__section">
                <div className="daily-entry__section-head">
                  <span className="briefing__section-monogram">{meta.short}</span>
                  <span>{section.label}</span>
                  {section.status === 'success' && (
                    <ConfidenceBadge
                      confidence={section.data_confidence}
                      rowCount={section.row_count}
                    />
                  )}
                </div>
                {section.summary && (
                  <p className="daily-entry__section-summary">{humanizeFieldNames(section.summary)}</p>
                )}
                <InlineSources sources={section.rag_sources} />
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

/* ─────── TraceCard ─────── */
function TraceCard({ trace, delay = '0.3s' }) {
  return (
    <div className="result-card result-card--trace" style={{ animationDelay: delay }}>
      <div className="result-card__label">Agent Trace</div>
      <ul className="trace-list">
        {trace.map((step, i) => {
          const isLast = i === trace.length - 1
          const isFail = step.toLowerCase().includes('failed')
          return (
            <li key={i} className="trace-item">
              <span
                className={`trace-item__dot ${
                  isFail ? 'trace-item__dot--fail' : isLast ? 'trace-item__dot--success' : ''
                }`}
              />
              {step}
            </li>
          )
        })}
      </ul>
    </div>
  )
}

/* ─────── UploadPanel (Excel → BigQuery) ─────── */
const UPLOAD_COLUMNS = ['Invoice', 'StockCode', 'Description', 'Quantity', 'InvoiceDate', 'Price', 'Customer ID', 'Country']
const UPLOAD_ACCEPT = '.xlsx,.xls,.csv'

function UploadPanel() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef(null)

  function resetAll() {
    setFile(null)
    setPreview(null)
    setResult(null)
    setError(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  function pickFile(f) {
    if (!f) return
    const lower = f.name.toLowerCase()
    if (!UPLOAD_ACCEPT.split(',').some((ext) => lower.endsWith(ext.trim()))) {
      setError('Format tidak didukung. Gunakan .xlsx, .xls, atau .csv')
      return
    }
    setFile(f)
    setPreview(null)
    setResult(null)
    setError(null)
  }

  async function _parseResponse(res, fallbackMsg) {
    // Backend kadang return non-JSON (mis. "Internal Server Error" plain text
    // saat ada exception tidak terduga). Baca body sebagai text dulu, baru
    // coba parse JSON. Kalau gagal parse, lempar text mentah supaya pesan
    // error asli tetap kelihatan di UI.
    const text = await res.text()
    let data = null
    try {
      data = text ? JSON.parse(text) : null
    } catch {
      // bukan JSON — bisa "Internal Server Error", HTML stack trace, dll.
      if (!res.ok) {
        throw new Error(`Backend ${res.status}: ${text.slice(0, 300) || fallbackMsg}`)
      }
    }
    if (!res.ok) {
      const detail = (data && (data.detail || data.message)) || text.slice(0, 300) || fallbackMsg
      throw new Error(detail)
    }
    return data
  }

  async function handleValidate() {
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetch('/api/upload/preview', { method: 'POST', body: form })
      const data = await _parseResponse(res, 'Gagal memvalidasi file')
      setPreview(data)
    } catch (err) {
      setError(err.message || 'Gagal memvalidasi file')
    } finally {
      setLoading(false)
    }
  }

  async function handleUpload() {
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetch('/api/upload/excel', { method: 'POST', body: form })
      const data = await _parseResponse(res, 'Gagal upload ke BigQuery')
      setResult(data)
    } catch (err) {
      setError(err.message || 'Gagal upload ke BigQuery')
    } finally {
      setUploading(false)
    }
  }

  function onDrop(e) {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files?.[0]
    if (f) pickFile(f)
  }

  return (
    <div className="upload-panel">
      <div className="upload-panel__header">
        <div>
          <p className="daily-panel__title">Upload Data ke BigQuery</p>
          <p className="daily-panel__desc">
            Tambahin data transaksi baru ke warehouse. File akan divalidasi dulu sebelum dikirim.
          </p>
        </div>
        <div className="upload-panel__schema">
          <p className="upload-panel__schema-label">Kolom wajib</p>
          <div className="upload-panel__cols">
            {UPLOAD_COLUMNS.map((c) => (
              <span key={c} className="source-tag source-tag--inline">{c}</span>
            ))}
          </div>
        </div>
      </div>

      {!result && (
        <div
          className={`upload-drop ${dragOver ? 'upload-drop--over' : ''} ${file ? 'upload-drop--has-file' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={UPLOAD_ACCEPT}
            onChange={(e) => pickFile(e.target.files?.[0])}
            hidden
          />
          {!file ? (
            <>
              <div className="upload-drop__icon" aria-hidden="true">⬆</div>
              <p className="upload-drop__title">Drag & drop file di sini</p>
              <p className="upload-drop__sub">atau klik buat pilih · .xlsx, .xls, .csv</p>
            </>
          ) : (
            <>
              <p className="upload-drop__filename">{file.name}</p>
              <p className="upload-drop__sub">{(file.size / 1024).toFixed(1)} KB · klik buat ganti file</p>
            </>
          )}
        </div>
      )}

      {file && !result && (
        <div className="upload-actions">
          <button className="ghost-btn" onClick={resetAll} disabled={loading || uploading}>
            Batal
          </button>
          <button
            className="ghost-btn"
            onClick={handleValidate}
            disabled={loading || uploading}
          >
            {loading ? 'Memvalidasi...' : 'Validasi dulu'}
          </button>
          <button
            className="primary-btn"
            onClick={handleUpload}
            disabled={uploading || loading || (preview && preview.valid_rows === 0)}
          >
            {uploading ? 'Mengirim ke BigQuery...' : 'Kirim ke BigQuery'} <span aria-hidden="true">&rarr;</span>
          </button>
        </div>
      )}

      {error && <HumaneError message={error} />}

      {loading && (
        <StepProgress
          key="upload-validate"
          steps={UPLOAD_VALIDATE_STEPS}
          title="Memvalidasi file..."
        />
      )}

      {uploading && (
        <StepProgress
          key="upload-send"
          steps={UPLOAD_SEND_STEPS}
          title="Mengirim ke BigQuery..."
        />
      )}

      {preview && !result && !loading && !uploading && (
        <div className="upload-preview">
          <div className="upload-stats">
            <UploadStat label="Total baris" value={preview.total_rows} />
            <UploadStat label="Baris valid" value={preview.valid_rows} tone="good" />
            <UploadStat label="Baris bermasalah" value={preview.invalid_rows} tone={preview.invalid_rows > 0 ? 'warn' : 'neutral'} />
          </div>
          {preview.errors?.length > 0 && (
            <div className="upload-errors">
              <p className="result-card__label">Peringatan validasi (maks 20)</p>
              <ul className="upload-error-list">
                {preview.errors.map((e, i) => (
                  <li key={i} className="upload-error-item">{e}</li>
                ))}
              </ul>
            </div>
          )}
          {preview.sample?.length > 0 && (
            <div className="upload-sample">
              <p className="result-card__label">Preview data yang akan dikirim</p>
              <div className="upload-sample__scroll">
                <table className="upload-table">
                  <thead>
                    <tr>
                      {Object.keys(preview.sample[0]).map((k) => (
                        <th key={k}>{k}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.sample.map((row, i) => (
                      <tr key={i}>
                        {Object.values(row).map((v, j) => (
                          <td key={j}>{v === null || v === undefined ? '—' : String(v)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {result && (
        <div className="upload-result">
          <div className={`upload-result__banner upload-result__banner--${result.status}`}>
            <span className="upload-result__status-badge">
              {result.status === 'success' ? '✓ Berhasil' : result.status === 'partial_success' ? '⚠ Sebagian' : '✗ Gagal'}
            </span>
            <p className="upload-result__msg">{result.message}</p>
          </div>
          <div className="upload-stats">
            <UploadStat label="Total baris" value={result.total_rows} />
            <UploadStat label="Masuk BigQuery" value={result.inserted_rows} tone="good" />
            <UploadStat label="Bermasalah" value={result.invalid_rows || 0} tone={(result.invalid_rows || 0) > 0 ? 'warn' : 'neutral'} />
          </div>
          <p className="input-hint">Tabel tujuan: <code>{result.table}</code></p>
          {result.errors?.length > 0 && (
            <div className="upload-errors">
              <p className="result-card__label">Detail error</p>
              <ul className="upload-error-list">
                {result.errors.map((e, i) => (
                  <li key={i} className="upload-error-item">{e}</li>
                ))}
              </ul>
            </div>
          )}
          <div className="action-bar">
            <button className="primary-btn" onClick={resetAll}>
              Upload file lain
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function UploadStat({ label, value, tone = 'neutral' }) {
  return (
    <div className={`upload-stat upload-stat--${tone}`}>
      <p className="upload-stat__value">{typeof value === 'number' ? value.toLocaleString('id-ID') : value}</p>
      <p className="upload-stat__label">{label}</p>
    </div>
  )
}

/* ─────── WaSimResult — render respon simulator sebagai chat bubble ─────── */

const WA_STATUS_META = {
  success: { label: '✓ Tersimpan', tone: 'good' },
  duplicate: { label: '⚠ Duplikat', tone: 'warn' },
  parse_error: { label: '✗ Parse error', tone: 'warn' },
  validation_error: { label: '✗ Validasi gagal', tone: 'warn' },
  rate_limited: { label: '⏳ Rate limit', tone: 'warn' },
  forbidden: { label: '✗ Sender ditolak', tone: 'warn' },
  bq_error: { label: '✗ BigQuery error', tone: 'warn' },
  sheets_error: { label: '✗ Sheet error', tone: 'warn' },
  error: { label: '✗ Error', tone: 'warn' },
}

function WaSimResult({ sim, body, sender }) {
  const meta = WA_STATUS_META[sim.status] || { label: sim.status || '—', tone: 'neutral' }
  const nowLabel = new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
  const payloadEntries = sim.payload
    ? Object.entries(sim.payload).filter(([, v]) => v !== null && v !== undefined && v !== '')
    : []

  return (
    <div className="wa-sim-result">
      {/* Meta bar */}
      <div className="wa-sim-result__meta">
        <span className={`wa-status-pill upload-stat upload-stat--${meta.tone}`}>{meta.label}</span>
        <span className="wa-sim-result__meta-info">Status backend: <code>{sim.status || '—'}</code></span>
        <span className="wa-sim-result__meta-info">Sender: <code>{sender || '—'}</code></span>
      </div>

      {/* Chat bubble preview */}
      <div className="wa-chat">
        <div className="wa-chat__bubble wa-chat__bubble--in">
          <pre className="wa-chat__text">{body || '(kosong)'}</pre>
          <span className="wa-chat__time">{nowLabel} ✓✓</span>
        </div>
        <div className="wa-chat__bubble wa-chat__bubble--out">
          <pre className="wa-chat__text">{sim.reply || '(bot tidak balas)'}</pre>
          <span className="wa-chat__time">{nowLabel}</span>
        </div>
      </div>

      {/* Payload grid — muncul cuma kalau pipeline sukses sampai parse */}
      {payloadEntries.length > 0 && (
        <div className="wa-sim-result__payload">
          <p className="wa-sim-result__payload-label">Payload ke BigQuery</p>
          <div className="wa-sim-result__grid">
            {payloadEntries.map(([k, v]) => (
              <div key={k} className="wa-sim-result__cell">
                <span className="wa-sim-result__k">{k}</span>
                <span className="wa-sim-result__v">{String(v)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/* ─────── WaPanel (WhatsApp Bot) ─────── */

// Preset contoh pesan supaya demo enak — tombol "Quick fill" tinggal klik.
const WA_EXAMPLES = [
  {
    label: 'Key:Value (lengkap)',
    body: `Invoice: 900001
StockCode: SKU-DEMO
Description: Demo Meta WA Key-Value
Quantity: 3
InvoiceDate: 2026-04-20 14:00
Price: 75000
Customer ID: 99001
Country: Indonesia`,
  },
  {
    label: 'CSV 1 baris',
    body: '900002,SKU-CSV,Demo Meta WA CSV,2,2026-04-20 14:05,50000,99002,Indonesia',
  },
  {
    label: 'Validation error',
    body: `Invoice: 900003
StockCode: SKU-BAD
Description: Quantity negatif
Quantity: -5
InvoiceDate: 2026-04-20 14:10
Price: 10000
Customer ID: 99003
Country: Indonesia`,
  },
  {
    label: 'Parse error',
    body: 'halo bot, gimana kabar?',
  },
]

function WaPanel() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [simBody, setSimBody] = useState('')
  const [simSender, setSimSender] = useState('6281393378081')
  const [simResult, setSimResult] = useState(null)
  const [simLoading, setSimLoading] = useState(false)
  const [retryLoading, setRetryLoading] = useState(false)
  const [retrySummary, setRetrySummary] = useState(null)

  async function runRetry() {
    if (retryLoading) return
    if (!window.confirm('Retry semua baris Sheet yang failed/pending ke BigQuery?')) return
    setRetryLoading(true)
    setRetrySummary(null)
    setError(null)
    try {
      const res = await fetch('/api/wa/retry?max_rows=200', { method: 'POST' })
      const data = await res.json()
      if (data.status === 'error') {
        setError(data.message || 'Retry gagal.')
      } else {
        setRetrySummary(data)
        loadRecent()
      }
    } catch (err) {
      setError(err?.message || 'Retry gagal.')
    } finally {
      setRetryLoading(false)
    }
  }

  async function loadRecent() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/wa/recent?limit=30')
      const data = await res.json()
      if (data.status === 'error') {
        setError(data.message || 'Gagal baca Sheet.')
        setRows([])
      } else {
        setRows(data.rows || [])
      }
    } catch (err) {
      setError(err?.message || 'Gagal memuat data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadRecent() }, [])

  async function runSimulate(e) {
    e.preventDefault()
    if (!simBody.trim() || simLoading) return
    setSimLoading(true)
    setSimResult(null)
    try {
      const form = new FormData()
      form.append('body', simBody)
      form.append('sender', simSender || '6281393378081')
      const res = await fetch('/api/wa/simulate', { method: 'POST', body: form })
      const text = await res.text()
      let data = null
      try { data = JSON.parse(text) } catch { /* non-JSON response */ }
      if (!data) {
        setSimResult({ ok: false, status: 'error', reply: text || 'Response kosong', payload: null })
      } else {
        setSimResult(data)
      }
      loadRecent()
    } catch (err) {
      setSimResult({ ok: false, status: 'error', reply: err?.message || 'gagal simulate', payload: null })
    } finally {
      setSimLoading(false)
    }
  }

  function fillExample(body) {
    setSimBody(body)
    setSimResult(null)
  }

  const statusTone = (s) => {
    const v = String(s || '').toLowerCase()
    if (v === 'inserted') return 'good'
    if (v === 'failed') return 'warn'
    if (v === 'pending') return 'neutral'
    return 'neutral'
  }

  return (
    <div className="daily-panel upload-panel">
      <div className="daily-panel__header">
        <div>
          <p className="daily-panel__title">WhatsApp Bot</p>
          <p className="daily-panel__desc">
            Transaksi yang masuk via WA otomatis di-staging ke Google Sheet lalu dikirim ke BigQuery.
          </p>
        </div>
        <div className="daily-panel__actions">
          <button className="ghost-btn" onClick={loadRecent} disabled={loading}>
            {loading ? 'Memuat...' : 'Muat ulang'}
          </button>
          <button className="primary-btn" onClick={runRetry} disabled={retryLoading}>
            {retryLoading ? 'Retry...' : 'Retry baris failed/pending'}
          </button>
        </div>
      </div>

      {retrySummary && (
        <div className="upload-result__banner upload-result__banner--success" style={{marginTop:'8px'}}>
          <span className="upload-result__status-badge">✓ Retry selesai</span>
          <p className="upload-result__msg">
            Scanned {retrySummary.scanned} · masuk BQ {retrySummary.inserted} ·
            masih gagal {retrySummary.still_failed} · duplikat {retrySummary.duplicates || 0} ·
            skipped {retrySummary.skipped_malformed}
          </p>
        </div>
      )}

      {/* Format cheatsheet */}
      <div className="upload-panel__schema" style={{ width: '100%' }}>
        <p className="upload-panel__schema-label">Format yang diterima bot</p>
        <pre className="wa-cheatsheet">{`1) CSV 1 baris:
489438,21329,DINOSAURS WRITING SET,28,2009-12-01 09:24:00,0.98,18102.0,United Kingdom

2) Multiline Key:Value:
Invoice : 489438
StockCode : 21329
Description : DINOSAURS WRITING SET
Quantity : 28
InvoiceDate : 2009-12-01 09:24:00
Price : 0.98
Customer ID : 18102.0
Country : United Kingdom`}</pre>
      </div>

      {/* Simulator — testing tanpa Meta */}
      <form className="wa-simulator" onSubmit={runSimulate}>
        <div className="wa-simulator__header">
          <p className="result-card__label">Simulator — kirim pesan seolah dari WhatsApp</p>
          <div className="wa-simulator__quickfill">
            {WA_EXAMPLES.map((ex) => (
              <button
                key={ex.label}
                type="button"
                className="ghost-btn wa-simulator__example"
                onClick={() => fillExample(ex.body)}
                disabled={simLoading}
              >
                {ex.label}
              </button>
            ))}
          </div>
        </div>

        <textarea
          className="wa-simulator__body"
          rows={7}
          placeholder="Tempel pesan WA di sini (salah satu format di atas), atau klik tombol Quick fill di atas..."
          value={simBody}
          onChange={(e) => setSimBody(e.target.value)}
          disabled={simLoading}
        />
        <div className="wa-simulator__controls">
          <input
            className="wa-simulator__sender"
            type="text"
            value={simSender}
            onChange={(e) => setSimSender(e.target.value)}
            placeholder="wa_id pengirim (mis. 6281234567890)"
            disabled={simLoading}
          />
          <button className="primary-btn" type="submit" disabled={simLoading || !simBody.trim()}>
            {simLoading ? 'Memproses...' : 'Kirim simulasi'}
          </button>
        </div>

        {simResult && <WaSimResult sim={simResult} body={simBody} sender={simSender} />}
      </form>

      {error && <HumaneError message={error} />}

      {/* Riwayat */}
      <div className="daily-history">
        <p className="daily-history__label">Riwayat transaksi WA ({rows.length})</p>
        {!loading && rows.length === 0 && !error && (
          <p className="input-hint">Belum ada transaksi masuk. Pastikan Google Sheet sudah di-share ke service account.</p>
        )}
        {rows.length > 0 && (
          <div className="upload-sample__scroll">
            <table className="upload-table">
              <thead>
                <tr>
                  <th>Waktu</th>
                  <th>Sender</th>
                  <th>Invoice</th>
                  <th>Stock</th>
                  <th>Qty</th>
                  <th>Price</th>
                  <th>Customer</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i}>
                    <td>{(r.received_at || '').replace('T', ' ').slice(0, 19)}</td>
                    <td>{r.sender}</td>
                    <td>{r.Invoice}</td>
                    <td>{r.StockCode}</td>
                    <td>{r.Quantity}</td>
                    <td>{r.Price}</td>
                    <td>{r['Customer ID'] || '—'}</td>
                    <td>
                      <span className={`upload-stat upload-stat--${statusTone(r.bq_status)} wa-status-pill`}>
                        {r.bq_status || '—'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
