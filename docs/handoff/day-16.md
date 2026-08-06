# Handoff Day 16 — PWA-only + Responsive Shell (Task 1–12)

**Dev slice ini:** Go Steven Sanjaya (rotasi via agen, estafet Task 1–11; Task 12 = handoff)
**Tanggal:** 2026-08-06
**Branch:** `feat/pwa-responsive-shell` (dari `main` @ `135253b`) — 17 commit fitur (HEAD `04f99e4`)
**PR:** belum dibuka — push, rebase, dan `gh pr create` **sengaja tidak dilakukan** di Task 12.
Developer lain sedang mengedit `mobile/lib/app.dart` secara paralel dan **belum push**, jadi
`origin/main` masih di `135253b` — tidak ada apa pun untuk di-rebase ke atasnya. Keputusan
push/PR dipegang controller/tim, di luar scope task ini.

---

## Apa yang berubah

- **`PhoneFrame` kini delegasi ke `AdaptiveShell`** (`mobile/lib/app.dart`, `mobile/lib/ui/adaptive_shell.dart`).
  Nama dan lokasi pemanggilan `PhoneFrame` dipertahankan persis — setiap route yang membungkusnya
  otomatis mendapat perilaku responsif tanpa developer route itu perlu tahu apa pun soal shell.
- **Nav rail menggantikan bottom nav di viewport ≥600px** untuk tab UMKM (`ShellRoute` di
  `app.dart:119-166`, widget `FortunasNavRail` di `mobile/lib/ui/nav_rail.dart`). Compact (<600)
  tetap `FortunasBottomNav` seperti sebelumnya; medium (600–1023) pakai rail ikon-saja lebar 76;
  expanded (≥1024) pakai rail extended lebar 200 + konten dibatasi 840px.
- **PWA jadi kanal rilis.** `manifest.json` dan `index.html` berisi identitas produk asli
  (nama, deskripsi, `lang="id"`, warna tema) — bukan lagi boilerplate `flutter create`.
- **Base URL same-origin `/api`** di web (`mobile/lib/api/client.dart`) — build web tidak lagi
  menembak `http://127.0.0.1:8000` langsung; ia mengasumsikan nginx reverse-proxy di depan.
- **Token store untuk web** — `flutter_secure_storage` (native-only, gagal di browser) diganti
  jalur `localStorage` untuk platform web; native (Android/iOS) tetap `flutter_secure_storage`.
- **nginx + runbook HTTPS** (`deploy/nginx-fortunas.conf`, `deploy/DEPLOY.md`) — same-origin
  proxy `/api/` (strip prefix) dan `/media/` (tidak strip), cache header no-cache untuk
  `flutter_service_worker.js`/`manifest.json`/`index.html`, `listen 443 ssl http2;`, langkah
  certbot lengkap.
- **CI menggerbang `flutter build web`** — job mobile di `.github/workflows/ci.yml` sekarang
  `flutter pub get` → `flutter analyze --no-fatal-infos` → `flutter test` → `flutter build web --release`,
  semua dengan `working-directory: mobile`. Job backend (ruff + pytest, deps minimal
  tanpa torch/chromadb) byte-identik, tidak tersentuh.
- **Font Inter disubset ke Latin** — lihat §Payload di bawah.

---

## Apa yang SENGAJA TIDAK berubah, dan kenapa

- **Isi 13 layar UMKM** (home, briefing, result, history, profile, checkout, products, orders,
  scan, dpa, login, register, splash) — logika internalnya tidak disentuh. Hanya *bungkusnya*
  (`PhoneFrame`/`ShellRoute`) yang berubah.
- **9 layar `customer_*`** dan **`CustomerBottomNav`** — shell customer (`ShellRoute` di
  `app.dart:209-228`) tetap `PhoneFrame` membungkus `Scaffold` + `CustomerBottomNav` 5-tab,
  tidak pernah mendapat rail. Ini disengaja: pengalaman customer tetap dibingkai HP di semua
  lebar viewport (lihat §Konvensi di bawah).
- **`theme/tokens.dart`** — tidak ada perubahan warna, tipografi, atau helper `display()`/`body()`.
  Font yang dirujuknya berubah isi biner (subset), bukan API-nya.
