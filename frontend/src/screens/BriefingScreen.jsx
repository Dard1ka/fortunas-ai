import { useEffect, useState } from 'react';
import ScreenHeader from '../ui/ScreenHeader.jsx';
import Pill from '../ui/Pill.jsx';
import Icon from '../ui/Icon.jsx';
import { api } from '../api/client.js';

const ICON_FOR_ANALYSIS = {
  repeat_customer:    'user',
  high_value_customer: 'coin',
  peak_hour:           'clock',
  bundle_opportunity:  'bag',
};

const COLOR_FOR_ANALYSIS = {
  repeat_customer:    'var(--violet)',
  high_value_customer: 'var(--sky)',
  peak_hour:           'var(--lime)',
  bundle_opportunity:  'var(--peach)',
};

function shortKpi(section) {
  // Take the first finding bullet (usually contains the headline number) and condense to <= 12 chars.
  const f = section.top_findings?.[0] || section.summary || '';
  const m = f.match(/(\d[\d.,]*\s*(?:%|jam|orang|trx|item|bundel|Rp\s*[\d.,kKmMjJ]*)?)/);
  if (m) return m[1].trim();
  return section.label?.split(' ')[1] || '—';
}

export default function BriefingScreen() {
  const [latest, setLatest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const ctrl = new AbortController();
    api.reportDaily(ctrl.signal)
      .then((data) => {
        if (data?.status === 'empty' || !data?.latest) {
          setLatest(null);
        } else {
          setLatest(data.latest);
        }
        setLoading(false);
      })
      .catch((err) => { setError(err.message); setLoading(false); });
    return () => ctrl.abort();
  }, []);

  return (
    <div style={{ minHeight: '100%' }}>
      <ScreenHeader />

      <div style={{ padding: '4px 18px 12px' }}>
        <Pill bg="var(--lime)" mono>BRIEFING · HARI INI</Pill>
        <h2
          style={{
            fontFamily: 'var(--font-display)',
            fontWeight: 700,
            fontSize: 22,
            letterSpacing: '-0.02em',
            margin: '10px 0 4px',
          }}
        >
          {loading ? 'Memuat briefing harian…' : (latest ? `Briefing ${latest.date}` : 'Belum ada briefing tersimpan')}
        </h2>
        <p style={{ color: 'var(--ink-3)', fontSize: 12.5, lineHeight: 1.5 }}>
          {loading
            ? 'Mengambil data terakhir dari server…'
            : (latest
                ? `${latest.sections?.length ?? 0} analisis selesai.`
                : 'Jalankan POST /report/daily/run dari Swagger atau klik "Mulai Briefing" di sesi sebelumnya untuk mengisi.')}
        </p>
      </div>

      {error && (
        <div style={{ margin: '0 18px 12px', padding: '14px 16px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 14, fontSize: 13 }}>
          {error}
        </div>
      )}

      {loading && <SkeletonBriefing />}

      {!loading && latest && (
        <>
          {/* Executive summary dark card */}
          <div
            style={{
              margin: '0 18px 12px',
              position: 'relative',
              overflow: 'hidden',
              background: 'var(--ink)',
              color: '#fff',
              borderRadius: 20,
              border: '1.5px solid var(--ink)',
              boxShadow: 'var(--shadow-pop)',
              padding: '18px 18px 20px',
            }}
          >
            <div
              style={{
                position: 'absolute',
                right: -30,
                top: -30,
                width: 110,
                height: 110,
                borderRadius: '50%',
                background: 'var(--lime)',
                opacity: 0.15,
              }}
            />
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                color: 'var(--lime)',
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                fontWeight: 600,
              }}
            >
              Executive Summary
            </div>
            <p
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 15,
                fontWeight: 500,
                lineHeight: 1.5,
                marginTop: 8,
                letterSpacing: '-0.01em',
              }}
            >
              {latest.executive_summary}
            </p>
          </div>

          {/* KPI grid */}
          <div
            style={{
              padding: '0 18px',
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 10,
              marginBottom: 12,
            }}
          >
            {(latest.sections || []).slice(0, 4).map((s) => (
              <div
                key={s.analysis_type}
                style={{
                  background: 'var(--surface)',
                  border: '1.5px solid var(--ink)',
                  borderRadius: 16,
                  padding: 12,
                  boxShadow: '2px 2px 0 var(--ink)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div
                    style={{
                      width: 28,
                      height: 28,
                      borderRadius: 8,
                      background: COLOR_FOR_ANALYSIS[s.analysis_type] || 'var(--violet)',
                      display: 'grid',
                      placeItems: 'center',
                      border: '1.5px solid var(--ink)',
                    }}
                  >
                    <Icon name={ICON_FOR_ANALYSIS[s.analysis_type] || 'chart'} size={15} stroke="var(--ink)" strokeWidth={2} />
                  </div>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 10,
                      fontWeight: 700,
                      color: 'var(--success)',
                    }}
                  >
                    {s.row_count ? `${s.row_count} row` : '—'}
                  </span>
                </div>
                <div
                  style={{
                    fontFamily: 'var(--font-display)',
                    fontSize: 18,
                    fontWeight: 700,
                    letterSpacing: '-0.02em',
                    marginTop: 10,
                    minHeight: 24,
                  }}
                >
                  {shortKpi(s)}
                </div>
                <div
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: 9.5,
                    color: 'var(--ink-3)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.06em',
                    marginTop: 2,
                  }}
                >
                  {s.label}
                </div>
              </div>
            ))}
          </div>

          {/* Top findings flattened */}
          <div style={{ padding: '0 18px 12px' }}>
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
              Temuan Utama
            </div>
            <div style={{ display: 'grid', gap: 8 }}>
              {flatFindings(latest.sections).slice(0, 3).map((f, i) => (
                <div
                  key={`${i}-${f.slice(0, 40)}`}
                  style={{
                    display: 'flex',
                    gap: 10,
                    padding: '10px 12px',
                    background: 'var(--surface-soft)',
                    border: '1.5px solid var(--border-hair)',
                    borderRadius: 12,
                  }}
                >
                  <div
                    style={{
                      flexShrink: 0,
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
                    }}
                  >
                    {i + 1}
                  </div>
                  <div style={{ fontSize: 12.5, color: 'var(--ink-2)', lineHeight: 1.5 }}>{f}</div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function flatFindings(sections) {
  const out = [];
  for (const s of sections || []) {
    for (const f of s.top_findings || []) {
      if (f && !out.includes(f)) out.push(f);
    }
  }
  return out;
}

function SkeletonBriefing() {
  const bar = {
    background: 'linear-gradient(90deg, var(--surface-soft) 0%, var(--surface-hover) 50%, var(--surface-soft) 100%)',
    backgroundSize: '200% 100%',
    animation: 'fortunas-shimmer 1.8s linear infinite',
    borderRadius: 10,
  };
  return (
    <>
      <div style={{ margin: '0 18px 12px', ...bar, height: 120 }} />
      <div style={{ padding: '0 18px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        {[0, 1, 2, 3].map((i) => <div key={i} style={{ ...bar, height: 100 }} />)}
      </div>
    </>
  );
}
