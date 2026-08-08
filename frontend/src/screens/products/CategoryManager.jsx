import { useState } from 'react';
import Button from '../../ui/Button.jsx';
import Card from '../../ui/Card.jsx';
import Input from '../../ui/Input.jsx';
import Icon from '../../ui/Icon.jsx';
import { api } from '../../api/client.js';

// Kelola kategori (paritas _CategorySheet Flutter).
// Hapus kategori TIDAK menghapus produk — produk jadi tanpa kategori; jumlah
// produk terdampak dihitung di klien dari daftar produk (paritas).
export default function CategoryManager({ categories, products, onChanged, onClose }) {
  const [name, setName] = useState('');
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [confirmFor, setConfirmFor] = useState(null);

  const add = async () => {
    const trimmed = name.trim();
    if (!trimmed) return; // paritas: kosong = diam, tanpa pesan & tanpa request
    setBusy(true); setError(null);
    try {
      await api.createCategory(trimmed);
      setName('');
      await onChanged();
    } catch (err) {
      setError(err.message || 'Gagal menambah kategori.'); // 409 duplikat tampil apa adanya
    } finally {
      setBusy(false);
    }
  };

  const remove = async (c) => {
    setConfirmFor(null);
    setBusy(true); setError(null);
    try {
      await api.deleteCategory(c.id);
      await onChanged(); // reload kategori + produk agar chip di kartu ikut hilang
    } catch (err) {
      setError(err.message || 'Gagal menghapus kategori.');
    } finally {
      setBusy(false);
    }
  };

  const affectedCount = (c) => products.filter((p) => p.category_id === c.id).length;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Kelola Kategori"
      style={{
        position: 'fixed', inset: 0, zIndex: 90, background: 'rgba(15,15,26,0.45)',
        display: 'grid', alignItems: 'end', justifyItems: 'center',
      }}
      onClick={(e) => { if (e.target === e.currentTarget && !confirmFor) onClose?.(); }}
    >
      <Card style={{ width: 'min(480px, 100%)', maxHeight: '80dvh', overflowY: 'auto', borderRadius: '24px 24px 0 0', display: 'grid', gap: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 17 }}>Kelola Kategori</div>
          <Button variant="text" onClick={onClose}>Tutup</Button>
        </div>
        <p style={{ fontSize: 12, color: 'var(--ink-3)', margin: 0 }}>
          Hapus kategori tidak menghapus produknya — produk jadi tanpa kategori.
        </p>

        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <Input
              id="category-add-field"
              label="Nama kategori baru"
              maxLength={60}
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <Button variant="secondary" onClick={add} disabled={busy}>Tambah</Button>
        </div>

        {error && (
          <div role="alert" style={{ padding: '10px 12px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 10, fontSize: 12.5 }}>
            {error}
          </div>
        )}

        <div style={{ display: 'grid', gap: 8 }}>
          {categories.length === 0 && (
            <div style={{ fontSize: 12.5, color: 'var(--ink-3)', textAlign: 'center', padding: 12 }}>Belum ada kategori.</div>
          )}
          {categories.map((c) => (
            <div key={c.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, padding: '10px 12px', border: '1.5px solid var(--border-soft)', borderRadius: 12 }}>
              <span style={{ fontSize: 13.5, fontWeight: 600 }}>{c.name}</span>
              <button
                type="button"
                data-testid={`category-delete-${c.id}`}
                aria-label={`Hapus kategori ${c.name}`}
                onClick={() => setConfirmFor(c)}
                style={{ width: 32, height: 32, borderRadius: 9, background: 'var(--surface)', border: '1.5px solid var(--border)', display: 'grid', placeItems: 'center', cursor: 'pointer' }}
              >
                <Icon name="trash" size={14} stroke="var(--error)" />
              </button>
            </div>
          ))}
        </div>

        {confirmFor && (
          <div style={{ padding: '12px 14px', background: 'var(--peach-soft)', border: '1.5px solid var(--ink)', borderRadius: 12, display: 'grid', gap: 8 }}>
            <div style={{ fontWeight: 700, fontSize: 13.5 }}>Hapus kategori {confirmFor.name}?</div>
            <div style={{ fontSize: 12.5 }}>
              {affectedCount(confirmFor) === 0
                ? 'Tidak ada produk di kategori ini.'
                : `${affectedCount(confirmFor)} produk akan jadi tanpa kategori.`}
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <Button variant="text" onClick={() => setConfirmFor(null)}>Batal</Button>
              <Button data-testid="category-delete-confirm" onClick={() => remove(confirmFor)} disabled={busy} style={{ background: 'var(--error)' }}>
                Hapus
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
