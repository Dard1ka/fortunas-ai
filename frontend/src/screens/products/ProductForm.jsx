import { useEffect, useRef, useState } from 'react';
import Button from '../../ui/Button.jsx';
import Card from '../../ui/Card.jsx';
import Input from '../../ui/Input.jsx';
import Icon from '../../ui/Icon.jsx';
import { api } from '../../api/client.js';
import { parseIntOrNull } from '../../lib/format.js';

// Form tambah produk (paritas _ProductFormSheet Flutter).
// Urutan validasi: nama dulu, baru gambar. Gambar WAJIB (backend juga menolak).
// stock/price/category_id HANYA dikirim bila non-null — tri-state, bukan 0/''.
export default function ProductForm({ categories, onClose, onSaved }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [stock, setStock] = useState('');
  const [price, setPrice] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [localError, setLocalError] = useState(null);
  const [serverError, setServerError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const previewRef = useRef('');

  useEffect(() => () => {
    // Bersihkan object URL preview saat unmount.
    if (previewRef.current) {
      try { URL.revokeObjectURL(previewRef.current); } catch { /* ignore */ }
    }
  }, []);

  const pickImage = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    if (previewRef.current) {
      try { URL.revokeObjectURL(previewRef.current); } catch { /* ignore */ }
    }
    try {
      const url = URL.createObjectURL(f);
      previewRef.current = url;
      setPreview(url);
    } catch {
      setPreview('');
    }
  };

  const submit = async () => {
    setLocalError(null);
    setServerError(null);
    if (!name.trim()) { setLocalError('Nama produk wajib diisi.'); return; }
    if (!file) { setLocalError('Gambar produk wajib dipilih.'); return; }

    const fd = new FormData();
    fd.append('name', name.trim());
    fd.append('description', description);
    fd.append('image', file, file.name || 'produk.jpg');
    const stockVal = parseIntOrNull(stock);
    if (stockVal != null) fd.append('stock', String(stockVal));
    const priceVal = parseIntOrNull(price);
    if (priceVal != null) fd.append('price', String(priceVal));
    const catVal = parseIntOrNull(categoryId);
    if (catVal != null) fd.append('category_id', String(catVal));

    setSubmitting(true);
    try {
      await api.createProduct(fd);
      onSaved();
    } catch (err) {
      setServerError(err.message || 'Gagal menyimpan produk.');
      setSubmitting(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Tambah Produk"
      style={{
        position: 'fixed', inset: 0, zIndex: 90, background: 'rgba(15,15,26,0.45)',
        display: 'grid', alignItems: 'end', justifyItems: 'center',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose?.(); }}
    >
      <Card style={{ width: 'min(480px, 100%)', maxHeight: '88dvh', overflowY: 'auto', borderRadius: '24px 24px 0 0', display: 'grid', gap: 12 }}>
        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 17 }}>Tambah Produk</div>
        <p style={{ fontSize: 12, color: 'var(--ink-3)', margin: 0 }}>
          Kode barang dibuat otomatis dari 2 huruf awal nama.
        </p>

        <Input
          id="product-name"
          label="Nama produk *"
          maxLength={80}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        <div style={{ display: 'grid', gap: 6 }}>
          <label htmlFor="product-desc" style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink-3)' }}>Deskripsi</label>
          <textarea
            id="product-desc"
            maxLength={1000}
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            style={{
              fontFamily: 'var(--font-body)', fontSize: 14, color: 'var(--ink)',
              background: 'var(--surface)', padding: 14,
              border: '1.5px solid var(--border)', borderRadius: 'var(--radius-md)',
              outline: 'none', width: '100%', boxSizing: 'border-box', resize: 'vertical',
            }}
          />
          <span style={{ fontSize: 11, color: 'var(--ink-4)', justifySelf: 'end' }}>{description.length}/1000</span>
        </div>

        <Input
          id="product-stock"
          label="Stok (opsional)"
          inputMode="numeric"
          hint="Kosongkan bila stok tidak dilacak."
          value={stock}
          onChange={(e) => setStock(e.target.value)}
        />
        <Input
          id="product-price"
          label="Harga Rp (opsional)"
          inputMode="numeric"
          hint="Wajib bila mau terima pesanan online."
          value={price}
          onChange={(e) => setPrice(e.target.value)}
        />

        <div style={{ display: 'grid', gap: 6 }}>
          <label htmlFor="product-category" style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink-3)' }}>Kategori</label>
          <select
            id="product-category"
            data-testid="product-category-dropdown"
            value={categoryId}
            onChange={(e) => setCategoryId(e.target.value)}
            style={{
              fontFamily: 'var(--font-body)', fontSize: 14, color: 'var(--ink)',
              background: 'var(--surface)', padding: 14,
              border: '1.5px solid var(--border)', borderRadius: 'var(--radius-md)',
              width: '100%', boxSizing: 'border-box',
            }}
          >
            <option value="">Tanpa kategori</option>
            {categories.map((c) => (
              <option key={c.id} value={String(c.id)}>{c.name}</option>
            ))}
          </select>
        </div>

        <div style={{ display: 'grid', gap: 6 }}>
          <label htmlFor="product-image" style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink-3)' }}>Gambar produk *</label>
          <label
            htmlFor="product-image"
            style={{
              width: 120, height: 120, borderRadius: 14, cursor: 'pointer',
              border: '1.5px dashed var(--border)', background: 'var(--surface-soft)',
              display: 'grid', placeItems: 'center', overflow: 'hidden',
            }}
          >
            {preview
              ? <img src={preview} alt="Preview produk" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              : <Icon name="upload" size={22} stroke="var(--ink-4)" />}
          </label>
          <input
            id="product-image"
            data-testid="product-pick-image"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={pickImage}
            style={{ display: 'none' }}
          />
          <span style={{ fontSize: 11, color: 'var(--ink-4)' }}>JPG/PNG/WebP, maksimal 5 MB.</span>
        </div>

        {(localError || serverError) && (
          <div role="alert" style={{ padding: '10px 12px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 10, fontSize: 12.5 }}>
            {localError || serverError}
          </div>
        )}

        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <Button variant="text" onClick={onClose}>Batal</Button>
          <Button data-testid="product-submit" onClick={submit} disabled={submitting}>
            {submitting ? 'Menyimpan…' : 'SIMPAN PRODUK'}
          </Button>
        </div>
      </Card>
    </div>
  );
}
