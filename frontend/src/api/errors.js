// Centralized user-facing error messages — Bahasa Indonesia.
// Extracted from legacy App.jsx so all screens speak the same vocabulary.

export function humanizeError(err, status) {
  if (err?.name === 'AbortError') return null;
  if (status >= 500) return 'Server sedang bermasalah. Coba lagi sebentar lagi.';
  if (status === 429) return 'Terlalu banyak permintaan. Tunggu beberapa detik, lalu coba lagi.';
  if (status === 408 || status === 504) {
    return 'Permintaan memakan waktu terlalu lama. Coba sederhanakan pertanyaan.';
  }
  if (status === 404) return 'Endpoint tidak ditemukan. Pastikan backend berjalan.';
  if (status >= 400) return 'Permintaan tidak dapat diproses. Periksa kembali pertanyaan Anda.';

  const msg = err?.message || '';
  if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
    return 'Tidak dapat terhubung ke server. Periksa koneksi atau pastikan backend menyala.';
  }
  return msg || 'Terjadi kesalahan yang tidak terduga.';
}