- **`bottom: 130` yang hardcoded** di 5 layar UMKM (`home_screen.dart`, `history_screen.dart`,
  `result_screen.dart`, `profile_screen.dart`, `briefing_screen.dart`) — nilai ini dihitung untuk
  memberi ruang di atas `FortunasBottomNav` (`extendBody: true`). Di medium/expanded tidak ada
  bottom nav (diganti rail di sisi kiri), jadi padding ini jadi dead space vertikal yang tidak
  perlu di layar lebar. **Ditunda murni untuk alasan koordinasi, bukan teknis** — mengedit lima
  file layar itu berisiko bertabrakan dengan kerjaan dev lain yang belum di-push. Ini adalah
  Task 4's `OPEN QUESTION` dari ledger, dan CONFIRMED visual pada Task 5 (rail memang menggantikan
  bottom nav dengan benar, dead space itu memang ada tapi bukan bug fungsional).
- **`android/` dan `ios/`** — tetap ada, tidak dihapus. `flutter build apk` masih harus bisa
  jalan untuk demo juri, jadi kedua folder platform native ini dipertahankan meski kanal rilis
  utama sekarang PWA.
- **`--wasm`/skwasm (jalur render WasmGC)** — DITUNDA, tapi alasannya **bukan lagi dependency**.
  `flutter_secure_storage` (dulu `^9.2.2`, ter-resolve ke `9.2.4`) memakai `dart:html`/`package:js`
  yang gagal kompilasi WasmGC; Task 6 (`d74b792`) menaikkannya ke `^10.3.1` untuk alasan lain
  (web token store di §"Apa yang berubah"), dan itu **sekaligus** menghilangkan `js` dari
  dependency tree — jalur `--wasm` sekarang **terbuka secara teknis**, cuma belum dicoba siapa
  pun. Tetap ditunda atas dasar risiko-vs-hasil dari spec
  (`brainstorming/specs/2026-08-06-pwa-responsive-shell-design.md` §5, di folder induk `Fortunas/`):
  penghematan hanya ≈0,45–0,58 MB gzip di browser yang mendukung WasmGC (Chrome/Edge 119+,
  Firefox 120+, **Safari 18.2+** — banyak iPhone UMKM masih di bawah versi itu dan otomatis
  fallback ke jalur JS/CanvasKit lama), Flutter sendiri masih memberi peringatan
  *"WebAssembly compilation is new. Understand the details before deploying to production"*,
  waktu build CI terukur naik dari 41,7 detik ke 117,9 detik, dan render engine yang berbeda
  berarti **seluruh 22 layar (13 UMKM + 9 customer) wajib diverifikasi ulang di browser** sebelum
  aman dipakai produksi.
- **Semantics accessibility** — belum disentuh sama sekali di branch ini. CanvasKit merender
  seluruh app sebagai satu `<canvas>`; snapshot accessibility halaman hanya menghasilkan tombol
  "Enable accessibility" tanpa elemen semantik lain di baliknya. Relevan kalau naskah paper
  menyinggung aksesibilitas, tapi eksplisit di luar cakupan branch ini (spec §6).
- **`frontend/` React** — dipertahankan sebagai arsip/rujukan desain, **tidak dihapus**
  (`git diff --name-only 135253b HEAD | grep '^frontend/'` kosong — nol file di bawah `frontend/`
  tersentuh branch ini). Spec §6 mensyaratkan folder ini "ditandai arsip di README-nya" — status
  itu **belum terpenuhi sebelum revisi handoff ini** (tidak ada `frontend/README.md` sebelumnya).
  Ditutup sekarang lewat `frontend/README.md` (baru): app ini bukan client yang di-ship (client
  yang di-ship = Flutter di `mobile/`, rilis PWA), disimpan karena 6 layar + voice flow Web Speech
  API-nya (`frontend/src/voice/useSpeechRecognition.js`) masih rujukan desain untuk 13 layar UMKM,
  dan tidak dibangun/dites/di-gate CI.

---

## Konvensi paling penting untuk dev berikutnya

