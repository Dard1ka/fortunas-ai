import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../ui/Button.jsx';
import Card from '../ui/Card.jsx';
import Icon from '../ui/Icon.jsx';
import Input from '../ui/Input.jsx';
import Pill from '../ui/Pill.jsx';
import { api } from '../api/client.js';
import { formatRupiah } from '../lib/format.js';

// Halaman pesan publik (pelanggan anonim, TANPA login) + pembayaran QRIS
// statis. SATU route /order, tiga fase di state (paritas Flutter
// public_order_screen.dart): code → menu → order. Refresh halaman
// mengembalikan ke fase kode — sama dengan Flutter, keranjang memang tidak
// dipersist.
const STATUS_LABEL = {
  pending_payment: { label: 'Menunggu bayar', bg: 'var(--peach)' },
  paid:            { label: 'Sudah dibayar',  bg: 'var(--sky)' },
  accepted:        { label: 'Diterima toko',  bg: 'var(--lime)' },
  completed:       { label: 'Selesai',        bg: 'var(--success)' },
  rejected:        { label: 'Ditolak',        bg: 'var(--peach-soft)' },
  expired:         { label: 'Kedaluwarsa',    bg: 'var(--surface-hover)' },
  cancelled:       { label: 'Dibatalkan',     bg: 'var(--peach-soft)' },
};

// Gate UI (backend tetap validasi ulang): bisa dipesan hanya bila harga sudah
// diset DAN (stok tak dilacak ATAU stok > 0).
const orderable = (p) => p.price != null && (p.stock == null || p.stock > 0);

function MenuCard({ product, qty, onAdd, onInc, onDec }) {
  const [imgBroken, setImgBroken] = useState(false);
  return (
    <Card style={{ padding: 10, display: 'grid', gap: 8, alignContent: 'start' }}>
      <div style={{ aspectRatio: '1.2', borderRadius: 10, overflow: 'hidden', background: 'var(--surface-soft)', display: 'grid', placeItems: 'center' }}>
        {product.image_url && !imgBroken ? (
          <img
            src={product.image_url}
            alt={product.name}
            onError={() => setImgBroken(true)}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        ) : (
          <Icon name="bag" size={22} stroke="var(--ink-4)" />
        )}
      </div>
      <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 13, lineHeight: 1.3, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
        {product.name}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 700 }}>
          {product.price != null ? formatRupiah(product.price) : 'Belum ada harga'}
        </span>
        {product.stock === 0 && <Pill bg="var(--peach-soft)" sm>Habis</Pill>}
      </div>
      {!orderable(product) ? (
        <Button variant="secondary" disabled style={{ minHeight: 40, fontSize: 12.5 }}>
          {product.price == null ? 'Belum dijual' : 'Habis'}
        </Button>
      ) : qty === 0 ? (
        <Button data-testid={`menu-add-${product.id}`} variant="secondary" onClick={onAdd} style={{ minHeight: 40, fontSize: 12.5 }}>
          Tambah
        </Button>
      ) : (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', border: '1.5px solid var(--border)', borderRadius: 10 }}>
          <button type="button" data-testid={`menu-dec-${product.id}`} aria-label={`Kurangi ${product.name}`} onClick={onDec} style={stepBtn}>−</button>
          <span data-testid={`menu-qty-${product.id}`} style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 13 }}>{qty}</span>
          <button type="button" data-testid={`menu-inc-${product.id}`} aria-label={`Tambah ${product.name}`} onClick={onInc} style={stepBtn}>+</button>
        </div>
      )}
    </Card>
  );
}

const stepBtn = {
  width: 38, height: 38, border: 'none', background: 'transparent',
  fontSize: 18, fontWeight: 700, cursor: 'pointer', color: 'var(--ink)',
};

