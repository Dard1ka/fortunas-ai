# Day 27 — Rebrand Logo (aset saja, tema UI tidak disentuh)

**Tanggal:** 2026-08-09 · **Branch:** `chore/rebrand-logo` · **Arahan Steven:** *"pokoknya mirip persis logonya aja, ui theme gitu masih sama aja"*

## Ringkasan

Seluruh permukaan produksi kini memakai **satu mark navy yang sama** (`#0D47A1`), menggantikan dua mark lama yang berbeda: huruf "F" emas serif (favicon/ikon PWA) dan huruf "F" lime miring buatan CSS (di dalam app). Tema UI **tidak berubah** — violet `#6D5EF7`, lime, dan latar krem tetap; `pwa-branding.test.js` lolos tanpa diubah.

## Satu sumber, delapan aset

Sumber kebenaran: `assets/brand/logo-mark-source.png` (1280×1280, transparan). Semua ikon diturunkan darinya oleh `scripts/gen_brand_assets.py` (Pillow, dijalankan manual — **bukan** bagian build/CI; hasilnya di-commit):

| Berkas | Ukuran | Bentuk | Dipakai |
|---|---|---|---|
| `logo-mark.png` | 512 | transparan, padding 6% | `BrandMark.jsx` (4 layar) |
| `favicon-16.png` / `favicon-32.png` | 16 / 32 | tile putih membulat | `index.html` |
| `favicon.ico` | 16/32/48 | tile putih membulat | permintaan default `/favicon.ico` |
| `apple-touch-icon.png` | 180 | tile putih **persegi penuh** | iOS home screen |
| `icon-192.png` / `icon-512.png` | 192 / 512 | tile putih membulat | manifest `any` |
| `icon-512-maskable.png` | 512 | tile putih **persegi penuh**, safe zone 80% | manifest `maskable` |

Regenerasi: ganti berkas sumber lalu `python scripts/gen_brand_assets.py`.

## Keputusan sadar

1. **PNG, bukan SVG.** Sumbernya raster dan tidak ada vectorizer di lingkungan kerja; menyisipkan PNG base64 ke `.svg` hanya membengkakkan favicon.
2. **Warna logo tidak dibalik** — tetap navy di atas terang, supaya "mirip persis".
3. **Proporsi asli 0,77:1 dipertahankan** — ikon persegi diberi padding, tidak digepengkan.
4. **apple-touch & maskable persegi penuh** (temuan QA visual): iOS memangkas jadi squircle dan Android jadi lingkaran. Kalau sudutnya sudah kita bulatkan duluan, sisa sudut transparan muncul sebagai sliver hitam di iOS. Diverifikasi: alpha keempat sudut = 255.
5. **Ikon 16 px dibiarkan menggumpal.** Garis putih di dalam mark memang menutup di bawah ~24 px. Menebalkannya berarti logonya jadi berbeda — melanggar "mirip persis". Siluet berliannya tetap dikenali.
6. **`logo.svg` (lockup bertulisan) DIHAPUS**, bukan diperbaiki: nol referensi di seluruh repo, dan teksnya memang rusak — "AI" dipaku di `x=742` sehingga menabrak "Fortunas" begitu metrik Georgia berbeda. Kalau nanti butuh lockup untuk slide/paper, itu pekerjaan terpisah dengan keputusan tipografi merek.
7. **`BrandMark.jsx` kehilangan rotasi −4° dan pop-shadow-nya** — konsekuensi yang disepakati agar logo di dalam app identik dengan ikon sistem.

## Bug lama yang ikut diperbaiki

`manifest.webmanifest` menuliskan `"sizes": "256x256"` untuk `logo-mark-256.png` yang aslinya **1254×1254**. Sekarang tiap entri cocok dengan dimensi berkasnya, dan `brand-assets.test.js` membaca dimensi langsung dari header IHDR PNG supaya kesalahan itu tidak bisa terulang tanpa ketahuan.

## Verifikasi

```
npm run lint  → 0 masalah
npm test      → Test Files 24 passed (24) · Tests 146 passed (146)   [140 → 146]
npm run build → ✓ built · precache 25 entries (712,64 KiB)           [sebelumnya 916 KiB]
```

Test baru: 5 di `brand-assets.test.js` (referensi emas hilang, ikon manifest ada berkasnya, `sizes` cocok dimensi asli, tepat satu maskable, logo app ada) + 1 di `components.test.jsx` (BrandMark merender `<img>`, bukan huruf "F").

## Deploy

Prosedur normal (`deploy/DEPLOY.md`): build → kosongkan `/var/www/fortunas` → unggah `dist/` → **salin ulang `payments/qris-statis.png`** (di luar git) → verifikasi `curl` tiap ikon 200.

**Catatan cache — bukan kegagalan deploy:** favicon di-cache sangat agresif browser dan service worker menyimpan ikon di precache, jadi pengunjung lama mungkin masih melihat logo emas sampai hard-reload (Ctrl+Shift+R) atau sampai SW versi baru aktif. Ikon PWA yang **sudah terpasang** di home screen HP ditulis saat install — perlu uninstall & install ulang untuk melihat logo baru.