**Kalau menambah route baru: bungkus dengan `PhoneFrame` seperti route lain, dan itu otomatis
mendapat perilaku responsif.** `PhoneFrame` membaca lokasi route lewat `GoRouter.maybeOf(context)`
dan mendelegasikan ke `AdaptiveShell`, yang memutuskan compact/medium/expanded dari lebar
viewport — tidak ada logika tambahan yang perlu ditulis di layar itu sendiri.

**Route customer WAJIB berprefiks `/customer/`.** Keputusan phone-only vs adaptif diturunkan
dari *path* route lewat `isPhoneOnlyRoute()` (lihat `mobile/lib/ui/adaptive_shell.dart`), bukan
dari jenis widget atau siapa pemanggilnya. Route yang lupa prefiks ini akan diam-diam mendapat
kolom lebar UMKM (840px) di viewport lebar, bukan bingkai HP 430px yang seharusnya menjaga
pengalaman customer tetap konsisten di semua device.

---

## Cara memverifikasi

```bash
cd mobile
flutter build web --release
# lalu serve build/web dari HTTP server apa pun, mis.:
python -m http.server 8099 --directory build/web
```

Cek di browser: 390px (compact, bottom nav), 800px (medium, rail 76 ikon-saja), 1440px
(expanded, rail 200 + konten 840), dan `/#/customer/login` (harus tetap kolom 430px terbingkai
di tengah dengan backdrop `#E9E4D8`, di viewport manapun).

**Peringatan cache — ini memakan waktu nyata saat mengerjakan branch ini.** HTTP cache browser
adalah *layer terpisah* dari service worker dan Cache API. Ia akan menyajikan `main.dart.js`
basi untuk build yang sudah diganti di disk, walau service worker sudah aktif dan Cache API
sudah dibersihkan. Membersihkan service worker + Cache API **tidak menyelesaikan** ini — kalau
tampilan terasa seperti kode lama padahal build baru sudah ada, serve dari **port/origin baru**
(mis. pindah dari `:8080` ke `:8099`), jangan mencoba clear cache lebih keras di origin yang sama.

---

## Angka payload (dengan metode pengukuran)

Diukur dengan .NET `GZipStream` pada `CompressionLevel.Optimal` terhadap artefak
`build/web` — bukan estimasi, bukan `gzip -9` command-line (beda encoder, angka bisa sedikit
berbeda).

| | Sebelum | Sesudah |
|---|---|---|
| Critical path (gzip) | 3,58 MB | 3,24 MB |
| Inter raw | 856 KB | 274 KB |
| Inter gzip | 448 KB | 134 KB |

Target DoD ≤3,25 MB gzip **tercapai** (3,24 MB).

Font `JetBrainsMono.ttf` dan `SpaceGrotesk.ttf` **tidak** disubset — sudah cukup kecil (89 KB
dan 62 KB gzip) sehingga risiko regresi coverage tidak sepadan dengan penghematannya.

---

## ⛔ Masih blocker

**Domain + HTTPS.** Tanpa secure context, browser mengunci `serviceWorker.register()`,
`beforeinstallprompt`, **dan `getUserMedia`** — jadi tanpa domain+HTTPS, **fitur voice mati**,
bukan cuma PWA install yang tidak muncul. Rumah (nginx config + runbook certbot) sudah dibangun
penuh di `deploy/DEPLOY.md` dan `deploy/nginx-fortunas.conf`; yang tersisa murni eksekusi
(arahkan DNS, ganti 4 placeholder `FORTUNAS_DOMAIN`, jalankan certbot).

Item ini naik dari 🔭 *anticipated* ke ⛔ *blocker* di `PENDING_EXTERNAL_SETUP.md` (folder induk
`Fortunas/`) tepat karena kanal rilis pindah ke PWA di branch ini — untuk kanal APK, HTTP hanya
"kurang ideal"; untuk PWA ia membunuh fitur yang bergantung pada secure context.

---

## 📌 Utang yang diterima sadar (accepted debt)

Ditulis apa adanya sesuai ledger (`.superpowers/sdd/2026-08-06-pwa-responsive-shell/progress.md`)
— kalau sesuatu tercatat di sana sebagai belum teruji atau trade sadar, begitu juga di sini.