export default function PublicOrderScreen() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState('code'); // code | menu | order
  const [codeInput, setCodeInput] = useState('');
  const [umkm, setUmkm] = useState(null);
  const [search, setSearch] = useState('');
  const [cart, setCart] = useState({}); // productId → qty (harga TIDAK disalin)
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(false);
  const [polling, setPolling] = useState(false); // khusus "Perbarui status"
  const [error, setError] = useState(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [custName, setCustName] = useState('');
  const [custPhone, setCustPhone] = useState('');
  const [nameError, setNameError] = useState(null);
  const [phoneError, setPhoneError] = useState(null);
  const [qrisBroken, setQrisBroken] = useState(false);

  const products = useMemo(() => umkm?.products || [], [umkm]);
  const visibleProducts = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return products;
    return products.filter((p) => String(p.name || '').toLowerCase().includes(q));
  }, [products, search]);

  const itemCount = Object.values(cart).reduce((a, b) => a + b, 0);
  // Total SELALU dihitung ulang dari harga menu server — harga bisa berubah
  // antara buka menu dan checkout; keranjang murni {id: qty}.
  const cartTotal = Object.entries(cart).reduce((sum, [id, qty]) => {
    const p = products.find((x) => x.id === Number(id));
    return sum + (p?.price || 0) * qty;
  }, 0);

  const loadMenu = async () => {
    const code = codeInput.trim();
    setError(null);
    if (!code) { setError('Masukkan kode UMKM dulu.'); return; }
    setLoading(true);
    try {
      const r = await api.getPublicUmkm(code);
      setUmkm(r);
      setCart({});     // ganti toko tidak membawa keranjang lama
      setSearch('');
      setPhase('menu');
    } catch (err) {
      setError(err.message || 'Gagal memuat menu.');
    } finally {
      setLoading(false);
    }
  };

  const increment = (p) => {
    if (!orderable(p)) return;
    const current = cart[p.id] || 0;
    if (p.stock != null && current >= p.stock) return; // cegah dini di UI
    setCart({ ...cart, [p.id]: current + 1 });
  };
  const decrement = (p) => {
    const current = cart[p.id] || 0;
    if (current <= 1) {
      const next = { ...cart };
      delete next[p.id]; // hapus key, bukan set 0
      setCart(next);
    } else {
      setCart({ ...cart, [p.id]: current - 1 });
    }
  };

  const createOrder = async () => {
    setNameError(null);
    setPhoneError(null);
    const name = custName.trim();
    const phone = custPhone.trim();
    let bad = false;
    if (!name) { setNameError('Nama wajib diisi'); bad = true; }
    if (!phone) { setPhoneError('No. HP wajib diisi'); bad = true; }
    if (bad) return;
    if (itemCount === 0) { setSheetOpen(false); setError('Keranjang masih kosong.'); return; }

    setLoading(true);
    setError(null);
    try {
      const payload = {
        customer_name: name,
        customer_phone: phone,
        items: Object.entries(cart).map(([id, qty]) => ({ product_id: Number(id), qty })),
      };
      // Kode diambil dari state umkm (respons server), BUKAN teks ketikan user.
      const r = await api.createPublicOrder(umkm.code, payload);
      setOrder(r);
      setSheetOpen(false);
      setQrisBroken(false);
      setPhase('order');
    } catch (err) {
      setSheetOpen(false);
      setError(err.message || 'Gagal membuat pesanan.'); // 429/409/400 BI dari server
    } finally {
      setLoading(false);
    }
  };

  // Dua panggilan berurutan: POST klaim bayar, lalu GET status — state order
  // di-replace dari GET (server = sumber kebenaran), bukan dari respons POST.
  const confirmPayment = async () => {
    if (!order?.payment_order_id) return;
    setLoading(true);
    setError(null);
    try {
      await api.confirmPublicOrderPayment(order.payment_order_id);
      const r = await api.getPublicOrderStatus(order.payment_order_id);
      setOrder(r);
    } catch (err) {
      setError(err.message || 'Gagal mengonfirmasi pembayaran.');
    } finally {
      setLoading(false);
    }
  };

  const refreshStatus = async () => {
    if (!order?.payment_order_id) return;
    setPolling(true);
    setError(null);
    try {
      const r = await api.getPublicOrderStatus(order.payment_order_id);
      setOrder(r);
    } catch (err) {
      setError(err.message || 'Gagal memperbarui status.');
    } finally {
      setPolling(false);
    }
  };

  const backToMenu = () => {
    setOrder(null);
    setCart({});
    setError(null);
    setPhase('menu');
  };
  const reset = () => {
    setUmkm(null);
    setCart({});
    setSearch('');
    setOrder(null);
    setError(null);
    setPhase('code');
  };

  const title = phase === 'code' ? 'Pesan tanpa akun' : phase === 'menu' ? (umkm?.name || 'Menu') : 'Status pesanan';
  const onBack = phase === 'code' ? () => navigate('/') : phase === 'menu' ? () => { reset(); } : backToMenu;

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column' }}>
      {/* Header publik minimal — tanpa pill "AI online" (bukan area UMKM). */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '14px 18px 10px' }}>
        <button
          type="button"
          aria-label="Kembali"
          onClick={onBack}
          style={{ width: 36, height: 36, borderRadius: 12, background: 'var(--surface)', border: '1.5px solid var(--ink)', boxShadow: '2px 2px 0 var(--ink)', display: 'grid', placeItems: 'center', cursor: 'pointer' }}
        >
          <Icon name="arrowLeft" size={16} strokeWidth={2.2} />
        </button>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 17, letterSpacing: '-0.02em', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {title}
          </div>
          {phase === 'menu' && umkm?.city ? (
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-3)' }}>{umkm.city}</div>
          ) : null}
        </div>
      </div>

      {error && (
        <div role="alert" style={{ margin: '0 18px 10px', padding: '10px 14px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 12, fontSize: 12.5 }}>
          {error}
        </div>
      )}

      {phase === 'code' && (
        <div style={{ padding: '8px 18px 24px', display: 'grid', gap: 12 }}>
          <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 22, letterSpacing: '-0.02em', margin: 0 }}>
            Masukkan kode UMKM
          </h2>
          <p style={{ color: 'var(--ink-3)', fontSize: 12.5, margin: 0 }}>
            Kode ada di etalase / struk toko (mis. KDS-001).
          </p>
          <Input
            id="public-order-code"
            data-testid="public-order-code"
            label="Kode UMKM"
            placeholder="KDS-001"
            value={codeInput}
            onChange={(e) => setCodeInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') loadMenu(); }}
            style={{ textTransform: 'uppercase' }}
            autoComplete="off"
          />
          <Button onClick={loadMenu} disabled={loading}>
            {loading ? 'Memuat…' : 'Lihat Menu'}
          </Button>
        </div>
      )}

      {phase === 'menu' && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '0 18px 10px' }}>
            <Input
              id="public-order-search"
              data-testid="public-order-search"
              placeholder="Cari menu…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              autoComplete="off"
            />
          </div>

          {visibleProducts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 36, color: 'var(--ink-3)', fontSize: 13 }}>
              {search.trim()
                ? `Menu "${search.trim()}" tak ditemukan.`
                : 'Belum ada menu di toko ini.'}
            </div>
          ) : (
            <div style={{ padding: '0 18px 120px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              {visibleProducts.map((p) => (
                <MenuCard
                  key={p.id}
                  product={p}
                  qty={cart[p.id] || 0}
                  onAdd={() => increment(p)}
                  onInc={() => increment(p)}
                  onDec={() => decrement(p)}
                />
              ))}
            </div>
          )}

          {itemCount > 0 && (
            <div style={{ position: 'sticky', bottom: 0, margin: 'auto 0 0', padding: '10px 18px max(env(safe-area-inset-bottom), 12px)', background: 'var(--ink)', display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--lime)' }}>{itemCount} item</div>
                <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 18, color: '#fff' }}>{formatRupiah(cartTotal)}</div>
              </div>
              <Button data-testid="public-order-checkout" onClick={() => { setNameError(null); setPhoneError(null); setSheetOpen(true); }}>
                Pesan
              </Button>
            </div>
          )}
        </div>
      )}

      {phase === 'order' && order && (
        <div style={{ padding: '0 18px 24px', display: 'grid', gap: 12 }}>
          <Card style={{ display: 'grid', gap: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Pill bg={(STATUS_LABEL[order.status] || {}).bg || 'var(--surface-soft)'} sm>
                {(STATUS_LABEL[order.status] || {}).label || order.status}
              </Pill>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--ink-3)' }}>#{order.id}</span>
            </div>
            <div style={{ display: 'grid', gap: 3 }}>
              {(order.items || []).map((it, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, color: 'var(--ink-2)' }}>
                  <span>{it.qty}× {it.name}</span>
                  <span style={{ fontFamily: 'var(--font-mono)' }}>{formatRupiah(it.subtotal)}</span>
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px dashed var(--border-soft)', paddingTop: 8 }}>
              <span style={{ fontWeight: 700, fontSize: 13.5 }}>Total</span>
              <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 18 }}>{formatRupiah(order.total)}</span>
            </div>
          </Card>

          {order.status === 'pending_payment' ? (
            <>
              <Card style={{ display: 'grid', gap: 10 }}>
                <div style={{ fontWeight: 700, fontSize: 13 }}>Scan QRIS untuk bayar</div>
                <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 20 }}>
                  Total: {formatRupiah(order.total)}
                </div>
                <div style={{ aspectRatio: '1', borderRadius: 12, overflow: 'hidden', background: 'var(--surface-soft)', display: 'grid', placeItems: 'center' }}>
                  {qrisBroken ? (
                    <div style={{ textAlign: 'center', padding: 18, fontSize: 12.5, color: 'var(--ink-3)' }}>
                      <div style={{ fontWeight: 700, color: 'var(--ink-2)' }}>Kode QRIS belum tersedia.</div>
                      <div style={{ marginTop: 6 }}>
                        Silakan hubungi penjual untuk cara pembayaran lain. Pesananmu tetap tersimpan.
                      </div>
                    </div>
                  ) : (
                    <img
                      src="/payments/qris-statis.png"
                      alt="QRIS pembayaran"
                      onError={() => setQrisBroken(true)}
                      style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                    />
                  )}
                </div>
              </Card>
              <Button data-testid="public-order-confirm-pay" onClick={confirmPayment} disabled={loading}>
                {loading ? 'Memeriksa…' : 'Saya sudah bayar'}
              </Button>
              <p style={{ fontSize: 12, color: 'var(--ink-3)', lineHeight: 1.5, margin: 0 }}>
                Scan QRIS di atas, bayar sesuai total, lalu tekan tombol ini. Penjual akan
                memverifikasi pembayaran sebelum memproses pesanan.
              </p>
            </>
          ) : (
            <Button data-testid="public-order-refresh" variant="secondary" onClick={refreshStatus} disabled={polling}>
              {polling ? 'Memperbarui…' : 'Perbarui status'}
            </Button>
          )}

          <Button data-testid="public-order-again" variant="text" onClick={backToMenu}>
            Pesan lagi di toko ini
          </Button>
        </div>
      )}

      {sheetOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Data pemesan"
          style={{ position: 'fixed', inset: 0, zIndex: 90, background: 'rgba(15,15,26,0.45)', display: 'grid', alignItems: 'end', justifyItems: 'center' }}
          onClick={(e) => { if (e.target === e.currentTarget) setSheetOpen(false); }}
        >
          <Card style={{ width: 'min(480px, 100%)', borderRadius: '24px 24px 0 0', display: 'grid', gap: 12 }}>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 17 }}>Data pemesan</div>
            <Input
              id="checkout-name"
              data-testid="checkout-name"
              label="Nama"
              value={custName}
              onChange={(e) => setCustName(e.target.value)}
              error={nameError}
              autoComplete="name"
            />
            <Input
              id="checkout-phone"
              data-testid="checkout-phone"
              label="No. HP (WhatsApp)"
              inputMode="tel"
              value={custPhone}
              onChange={(e) => setCustPhone(e.target.value)}
              error={phoneError}
              autoComplete="tel"
            />
            <Button onClick={createOrder} disabled={loading}>
              {loading ? 'Membuat pesanan…' : 'Buat pesanan & bayar'}
            </Button>
          </Card>
        </div>
      )}
    </div>
  );
}
