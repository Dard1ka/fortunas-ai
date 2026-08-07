# ADR 0001 — Kanal rilis: PWA Flutter web, native tidak dirilis

- **Status:** ⚫ **SUPERSEDED oleh [ADR-0002](0002-react-production-client.md) (2026-08-07) — tidak pernah diratifikasi (hanya pengusul yang menandatangani)**
- **Tanggal keputusan diambil:** 2026-08-06 · **Tanggal ADR ditulis:** 2026-08-07
- **Diusulkan oleh:** Go Steven Sanjaya
- **Perlu persetujuan:** Gregorius Darrel Andika Setya (ketua) · Filo Alvian Ongky · Michael Ivan Santoso

> **Kenapa ADR ini ada.** Keputusan di bawah sudah *dieksekusi* lewat PR #26 sebelum tim
> membahasnya. PR itu dibuat dan di-merge oleh orang yang sama, **nol review**, 15 menit
> setelah dibuka — proteksi branch `main` hanya mewajibkan CI hijau, tidak mewajibkan
> persetujuan manusia. Dokumen ini memaparkan keputusan itu apa adanya supaya tim bisa
> menyetujui, mengubah, atau membatalkannya **secara sadar**, bukan mewarisinya diam-diam.

---

## Konteks

Proposal hibah meng-*commit* dua hal yang ternyata tidak saling cocok dengan implementasi:

| Yang dijanjikan proposal | Yang dibangun |
|---|---|
| Luaran wajib #2: **"Prototype MVP web app"** | Aplikasi Flutter yang ditargetkan mobile native |
| Novelty #5: **"Web simulator chat WhatsApp-like"** | idem |
| Tech stack: **React 19 + Vite** | Flutter |
| Metrik: **SUS ≥ 75, n=30 UMKM** | butuh 30 pemilik warung meng-*sideload* APK |

Riwayat frontend berjalan bolak-balik:

```
React 19 + Vite PWA  →  Flutter native  →  Flutter web (PWA)
   (6 layar)            (22 layar)          (22 layar)
```

Langkah pertama tercatat di `mobile/MIGRATION.md` dengan alasan *"stack picks match the design
hand-off spec"* — yaitu artboard mockup, bukan kanal rilis. Langkah kedua adalah keputusan yang
sedang diratifikasi dokumen ini.

## Keputusan

Kanal rilis produk = **PWA yang dibangun dari Flutter web** (`flutter build web`), disajikan di
`app.fortunas.id`. Distribusi native (APK/iOS) **tidak dirilis**.

Turunannya yang sudah dieksekusi:
- `mobile/android/`, `mobile/ios/` **dihapus** (2026-08-07) — demo juri memakai PWA yang sudah
  ter-deploy, bukan APK sideload.
- `frontend/` (React) sempat **dihapus** lalu **dipulihkan** sebagai arsip/rujukan desain (Task
  1e, 2026-08-07, membatalkan sebagian keputusan ini) — lihat amandemen di bawah.
- Layar webview Midtrans Snap **dihapus** — `webview_flutter` nol dukungan web.
- `PhoneFrame` 430 px diganti `AdaptiveShell` tiga tier (compact / medium / expanded).

> **Amandemen (Task 1e, 2026-08-07):** menghapus `frontend/` dari repo ternyata melangkah
> terlalu jauh dan sudah dibatalkan. Kanal rilis (PWA Flutter web, native tidak dirilis) tetap
> berlaku persis seperti keputusan ADR ini — yang berubah cuma satu turunan di atas. Alasannya:
> React tetap secara arsitektur jalur yang lebih tepat untuk produk web-only (DOM asli, payload
> ~0,2 MB vs Flutter web yang terukur 3,28 MB, accessibility dan SEO jalan — lihat tabel "Biaya"
> di bawah) dan merupakan stack yang benar-benar di-*commit* proposal hibah (React 19 + Vite);
> menghapusnya menghapus bukti bahwa stack yang dijanjikan itu pernah dibangun. `frontend/`
> sekarang berstatus arsip/rujukan desain (`frontend/README.md`) — tidak dibangun, tidak dites,
> tidak di-gate CI, bukan klien yang di-ship. Migrasi kembali ke React sebagai klien yang
> di-ship **tetap terbuka sebagai pekerjaan pasca-hibah**, kalau tim suatu saat memutuskan
> keunggulan arsitektur itu sepadan dengan biaya menulis ulang dari 6 layar React ke paritas
> dengan 22 layar Flutter saat ini.

## Alternatif yang dipertimbangkan

**(a) Tetap rilis APK.** Ditolak: mengirim link ke 30 UMKM jauh lebih realistis daripada
menyuruh mereka sideload, dan proposal menjanjikan web app.

**(b) Kembali ke React/Vite (atau pindah ke Next.js).** Ditolak **karena waktu, bukan karena
kalah teknis** — lihat "Biaya" di bawah. React hanya pernah mencapai 6 layar; Flutter punya 22
layar, 227 test, checkout, loyalty, promo, katalog, pesan-publik, dan QRIS. Menulis ulang semua
itu, 20 hari dari tenggat, dengan 3 dev, menukar utang teknis terukur dengan risiko gagal kirim.