1. **Bug rendering pre-existing: `✓` hilang di layar scan member** (ditemukan saat membangun
   font gate, **bukan disebabkan branch ini**).
   `mobile/lib/screens/scan_screen.dart:138` merender
   `Text('✓ ${r.username ?? 'Pelanggan'} terdaftar sebagai member', style: display(...))`.
   `display()` (`mobile/lib/theme/tokens.dart:67-80`) memakai `fontFamily: 'SpaceGrotesk'`, dan
   SpaceGrotesk **tidak pernah** memiliki glyph U+2713 `✓` — diverifikasi dengan `fontTools`
   langsung terhadap font yang dibundel, bukan diasumsikan. Baris ini jadi tampil **setiap kali
   pelanggan mendaftar sebagai member lewat scan QR** — pesan sukses yang dilihat pemilik toko
   secara rutin.
   Tidak disebabkan branch ini: bug ini sudah ada sebelumnya, dan hanya terlihat sekarang karena
   `mobile/tool/font_coverage_gate.py` dibuat generik untuk mengecek ketiga font bundel, bukan
   cuma Inter.
   **Belum terselesaikan:** tidak diverifikasi empiris apakah CanvasKit jatuh ke font bundel lain
   (Inter, yang sekarang punya `✓`), menampilkan tofu `▯`, atau mencoba fetch Noto lewat network
   — opsi terakhir ini akan bertentangan dengan catatan "font dibundel, tanpa fetch network saat
   runtime, jalan offline" di `mobile/lib/theme/tokens.dart:63-65`. Butuh pengecekan di device
   asli atau browser; layar ini butuh sesi backend terautentikasi untuk dicapai, jadi tidak bisa
   diverifikasi dari lingkungan sandbox task ini.
   Perbaikannya cuma satu kata (`display()` → `body()` di baris itu, supaya memakai Inter yang
   sudah punya `✓`) atau membuang glyph-nya — tapi keduanya perubahan Dart, di luar scope task
   font.

2. **`Scaffold` dobel di `ShellRoute` builder tab UMKM** (`app.dart:119-155`) — cabang compact
   dan cabang medium/expanded masing-masing membangun `Scaffold` sendiri (beda
   `bottomNavigationBar`/`extendBody`) padahal bisa disatukan jadi satu `Scaffold` dengan field
   kondisional. Ditahan demi diff minimality selagi edit dev lain di file yang sama belum di-push.

3. **Ketidakcocokan tier di rentang viewport 1024–1223px** — dikonfirmasi lewat pembacaan kode
   (`app.dart:126` + `adaptive_shell.dart:29-33`), bukan cuma disalin dari catatan: tier untuk
   memutuskan rail *extended* dihitung dari **lebar viewport penuh** (`shellTierFor(constraints.maxWidth)`
   di `ShellRoute` builder, sebelum rail memakan tempat), sedangkan `AdaptiveShell` di dalam
   `Expanded` menghitung tier-nya **sendiri** dari lebar yang tersisa **setelah** rail dikurangkan.
   Untuk viewport 1024–1223px: tier luar = `expanded` (rail 200px, `kNavRailExtendedWidth`) karena
   W ≥ 1024, tapi sisa lebar untuk konten (`W − 200`) jatuh di 824–1023px — di bawah ambang 1024 —
   sehingga `AdaptiveShell` di dalamnya menghitung tier `medium` (konten 720px, gutter 32px).
   Hasilnya: rail extended (dengan label teks) berdampingan dengan kolom konten lebar medium,
   bukan expanded (840px). Bukan bug fungsional (tidak ada crash, tidak ada konten terpotong),
   tapi kombinasi tier rail vs tier konten tidak selalu selaras di pita sempit ini.

4. **`kExpandedGutter` (48.0) tidak pernah terjangkau secara aritmetika** — di tier expanded,
   lebar konten (840) selalu menang atas gutter sebagai constraint pembatas untuk lebar viewport
   yang realistis; nilai gutter jadi dekoratif, tidak pernah benar-benar membatasi apa pun.
   Pertanyaan desain, bukan bug.

5. **Literal `'umkm_access_token'` terduplikasi** di dua token store (`SecureTokenStore` untuk
   native, store berbasis `localStorage` untuk web) tanpa konstanta bersama. Mengedit satu tanpa
   yang lain akan diam-diam memecah key native/web, dan tidak ada test yang akan menangkapnya.

