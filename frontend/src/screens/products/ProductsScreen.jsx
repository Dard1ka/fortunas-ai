import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ScreenHeader from '../../ui/ScreenHeader.jsx';
import Pill from '../../ui/Pill.jsx';
import Icon from '../../ui/Icon.jsx';
import Button from '../../ui/Button.jsx';
import Card from '../../ui/Card.jsx';
import Input from '../../ui/Input.jsx';
import { api } from '../../api/client.js';
import { formatRupiah, parseIntOrNull } from '../../lib/format.js';
import ProductForm from './ProductForm.jsx';
import CategoryManager from './CategoryManager.jsx';

// Badge stok — 4 varian, ambang 5 = LOW_STOCK_THRESHOLD backend (product_repo).
function stockBadge(stock) {
  if (stock == null) return { label: 'Tak dilacak', bg: 'var(--surface-hover)' };
  if (stock === 0) return { label: 'Habis', bg: 'var(--peach-soft)' };
  if (stock <= 5) return { label: 'Menipis', bg: 'var(--peach)' };
  return { label: `Stok: ${stock}`, bg: 'var(--lime)' };
}

// Overlay dialog kecil (stok/harga/hapus) — pola overlay VoiceFlow, tanpa lib.
export function Dialog({ title, children, onClose }) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={title}
      style={{
        position: 'fixed', inset: 0, zIndex: 90, background: 'rgba(15,15,26,0.45)',
        display: 'grid', placeItems: 'center', padding: 18,
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose?.(); }}
    >
      <Card style={{ width: 'min(420px, 100%)', display: 'grid', gap: 12 }}>
        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 16 }}>{title}</div>
        {children}
      </Card>
    </div>
  );
}

function StockDialog({ product, onClose, onSaved }) {
  const [value, setValue] = useState(product.stock == null ? '' : String(product.stock));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const save = async () => {
    setBusy(true); setError(null);
    try {
      await api.setStock(product.id, parseIntOrNull(value));
      onSaved();
    } catch (err) {
      setError(err.message || 'Gagal menyimpan stok.');
      setBusy(false);
    }
  };
  return (
    <Dialog title={`Stok ${product.name}`} onClose={onClose}>
      <Input
        id="edit-stock-field"
        data-testid="edit-stock-field"
        label="Stok"
        inputMode="numeric"
        hint="Kosongkan bila stok tidak dilacak."
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
      {error && <div role="alert" style={{ fontSize: 12, color: 'var(--error)' }}>{error}</div>}
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
        <Button variant="text" onClick={onClose}>Batal</Button>
        <Button data-testid="edit-stock-save" onClick={save} disabled={busy}>
          {busy ? 'Menyimpan…' : 'Simpan'}
        </Button>
      </div>
    </Dialog>
  );
}

function PriceDialog({ product, onClose, onSaved }) {
  const [value, setValue] = useState(product.price == null ? '' : String(product.price));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const save = async () => {
    setBusy(true); setError(null);
    try {
      await api.setPrice(product.id, parseIntOrNull(value));
      onSaved();
    } catch (err) {
      setError(err.message || 'Gagal menyimpan harga.');
      setBusy(false);
    }
  };
  return (
    <Dialog title={`Harga ${product.name}`} onClose={onClose}>
      <Input
        id="edit-price-field"
        data-testid="edit-price-field"
        label="Harga (Rp)"
        inputMode="numeric"
        hint="Kosongkan bila harga belum diset."
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
      {error && <div role="alert" style={{ fontSize: 12, color: 'var(--error)' }}>{error}</div>}
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
        <Button variant="text" onClick={onClose}>Batal</Button>
        <Button data-testid="edit-price-save" onClick={save} disabled={busy}>
          {busy ? 'Menyimpan…' : 'Simpan'}
        </Button>
      </div>
    </Dialog>
  );
}

