import Icon from '../ui/Icon.jsx';
import Pill from '../ui/Pill.jsx';

const formatRp = (n) => 'Rp ' + new Intl.NumberFormat('id-ID').format(Number(n) || 0);

// Layar konfirmasi hasil parser MULTI-ITEM (paritas voice_parsed.dart A04):
// tiap baris bisa dikoreksi, baris bisa ditambah/dihapus, grand total live.
// Parser sengaja best-effort — layar ini pagar terakhirnya.
function ItemRow({ item, index, editing, submitting, onChangeItem, onRemoveItem }) {
  const subtotal = (Number(item.qty) || 0) * (Number(item.unit_price) || 0);
  return (
    <div
      data-testid={`voice-item-${index}`}
      style={{
        border: '1.5px solid var(--border)',
        borderRadius: 12,
        padding: '10px 12px',
        display: 'grid',
        gap: 8,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {editing ? (
          <input
            aria-label={`Produk item ${index + 1}`}
            value={item.product}
            onChange={(e) => onChangeItem(index, 'product', e.target.value)}
            placeholder="Nama produk"
            style={{ ...inputStyle, flex: 1, fontWeight: 700 }}
          />
        ) : (
          <div style={{ flex: 1, fontWeight: 700, fontSize: 14 }}>
            {item.product || <span style={{ color: 'var(--ink-4)' }}>Nama produk…</span>}
          </div>
        )}
        {editing && (
          <button
            type="button"
            aria-label={`Hapus item ${index + 1}`}
            data-testid={`voice-item-remove-${index}`}
            disabled={submitting}
            onClick={() => onRemoveItem(index)}
            style={{
              width: 32, height: 32, borderRadius: 9, background: 'var(--surface)',
              border: '1.5px solid var(--border)', display: 'grid', placeItems: 'center', cursor: 'pointer',
            }}
          >
            <Icon name="trash" size={14} stroke="var(--error)" />
          </button>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr 1.2fr', gap: 8, alignItems: 'center' }}>
        <div>
          <div style={labelStyle}>Jumlah</div>
          {editing ? (
            <input
              aria-label={`Jumlah item ${index + 1}`}
              inputMode="numeric"
              value={item.qty}
              onChange={(e) => onChangeItem(index, 'qty', e.target.value)}
              style={{ ...inputStyle, fontFamily: 'var(--font-mono)' }}
            />
          ) : (
            <div style={valueStyle}>{item.qty}</div>
          )}
        </div>
        <div>
          <div style={labelStyle}>Harga satuan</div>
          {editing ? (
            <input
              aria-label={`Harga item ${index + 1}`}
              inputMode="numeric"
              value={item.unit_price}
              onChange={(e) => onChangeItem(index, 'unit_price', e.target.value)}
              style={{ ...inputStyle, fontFamily: 'var(--font-mono)' }}
            />
          ) : (
            <div style={valueStyle}>{formatRp(item.unit_price)}</div>
          )}
        </div>
        <div>
          <div style={labelStyle}>Subtotal</div>
          <div style={{ ...valueStyle, fontWeight: 700 }}>{formatRp(subtotal)}</div>
        </div>
      </div>
    </div>
  );
}

const labelStyle = {
  fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--ink-4)',
  letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 3,
};
const valueStyle = { fontFamily: 'var(--font-mono)', fontSize: 13 };
const inputStyle = {
  fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--ink)',
  background: 'var(--surface)', padding: '8px 10px',
  border: '1.5px solid var(--border)', borderRadius: 9,
  outline: 'none', width: '100%', boxSizing: 'border-box',
};

export default function VoiceParsed({
  tx, editing, submitting, error,
  onEdit, onChangeMeta, onChangeItem, onAddItem, onRemoveItem, onRetry, onConfirm,
}) {
  const grandTotal = tx.items.reduce(
    (sum, it) => sum + (Number(it.qty) || 0) * (Number(it.unit_price) || 0),
    0,
  );

  return (
    <div style={{ flex: 1, padding: '14px 18px 100px', overflowY: 'auto' }}>
      <div style={{ fontSize: 13, color: 'var(--ink-2)', lineHeight: 1.5, marginBottom: 14 }}>
        AI menangkap <strong>{tx.items.length} item</strong>. Periksa lalu konfirmasi.
      </div>

      <div
        style={{
          background: 'var(--surface)',
          border: '1.5px solid var(--ink)',
          borderRadius: 18,
          boxShadow: '2px 2px 0 var(--ink)',
          overflow: 'hidden',
        }}
      >
        {/* header invoice + toggle edit */}
        <div
          style={{
            padding: '14px 16px 12px',
            background: 'var(--violet)',
            color: '#fff',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <div style={{ minWidth: 0 }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, opacity: 0.8, letterSpacing: '0.06em' }}>
              INVOICE · OTOMATIS
            </div>
            {editing ? (
              <input
                aria-label="Invoice"
                value={tx.invoice}
                onChange={(e) => onChangeMeta('invoice', e.target.value)}
                style={{ ...inputStyle, marginTop: 4, fontFamily: 'var(--font-mono)' }}
              />
            ) : (
              <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 18, marginTop: 2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {tx.invoice || 'Otomatis'}
              </div>
            )}
          </div>
          <button
            type="button"
            onClick={onEdit}
            style={{
              display: 'flex', alignItems: 'center', gap: 6, padding: '6px 10px',
              background: 'rgba(255,255,255,0.16)', border: '1px solid rgba(255,255,255,0.5)',
              borderRadius: 8, color: '#fff', fontSize: 11, fontWeight: 600,
              cursor: 'pointer', fontFamily: 'var(--font-body)', flexShrink: 0,
            }}
          >
            <Icon name="edit" size={12} stroke="#fff" strokeWidth={2} />
            {editing ? 'Selesai' : 'Edit'}
          </button>
        </div>

        {/* daftar item */}
        <div style={{ padding: '12px 14px', display: 'grid', gap: 10 }}>
          {tx.items.map((it, i) => (
            <ItemRow
              key={i}
              item={it}
              index={i}
              editing={editing}
              submitting={submitting}
              onChangeItem={onChangeItem}
              onRemoveItem={onRemoveItem}
            />
          ))}
          {editing && (
            <button
              type="button"
              data-testid="voice-item-add"
              onClick={onAddItem}
              disabled={submitting}
              style={{
                padding: '10px', background: 'var(--surface-soft)', color: 'var(--ink-2)',
                border: '1.5px dashed var(--border)', borderRadius: 10, cursor: 'pointer',
                fontFamily: 'var(--font-body)', fontWeight: 600, fontSize: 12.5,
              }}
            >
              + Tambah item
            </button>
          )}

          {/* pelanggan + grand total */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, borderTop: '1px dashed var(--border-soft)', paddingTop: 10 }}>
            <div style={{ flex: 1 }}>
              <div style={labelStyle}>Pelanggan</div>
              {editing ? (
                <input
                  aria-label="Pelanggan"
                  value={tx.customer || ''}
                  onChange={(e) => onChangeMeta('customer', e.target.value)}
                  style={inputStyle}
                />
              ) : (
                <div style={{ fontSize: 13 }}>{tx.customer || 'Walk-in'}</div>
              )}
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={labelStyle}>Grand Total</div>
              <div data-testid="voice-grand-total" style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 18, color: 'var(--violet-deep)' }}>
                {formatRp(grandTotal)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* destination chips */}
      <div style={{ marginTop: 16, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-3)', fontWeight: 700, letterSpacing: '0.06em' }}>
          AKAN DISIMPAN KE:
        </div>
        <Pill bg="var(--surface)" sm mono>📊 Google Sheets</Pill>
        <Pill bg="var(--surface)" sm mono>🗄 BigQuery</Pill>
      </div>

      {error && (
        <div
          style={{
            marginTop: 14, padding: '12px 14px', background: 'var(--peach-soft)',
            border: '1.5px solid var(--ink)', borderRadius: 12, fontSize: 12.5,
            color: 'var(--ink-2)', lineHeight: 1.5,
          }}
        >
          {error}
        </div>
      )}

      {/* actions */}
      <div style={{ marginTop: 18, display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 10 }}>
        <button
          type="button"
          onClick={onRetry}
          disabled={submitting}
          style={{
            padding: '14px 12px', background: 'var(--surface)', color: 'var(--ink)',
            border: '1.5px solid var(--ink)', borderRadius: 14, boxShadow: '2px 2px 0 var(--ink)',
            cursor: submitting ? 'default' : 'pointer', fontFamily: 'var(--font-body)',
            fontWeight: 600, fontSize: 13, display: 'flex', alignItems: 'center',
            justifyContent: 'center', gap: 6, opacity: submitting ? 0.5 : 1,
          }}
        >
          <Icon name="mic" size={16} strokeWidth={2} /> Ulangi
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={submitting || tx.items.length === 0}
          style={{
            padding: '14px 14px', background: 'var(--ink)', color: 'var(--lime)',
            border: '1.5px solid var(--ink)', borderRadius: 14, boxShadow: 'var(--shadow-pop)',
            cursor: submitting ? 'default' : 'pointer', fontFamily: 'var(--font-body)',
            fontWeight: 700, fontSize: 13.5, display: 'flex', alignItems: 'center',
            justifyContent: 'center', gap: 8, opacity: submitting || tx.items.length === 0 ? 0.6 : 1,
          }}
        >
          {submitting ? (
            <span
              style={{
                width: 18, height: 18, borderRadius: '50%',
                border: '2px solid rgba(212,245,106,0.35)', borderTopColor: 'var(--lime)',
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
