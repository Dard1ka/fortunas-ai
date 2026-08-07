import Icon from '../ui/Icon.jsx';
import Pill from '../ui/Pill.jsx';

const formatRp = (n) => 'Rp ' + new Intl.NumberFormat('id-ID').format(Number(n) || 0);

export default function VoiceParsed({ tx, editing, onChange, onEdit, onRetry, onConfirm, submitting, error }) {
  return (
    <div style={{ flex: 1, padding: '14px 18px 100px', overflowY: 'auto' }}>
      <div style={{ fontSize: 13, color: 'var(--ink-2)', lineHeight: 1.5, marginBottom: 14 }}>
        AI menangkap <strong>1 transaksi</strong>. Periksa lalu konfirmasi.
      </div>

      {/* transaction card */}
      <div
        style={{
          background: 'var(--surface)',
          border: '1.5px solid var(--ink)',
          borderRadius: 18,
          boxShadow: '2px 2px 0 var(--ink)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            padding: '14px 16px 12px',
            background: 'var(--violet)',
            color: '#fff',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                opacity: 0.8,
                letterSpacing: '0.06em',
              }}
            >
              INVOICE · OTOMATIS
            </div>
            <div
              style={{
                fontFamily: 'var(--font-display)',
                fontWeight: 700,
                fontSize: 18,
                marginTop: 2,
              }}
            >
              {tx.invoice || 'Otomatis'}
            </div>
          </div>
          <button
            type="button"
            onClick={onEdit}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '6px 10px',
              background: 'rgba(255,255,255,0.16)',
              border: '1px solid rgba(255,255,255,0.5)',
              borderRadius: 8,
              color: '#fff',
              fontSize: 11,
              fontWeight: 600,
              cursor: 'pointer',
              fontFamily: 'var(--font-body)',
            }}
          >
            <Icon name="edit" size={12} stroke="#fff" strokeWidth={2} />
            {editing ? 'Selesai' : 'Edit'}
          </button>
        </div>

        <Field label="Produk"        value={tx.product}     k="product"     editing={editing} onChange={onChange} />
        <Field label="Jumlah"        value={tx.qty}         k="qty"         editing={editing} onChange={onChange} mono />
        <Field label="Harga satuan"  value={tx.unit_price}  k="unit_price"  editing={editing} onChange={onChange} mono display={formatRp(tx.unit_price)} />
        <Field label="Pelanggan"     value={tx.customer || ''} k="customer" editing={editing} onChange={onChange} />
        <Field label="Negara"        value={tx.country || 'Indonesia'} k="country" editing={editing} onChange={onChange} />
        <Field label="TOTAL"         value={tx.total}       k="total"       editing={false}   onChange={onChange} mono accent display={formatRp(tx.total)} />
      </div>

      {/* destination chips */}
      <div
        style={{
          marginTop: 16,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          flexWrap: 'wrap',
        }}
      >
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--ink-3)',
            fontWeight: 700,
            letterSpacing: '0.06em',
          }}
        >
          AKAN DISIMPAN KE:
        </div>
        <Pill bg="var(--surface)" sm mono>📊 Google Sheets</Pill>
        <Pill bg="var(--surface)" sm mono>🗄 BigQuery</Pill>
      </div>

      {error && (
        <div
          style={{
            marginTop: 14,
            padding: '12px 14px',
            background: 'var(--peach-soft)',
            border: '1.5px solid var(--ink)',
            borderRadius: 12,
            fontSize: 12.5,
            color: 'var(--ink-2)',
            lineHeight: 1.5,
          }}
        >
          {error}
        </div>
      )}

      {/* actions */}
      <div
        style={{
          marginTop: 18,
          display: 'grid',
          gridTemplateColumns: '1fr 2fr',
          gap: 10,
        }}
      >
        <button
          type="button"
          onClick={onRetry}
          disabled={submitting}
          style={{
            padding: '14px 12px',
            background: 'var(--surface)',
            color: 'var(--ink)',
            border: '1.5px solid var(--ink)',
            borderRadius: 14,
            boxShadow: '2px 2px 0 var(--ink)',
            cursor: submitting ? 'default' : 'pointer',
            fontFamily: 'var(--font-body)',
            fontWeight: 600,
            fontSize: 13,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            opacity: submitting ? 0.5 : 1,
          }}
        >
          <Icon name="mic" size={16} strokeWidth={2} /> Ulangi
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={submitting}
          style={{
            padding: '14px 14px',
            background: 'var(--ink)',
            color: 'var(--lime)',
            border: '1.5px solid var(--ink)',
            borderRadius: 14,
            boxShadow: 'var(--shadow-pop)',
            cursor: submitting ? 'default' : 'pointer',
            fontFamily: 'var(--font-body)',
            fontWeight: 700,
            fontSize: 13.5,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            opacity: submitting ? 0.6 : 1,
          }}
        >
          {submitting ? (
            <span
              style={{
                width: 18,
                height: 18,
                borderRadius: '50%',
                border: '2px solid rgba(212,245,106,0.35)',
                borderTopColor: 'var(--lime)',
                animation: 'fortunas-spin 0.7s linear infinite',
              }}
            />
          ) : (
            <Icon name="check" size={18} stroke="var(--lime)" strokeWidth={2.4} />
          )}
          {submitting ? 'Menyimpan…' : 'Konfirmasi & Simpan'}
        </button>
      </div>
    </div>
  );
}

function Field({ label, value, k, editing, onChange, mono, accent, display }) {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: 10,
        padding: '12px 14px',
        borderBottom: '1px solid var(--border-hair)',
      }}
    >
      <div
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 10.5,
          color: 'var(--ink-3)',
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
          fontWeight: 600,
        }}
      >
        {label}
      </div>
      {editing ? (
        <input
          value={value ?? ''}
          onChange={(e) => onChange(k, e.target.value)}
          style={{
            background: 'var(--surface-soft)',
            border: '1.5px solid var(--ink)',
            borderRadius: 8,
            padding: '6px 10px',
            fontFamily: mono ? 'var(--font-mono)' : 'var(--font-display)',
            fontWeight: 600,
            fontSize: 14,
            color: 'var(--ink)',
            textAlign: 'right',
            width: 140,
            outline: 'none',
          }}
        />
      ) : (
        <div
          style={{
            fontFamily: mono ? 'var(--font-mono)' : 'var(--font-display)',
            fontSize: accent ? 17 : 14.5,
            fontWeight: accent ? 700 : 600,
            color: accent ? 'var(--violet)' : 'var(--ink)',
            letterSpacing: '-0.01em',
            textAlign: 'right',
          }}
        >
          {display ?? value}
        </div>
      )}
    </div>
  );
}