**(c) PWA di sub-path `/app`.** Ditolak: butuh `<base href>` dan aset gampang 404. Risiko naik,
untung nol.

**(d) Origin terpisah (PWA di CDN, API di VPS).** Ditolak: API tetap wajib domain+TLS, plus dua
sertifikat dan permukaan CORS yang bisa salah diam-diam. Manfaat CDN tidak sebanding untuk n=30.

## Biaya — diukur, bukan diperkirakan

| | Flutter web (terukur 2026-08-07) | React/Vite atau Next.js |
|---|---|---|
| Payload cold load | **3,28 MB gzip** (Chrome/Edge) · 3,94 MB (Firefox/Safari) | ~0,15–0,3 MB |
| Accessibility | **nol semantics** — CanvasKit merender seluruh app ke satu `<canvas>` | DOM asli, screen reader jalan |
| SEO | **nol** — canvas tidak bisa di-index | Next.js: SSR/SSG |
| Select teks, Ctrl+F browser | terbatas | normal |

Rincian payload: `main.dart.js` 0,93 MB · `canvaskit.wasm` 2,03 MB · font bundel 0,28 MB.
Metode: .NET `GZipStream` `CompressionLevel.Optimal` terhadap artefak `build/web`.

**Payload ±15× lebih berat** dari SPA setara. Untuk UMKM di 4G Indonesia itu biaya nyata — dan
itu sebabnya layar tunggu ber-brand harus ditambahkan ke `index.html`; SPA React tidak akan
pernah membutuhkannya.

**Tidak ada klaim jujur yang bisa mengatakan Flutter web unggul secara teknis di ranah web.**
Keputusan ini didorong oleh pekerjaan yang sudah terlanjur dibangun dan oleh tenggat — keduanya
alasan yang sah, tapi keduanya bukan keunggulan teknis.

## Konsekuensi

**Positif:** memenuhi luaran wajib #2 dan novelty #5 · SUS n=30 lewat link, bukan sideload ·
satu basis kode · voice `speech_to_text` sudah terintegrasi · boot offline setelah load pertama.

**Negatif:** payload 3,28 MB · nol accessibility semantics · nol SEO · **HTTPS naik jadi blocker
keras** (tanpa secure context, service worker, install prompt, **dan mikrofon** semuanya mati).

**Untuk paper:** deviasi kedua dari proposal setelah substitusi LLM. Sebaiknya ditulis sendiri
sebagai trade-off sadar — penguji yang membaca "PWA untuk UMKM" lalu mengukur 3,28 MB akan
bertanya. Dipetakan di `Fortunas/PROPOSAL_VS_REALITA.md`.

## Reversibilitas

| Kapan | Biaya membatalkan |
|---|---|
| **Sekarang** (branch `feat/ui-polish-pwa` belum di-merge) | **Murah.** `frontend/` sudah dipulihkan (Task 1e); sisa `git checkout 41d595f -- mobile/android mobile/ios` untuk membatalkan sisa keputusan ini |
| Setelah PR ini di-merge | Sedang — perlu revert lintas commit |
| Setelah deploy `app.fortunas.id` | Mahal — DNS, sertifikat, dan ekspektasi pengguna ikut terlibat |

**Inilah titik paling murah untuk mengubah arah.** Karena itu ADR ini diedarkan sekarang.

## Persetujuan

Beri centang + tanggal. Kalau **menolak atau ingin mengubah**, tulis alasannya di bawah — dan
`feat/ui-polish-pwa` jangan di-merge dulu.

- [ ] **Gregorius Darrel Andika Setya** (ketua) — tanggal:
- [ ] **Filo Alvian Ongky** — tanggal:
- [ ] **Michael Ivan Santoso** — tanggal:
- [x] **Go Steven Sanjaya** — 2026-08-06 (pengusul)

**Catatan/keberatan:**

---

## Rekomendasi proses (terpisah dari keputusan di atas)

Celah yang memungkinkan keputusan ini lolos tanpa review masih terbuka: proteksi branch `main`
mewajibkan status check CI, **tidak** mewajibkan approval. Dua PR terakhir (#25, #26) masuk `main`
dengan nol review.

Perbaikannya satu setelan (**butuh hak admin repo**): *Settings → Branches → `main` →
Require a pull request before merging* + *Require approvals: 1*.

> ⚠️ **Jangan sentuh daftar required status check di layar yang sama.** Nama job
> `Mobile (flutter analyze)` dicocokkan **harfiah**; pernah membuat PR macet berstatus `blocked`
> (bukan `dirty`), yang menyesatkan karena terlihat seperti "menunggu review".

**Status rekomendasi ini: DITUNDA atas permintaan Steven, 2026-08-07.** Bukan bagian dari
keputusan arsitektur; dicatat di sini supaya tidak hilang.
