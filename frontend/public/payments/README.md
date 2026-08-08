# Aset pembayaran (TIDAK di-commit)

Halaman `/order` menampilkan `/payments/qris-statis.png` saat pesanan berstatus
`pending_payment`.

**File QR TIDAK pernah di-commit ke repo ini** — QRIS berisi identitas
pembayaran nyata (nama pemilik, merchant ID, NMID) dan repo ini publik. Pola
sama dengan `mobile/assets/payments/` lama: folder di-track, file dipasang
manual.

## Pasang di server (produksi)

Salin file QR ke docroot hasil build:

```bash
scp qris-statis.png deploy@VPS:/var/www/fortunas/payments/qris-statis.png
```

(Direktori `payments/` ikut ter-deploy dari `frontend/public/`; hanya PNG-nya
yang diisi manual. Redeploy `dist/` menimpa folder — salin ulang setelah
deploy, atau tambahkan langkah ini ke skrip deploy.)

## Dev lokal

Letakkan PNG apa pun di `frontend/public/payments/qris-statis.png` (gitignored).
Tanpa file, UI menampilkan fallback: "Kode QRIS belum tersedia." — bukan error.
