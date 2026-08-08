// Helper format bersama layar Wave C (spec4 §3 keputusan #6-#7).

// Konvensi Rupiah React existing: 'Rp ' + pemisah ribuan id-ID, tanpa desimal.
export const formatRupiah = (n) =>
  'Rp ' + new Intl.NumberFormat('id-ID').format(Number(n) || 0);

// Tri-state: kosong/non-angka = null (stok tak dilacak / harga belum diset /
// tanpa kategori) — JANGAN pernah jatuh ke 0. Padanan int.tryParse Dart.
export function parseIntOrNull(s) {
  const t = String(s ?? '').trim();
  if (!t) return null;
  const n = Number.parseInt(t, 10);
  return Number.isNaN(n) ? null : n;
}