function ProductTile({ product, categoryName, onEditStock, onEditPrice, onDelete }) {
  const [imgBroken, setImgBroken] = useState(false);
  const badge = stockBadge(product.stock);
  return (
    <Card style={{ display: 'flex', gap: 12, padding: 14, alignItems: 'flex-start' }}>
      {imgBroken || !product.image_url ? (
        <div style={{ width: 56, height: 56, borderRadius: 12, background: 'var(--surface-soft)', border: '1.5px solid var(--border-soft)', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="close" size={18} stroke="var(--ink-4)" />
        </div>
      ) : (
        <img
          src={product.image_url}
          alt={product.name}
          onError={() => setImgBroken(true)}
          style={{ width: 56, height: 56, borderRadius: 12, objectFit: 'cover', border: '1.5px solid var(--border-soft)', flexShrink: 0 }}
        />
      )}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 14 }}>{product.name}</span>
          <Pill bg="var(--surface-soft)" sm mono>{(product.stock_code || '').toUpperCase()}</Pill>
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 6 }}>
          <Pill bg={badge.bg} sm>{badge.label}</Pill>
          {product.price == null
            ? <Pill bg="var(--peach-soft)" sm>Harga belum diset</Pill>
            : <Pill bg="var(--lime-deep)" sm>{formatRupiah(product.price)}</Pill>}
          <Pill bg="var(--surface-hover)" sm>{categoryName || 'Tanpa kategori'}</Pill>
        </div>
        {product.description ? (
          <div style={{ fontSize: 12, color: 'var(--ink-3)', marginTop: 6, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
            {product.description}
          </div>
        ) : null}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        <button type="button" data-testid={`product-edit-price-${product.id}`} aria-label={`Ubah harga ${product.name}`} onClick={onEditPrice} style={iconBtn}>
          <Icon name="coin" size={15} />
        </button>
        <button type="button" data-testid={`product-edit-stock-${product.id}`} aria-label={`Ubah stok ${product.name}`} onClick={onEditStock} style={iconBtn}>
          <Icon name="chart" size={15} />
        </button>
        <button type="button" data-testid={`product-delete-${product.id}`} aria-label={`Hapus ${product.name}`} onClick={onDelete} style={iconBtn}>
          <Icon name="trash" size={15} stroke="var(--error)" />
        </button>
      </div>
    </Card>
  );
}

const iconBtn = {
  width: 34, height: 34, borderRadius: 10, background: 'var(--surface)',
  border: '1.5px solid var(--border)', display: 'grid', placeItems: 'center', cursor: 'pointer',
};

