# Halaman Uji Domain & Hosting

`index.html` — satu file statis untuk memverifikasi rantai deploy **sebelum**
build PWA di-upload. Nol dependency, nol request eksternal, semua path relatif.

## Kenapa ada

Build React (Vite) terdiri dari banyak file (index.html + aset ber-hash +
service worker). Kalau ia gagal tampil di domain baru, penyebabnya ambigu: DNS
belum mengarah, docroot salah, sertifikat belum diterbitkan, atau build-nya
sendiri rusak. Halaman ini menjawab bagian "domain/hosting" lebih dulu, jadi
kegagalan berikutnya pasti soal build.

## Yang diperiksa

| Cek | Menjawab pertanyaan |
|---|---|
| Identitas host | Aku sedang melihat domain sungguhan, atau cPanel temporary URL? |
| HTTPS & secure context | Service worker, install PWA, dan **mikrofon** diizinkan browser? |
| Service Worker | PWA bisa dipasang? |
| Mikrofon | Fitur voice bisa jalan? (dibaca tanpa memicu prompt izin) |
| Server & protokol | Apache (shared hosting) atau nginx (VPS)? Jam server sinkron? |
| Backend `/api/health` | Proxy `/api/` → FastAPI hidup? |

Tombol **Salin laporan** menghasilkan ringkasan teks untuk ditempel ke grup tim.

## Cara pasang

### A. cPanel shared hosting (Biznet NEO)

1. cPanel → **File Manager** → masuk ke `public_html`.
2. **Upload** `index.html`.
3. Buka lewat salah satu URL:
   - temporary URL: `http://<server>/~<user>/` — melewati DNS, bisa dipakai
     walau domain belum aktif;
   - domain, setelah DNS-nya mengarah ke IP hosting.

Efek samping yang diinginkan: `public_html` yang kosong menampilkan
**directory listing** (`Index of /`) dan membocorkan isi folder. Begitu
`index.html` ada, Apache menyajikannya lebih dulu dan listing itu berhenti.

### B. VPS nginx

Taruh di `root /var/www/fortunas` (lihat `../nginx-fortunas.conf`):

```bash
sudo install -m 644 index.html /var/www/fortunas/index.html
```

`location = /index.html` sudah ber-`Cache-Control: no-cache`, jadi build asli
menimpanya tanpa menyisakan cache basi di perangkat UMKM.

## Setelah semua hijau

```bash
cd frontend
npm ci && npm run build
# cek: grep -R "fonts.googleapis" dist/  → harus kosong
# upload isi frontend/dist/ ke docroot — menimpa index.html ini
```

Backend FastAPI **tidak** bisa berjalan di shared hosting (Apache cPanel tidak
mem-proxy `/api/`). Pola produksi yang dipakai: PWA statis + backend di VPS yang
sama, satu origin `app.fortunas.id` (nginx menyajikan `/` dan mem-proxy `/api/`
— lihat `../nginx-fortunas.conf` dan `../DEPLOY.md`).

## Aturan saat mengedit file ini

1. **Path relatif saja.** Di temporary URL `/~user/`, path absolut menunjuk ke
   docroot server dan akan 404 walau file-nya ada.
2. **Tanpa request eksternal.** Alat diagnosa tidak boleh punya dependensi yang
   bisa gagal sendiri; CDN yang down akan terlihat seperti hosting yang down.
