import { useEffect, useRef, useState } from 'react';
import ScreenHeader from '../ui/ScreenHeader.jsx';
import Pill from '../ui/Pill.jsx';
import Icon from '../ui/Icon.jsx';
import Button from '../ui/Button.jsx';
import Input from '../ui/Input.jsx';
import Card from '../ui/Card.jsx';
import { api } from '../api/client.js';

const rupiah = (n) =>
  new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 })
    .format(Number(n) || 0);

const EMPTY_ROW = { product: '', qty: '', unit_price: '' };

export default function CheckoutScreen() {
  const [items, setItems] = useState([{ ...EMPTY_ROW }]);
  const [customer, setCustomer] = useState('');
  const [qrToken, setQrToken] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [sentToken, setSentToken] = useState(false);
  // Autocomplete: satu daftar aktif untuk baris yang sedang diketik.
  const [suggest, setSuggest] = useState({ row: -1, options: [] });
  const debounceRef = useRef();

  useEffect(() => () => clearTimeout(debounceRef.current), []);

  const setRow = (i, patch) => {
    setItems((prev) => prev.map((row, idx) => (idx === i ? { ...row, ...patch } : row)));
  };

  const onProductChange = (i, value) => {
    setRow(i, { product: value });
    clearTimeout(debounceRef.current);
    if (value.trim().length < 2) {
      setSuggest({ row: -1, options: [] });
      return;
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const r = await api.productsSearch(value.trim());
        setSuggest({ row: i, options: (r?.products || []).slice(0, 5) });
      } catch {
        // Katalog kosong / gagal → kasir tetap bisa ketik manual.
        setSuggest({ row: -1, options: [] });
      }
    }, 250);
  };

  const pickSuggestion = (i, p) => {
    setRow(i, { product: p.name, ...(p.price != null ? { unit_price: p.price } : {}) });
    setSuggest({ row: -1, options: [] });
  };

  const grandTotal = items.reduce(
    (sum, it) => sum + (Number(it.qty) || 0) * (Number(it.unit_price) || 0), 0,
  );

  const canSubmit = !busy && items.every(
    (it) => it.product.trim() && Number(it.qty) > 0 && Number(it.unit_price) >= 0,
  );

  const submit = async () => {
    setBusy(true);
    setError(null);
    setResult(null);
    const tokenIncluded = Boolean(qrToken.trim());
    try {
      const payload = {
        items: items.map((it) => ({
          product: it.product.trim(),
          qty: Number(it.qty),
          unit_price: Number(it.unit_price),
        })),
        ...(customer.trim() ? { customer: customer.trim() } : {}),
        // Token QR masuk MENTAH — single-use + TTL 90 detik; pre-validate via
        // /scan/validate akan MEMBAKAR nonce dan attach gagal diam-diam.
        ...(tokenIncluded ? { customer_qr_token: qrToken.trim() } : {}),
      };
      const res = await api.checkoutConfirm(payload);
      if (res?.ok === false) {
        setError(res.reply || 'Gagal menyimpan transaksi.');
        return;
      }
      setSentToken(tokenIncluded);
      setResult(res);
    } catch (err) {
      setError(err.message || 'Gagal menyimpan transaksi.');
    } finally {
      setBusy(false);
    }
  };

  const resetForm = () => {
    setItems([{ ...EMPTY_ROW }]);
    setCustomer('');
    setQrToken('');
    setResult(null);
    setError(null);
    setSentToken(false);
  };

  // Attach dianggap GAGAL bila token ikut terkirim tapi backend tidak
  // menautkan customer (ok:true + customer_user_id null + catatan di reply).
  const attachFailed = result && sentToken && !result.customer_user_id;

  return (
    <div style={{ minHeight: '100%' }}>
      <ScreenHeader subtitle="Kasir" />

      <div style={{ padding: '4px 18px 12px' }}>
        <Pill bg="var(--violet-soft)" mono>KASIR · MULTI-ITEM</Pill>
        <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 22, letterSpacing: '-0.02em', margin: '10px 0 4px' }}>
          Catat transaksi
        </h2>
        <p style={{ color: 'var(--ink-3)', fontSize: 12.5, lineHeight: 1.5 }}>
          Beberapa item sekaligus, opsional tautkan pelanggan lewat token QR.
        </p>
      </div>

      {result ? (
        <div style={{ padding: '0 18px 24px', display: 'grid', gap: 12 }}>
          <Card style={{ display: 'grid', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 34, height: 34, borderRadius: 10, background: 'var(--lime)', border: '1.5px solid var(--ink)', display: 'grid', placeItems: 'center' }}>
                <Icon name="check" size={18} stroke="var(--ink)" strokeWidth={2.4} />
              </div>
              <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 16 }}>
                Transaksi tersimpan
              </div>
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11.5, color: 'var(--ink-3)' }}>
              {result.invoice} · {result.item_count} item · {rupiah(result.grand_total)}
            </div>
            {result.customer_user_id && (
              <div style={{ fontSize: 12.5, color: 'var(--success)', fontWeight: 600 }}>
                Customer tertaut ✓ {result.is_new_member
                  ? '(member baru)'
                  : result.member_since ? `(member sejak ${result.member_since})` : ''}
              </div>
            )}
          </Card>

          {attachFailed && (
            <div
              role="alert"
              style={{ padding: '12px 14px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 12, fontSize: 12.5, lineHeight: 1.5 }}
            >
              <strong>Poin pelanggan tidak terhubung.</strong> {result.reply}
              {' '}Token QR sekali pakai & kedaluwarsa 90 detik — minta pelanggan tampilkan QR baru, lalu ulangi di transaksi berikutnya.
            </div>
          )}

          <Button onClick={resetForm} style={{ justifySelf: 'start' }}>Transaksi baru</Button>
        </div>
      ) : (
        <div style={{ padding: '0 18px 24px', display: 'grid', gap: 12 }}>
          <Card style={{ display: 'grid', gap: 12 }}>
            {items.map((it, i) => (
              <div key={i} style={{ display: 'grid', gap: 8, paddingTop: i ? 10 : 0, borderTop: i ? '1px dashed var(--border-soft)' : 'none' }}>
                <div style={{ position: 'relative' }}>
                  <Input
                    id={`product-${i}`}
                    label={`Produk ${i + 1}`}
                    placeholder="mis. Kopi Susu"
                    value={it.product}
                    onChange={(e) => onProductChange(i, e.target.value)}
                    autoComplete="off"
                  />
                  {suggest.row === i && suggest.options.length > 0 && (
                    <ul
                      role="listbox"
                      style={{ listStyle: 'none', margin: '4px 0 0', padding: 4, background: 'var(--surface)', border: '1.5px solid var(--ink)', borderRadius: 10, boxShadow: 'var(--shadow-pop-xs)', display: 'grid', gap: 2 }}
                    >
                      {suggest.options.map((p) => (
                        <li key={p.id}>
                          <button
                            type="button"
                            role="option"
                            aria-selected="false"
                            onClick={() => pickSuggestion(i, p)}
                            style={{ width: '100%', textAlign: 'left', padding: '8px 10px', border: 'none', background: 'transparent', borderRadius: 8, fontSize: 13, cursor: 'pointer' }}
                          >
                            {p.name}{p.price != null ? ` · ${rupiah(p.price)}` : ''}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 8, alignItems: 'end' }}>
                  <Input
                    id={`qty-${i}`}
                    label={`Jumlah ${i + 1}`}
                    type="number"
                    min="1"
                    placeholder="1"
                    value={it.qty}
                    onChange={(e) => setRow(i, { qty: e.target.value })}
                  />
                  <Input
                    id={`price-${i}`}
                    label={`Harga satuan ${i + 1}`}
                    type="number"
                    min="0"
                    placeholder="15000"
                    value={it.unit_price}
                    onChange={(e) => setRow(i, { unit_price: e.target.value })}
                  />
                  {items.length > 1 && (
                    <button
                      type="button"
                      aria-label={`Hapus baris ${i + 1}`}
                      onClick={() => setItems((prev) => prev.filter((_, idx) => idx !== i))}
                      style={{ width: 44, height: 44, borderRadius: 12, border: '1.5px solid var(--ink)', background: 'var(--surface)', color: 'var(--error)', display: 'grid', placeItems: 'center', cursor: 'pointer' }}
                    >
                      <Icon name="trash" size={16} stroke="var(--error)" strokeWidth={2} />
                    </button>
                  )}
                </div>
              </div>
            ))}

            <Button variant="secondary" onClick={() => setItems((prev) => [...prev, { ...EMPTY_ROW }])} style={{ justifySelf: 'start' }}>
              + Tambah baris
            </Button>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: 10, borderTop: '2px solid var(--border)' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5, color: 'var(--ink-3)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Total</span>
              <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 18 }}>{rupiah(grandTotal)}</span>
            </div>
          </Card>

          <Card style={{ display: 'grid', gap: 10 }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 700, color: 'var(--ink-3)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              Pelanggan (opsional)
            </div>
            <Input
              id="customer-name"
              label="Nama pelanggan"
              placeholder="mis. Sari"
              value={customer}
              onChange={(e) => setCustomer(e.target.value)}
            />
            <Input
              id="qr-token"
              label="Token QR customer (opsional)"
              placeholder="tempel token dari HP pelanggan"
              hint="Minta pelanggan buka QR di HP-nya; token sekali pakai & kedaluwarsa 90 detik — tempel lalu langsung simpan."
              value={qrToken}
              onChange={(e) => setQrToken(e.target.value)}
              autoComplete="off"
            />
          </Card>

          {error && (
            <div role="alert" style={{ padding: '12px 14px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 12, fontSize: 12.5 }}>
              {error}
            </div>
          )}

          <Button onClick={submit} disabled={!canSubmit} style={{ width: '100%' }}>
            {busy ? 'Menyimpan…' : 'Simpan transaksi'}
          </Button>
        </div>
      )}
    </div>
  );
}