export default function ProductsScreen() {
  const navigate = useNavigate();
  const [products, setProducts] = useState(null);
  const [categories, setCategories] = useState([]);
  const [needsOnboarding, setNeedsOnboarding] = useState(false);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);
  const [busyAuto, setBusyAuto] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [showCategories, setShowCategories] = useState(false);
  const [stockFor, setStockFor] = useState(null);
  const [priceFor, setPriceFor] = useState(null);
  const [deleteFor, setDeleteFor] = useState(null);

  // Muat produk + kategori BERSAMAAN — chip kategori di kartu di-resolve dari
  // daftar kategori; fetch terpisah membuat chip "Tanpa kategori" berkedip.
  const load = useCallback(async () => {
    setError(null);
    try {
      const [p, c] = await Promise.all([api.listProducts(), api.listCategories()]);
      setProducts(p.products || []);
      setNeedsOnboarding(Boolean(p.needs_onboarding));
      setCategories(c.categories || []);
    } catch (err) {
      setError(err.message || 'Gagal memuat produk.');
      if (products == null) setProducts([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => { load(); }, [load]);

  const catName = (id) => categories.find((c) => c.id === id)?.name || null;
  const uncategorized = (products || []).filter((p) => p.category_id == null).length;

  const runAutoCategorize = async () => {
    setBusyAuto(true);
    setNotice(null);
    try {
      const r = await api.autoCategorize();
      const n = r?.categorized ?? 0;
      setNotice(n === 0
        ? 'Semua produk sudah punya kategori.'
        : `AI mengelompokkan ${n} produk. Kamu tetap bisa mengubahnya.`);
      await load(); // AI bisa membuat kategori baru → produk & kategori di-reload
    } catch {
      setNotice('Gagal menjalankan auto-kategori. Coba lagi.');
    } finally {
      setBusyAuto(false);
    }
  };

  const removeProduct = async (p) => {
    setDeleteFor(null);
    setNotice(null);
    try {
      await api.deleteProduct(p.id);
      await load();
    } catch (err) {
      setError(err.message || 'Gagal menghapus produk.');
    }
  };

  return (
    <div style={{ minHeight: '100%' }}>
      <ScreenHeader subtitle="Kelola Produk" />

      <div style={{ padding: '4px 18px 8px', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 22, letterSpacing: '-0.02em', margin: '0 0 4px' }}>
            Produk Saya
          </h2>
          <p style={{ color: 'var(--ink-3)', fontSize: 12.5, margin: 0 }}>
            Kode barang dibuat otomatis dari 2 huruf awal nama.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button variant="text" data-testid="products-back" onClick={() => navigate('/me')}>Kembali</Button>
          <Button variant="secondary" data-testid="products-manage-categories" onClick={() => setShowCategories(true)}>
            Kategori
          </Button>
        </div>
      </div>

      <div style={{ padding: '0 18px 90px', display: 'grid', gap: 10 }}>
        {notice && (
          <div role="status" style={{ padding: '10px 14px', background: 'var(--lime)', border: '1.5px solid var(--ink)', borderRadius: 12, fontSize: 12.5 }}>
            {notice}
          </div>
        )}
        {error && (
          <div role="alert" style={{ padding: '10px 14px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 12, fontSize: 12.5 }}>
            {error}
          </div>
        )}

        {needsOnboarding && products != null && (
          <div style={{ padding: '12px 14px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 12, fontSize: 12.5 }}>
            Kamu wajib menambahkan minimal 1 produk sebelum mulai berjualan.
          </div>
        )}

        {!needsOnboarding && uncategorized > 0 && (
          <div data-testid="auto-categorize-banner" style={{ padding: '12px 14px', background: 'var(--sky)', border: '1.5px solid var(--ink)', borderRadius: 12, display: 'grid', gap: 8 }}>
            <div style={{ fontSize: 12.5, fontWeight: 700 }}>{uncategorized} produk belum berkategori</div>
            <div style={{ fontSize: 12, color: 'var(--ink-2)' }}>
              Biarkan AI mengelompokkan produkmu supaya menu pelanggan lebih rapi.
            </div>
            <Button variant="secondary" onClick={runAutoCategorize} disabled={busyAuto} style={{ justifySelf: 'start' }}>
              {busyAuto ? 'Mengelompokkan…' : 'Kelompokkan dengan AI'}
            </Button>
          </div>
        )}

        {products == null && <div style={{ textAlign: 'center', padding: 32, color: 'var(--ink-3)', fontSize: 13 }}>Memuat…</div>}

        {products != null && !needsOnboarding && products.length === 0 && !error && (
          <div style={{ textAlign: 'center', padding: 32, color: 'var(--ink-3)', fontSize: 13 }}>Belum ada produk.</div>
        )}

        {(products || []).map((p) => (
          <ProductTile
            key={p.id}
            product={p}
            categoryName={catName(p.category_id)}
            onEditStock={() => setStockFor(p)}
            onEditPrice={() => setPriceFor(p)}
            onDelete={() => setDeleteFor(p)}
          />
        ))}

        <Button data-testid="product-add-fab" onClick={() => { setNotice(null); setShowForm(true); }} style={{ position: 'sticky', bottom: 16 }}>
          + Tambah Produk
        </Button>
      </div>

      {showForm && (
        <ProductForm
          categories={categories}
          onClose={() => setShowForm(false)}
          onSaved={async () => {
            setShowForm(false);
            setNotice('Produk berhasil ditambahkan.');
            await load();
          }}
        />
      )}

      {showCategories && (
        <CategoryManager
          categories={categories}
          products={products || []}
          onChanged={load}
          onClose={() => setShowCategories(false)}
        />
      )}

      {stockFor && (
        <StockDialog
          product={stockFor}
          onClose={() => setStockFor(null)}
          onSaved={async () => { setStockFor(null); await load(); }}
        />
      )}
      {priceFor && (
        <PriceDialog
          product={priceFor}
          onClose={() => setPriceFor(null)}
          onSaved={async () => { setPriceFor(null); await load(); }}
        />
      )}
      {deleteFor && (
        <Dialog title={`Hapus produk ${deleteFor.name}?`} onClose={() => setDeleteFor(null)}>
          <div style={{ fontSize: 12.5, color: 'var(--ink-2)' }}>
            Produk dihapus dari katalog. Tindakan ini tidak bisa dibatalkan.
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <Button variant="text" onClick={() => setDeleteFor(null)}>Batal</Button>
            <Button onClick={() => removeProduct(deleteFor)} style={{ background: 'var(--error)' }}>Hapus</Button>
          </div>
        </Dialog>
      )}
    </div>
  );
}