6. **`bottom: 130` hardcoded** di 5 layar UMKM — lihat §"Apa yang SENGAJA TIDAK berubah" di atas.
   Ditunda demi koordinasi, bukan karena tidak tahu solusinya.

### Catatan tambahan (minor, untuk konteks — lihat ledger untuk daftar lengkap)

- Sejumlah minor kosmetik/dokumentasi dari Task 1–3 (urutan import, dartdoc yang merujuk simbol
  yang baru lahir di task berikutnya, komentar `adaptive_shell.dart` yang salah soal alasan
  `Scaffold` tidak kolaps) — semua tercatat di ledger, tidak diulang di sini karena tidak
  memengaruhi perilaku.
- `kMediaBaseUrl` sisi native menurunkan ulang `String.fromEnvironment` sendiri, tidak
  mendelegasikan ke `kApiBaseUrl` — provably setara, cuma DRY kosmetik.

---

## Tooling baru: `mobile/tool/font_coverage_gate.py`

Mengecek apakah setiap karakter non-ASCII yang benar-benar **dirender** oleh source Dart
(bukan sekadar muncul di komentar) ada di cmap font yang ditunjuk. Lahir dari insiden nyata:
pass subsetting pertama memakai daftar karakter yang ditulis tangan, dan daftar itu salah dua
arah sekaligus — melewatkan `⚠`/`✓` yang benar-benar dirender, dan menyertakan `∕` yang tidak
pernah ada di font maupun dipakai di app manapun.

Cara pakai:
```bash
cd mobile
python tool/font_coverage_gate.py                                  # cek Inter.ttf (default)
python tool/font_coverage_gate.py --font assets/fonts/JetBrainsMono.ttf
python tool/font_coverage_gate.py --font assets/fonts/SpaceGrotesk.ttf
```

Butuh `pip install fonttools`. **Exit non-zero** kalau ada codepoint yang dirender tapi hilang
dari cmap font target (kecuali yang di-allowlist sebagai gap pre-existing yang sudah
diverifikasi, mis. dua emoji yang tidak pernah ada di Inter). Detail lengkap rasional setiap
unicode range ada di `mobile/tool/README.md`.

**Belum diwire ke CI** — butuh langkah setup Python (`pip install fonttools`) ditambahkan ke job
mobile di `.github/workflows/ci.yml` sebelum `flutter test` jalan. Dicatat sebagai follow-up,
bukan dikerjakan di task ini.

---

## Batas jujur verifikasi

- **Shell tab UMKM (rail vs bottom nav) TIDAK PERNAH diverifikasi di browser sungguhan.** Auth
  gate memantulkan pengunjung tak terautentikasi ke `/login`, dan backend lokal tidak bisa
  dijalankan di sandbox ini (`app/main.py` → `routes/ask.py` → `agents/rag_agent.py` mengimpor
  `chromadb` secara eager, ±400 MB dependency). Klaim rail bersandar pada
  `mobile/test/ui/umkm_shell_route_test.dart`, yang mem-pump `routerProvider` **asli** (bukan
  router sintetis) dan memin lebar rail 76px di 600px serta 200px di 1440px, plus lebar konten
  840px. Verifikasi browser untuk shell tab ini masih terbuka untuk tim begitu ada backend yang
  bisa jalan.
- **Konfigurasi nginx dan runbook certbot dinalar dari semantik yang terdokumentasi, bukan
  dieksekusi** — tidak ada nginx atau certbot di sandbox dev ini. Sanity-check di bootstrap VPS
  nyata pertama tetap diperlukan.

---

## Files yang diubah (Task 12 saja)

- `docs/handoff/day-16.md` — dokumen ini (baru).

Task 1–11 (kode fitur, fix round, dan tooling) sudah di-commit sebelumnya di 17 commit HEAD
`04f99e4` — lihat `git log --oneline 135253b..HEAD` untuk daftar commit dan
`.superpowers/sdd/2026-08-06-pwa-responsive-shell/progress.md` untuk detail per-task, tiap
ronde fix, dan setiap temuan review.
