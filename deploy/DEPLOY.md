# Deploy Fortunas AI ke VPS (Ubuntu) — PWA + API satu origin, HTTPS wajib

Panduan langkah demi langkah. Target akhir: **satu domain HTTPS** menyajikan
aplikasi (PWA Flutter web) di `/` dan mem-proxy API di `/api/` — keduanya dari
nginx yang sama, `deploy/nginx-fortunas.conf`. Backend tidak diubah sama sekali;
trailing slash pada `proxy_pass` yang memotong prefiks `/api`.

> **⛔ HTTPS + domain bukan langkah opsional di akhir — ia PRASYARAT.**
> Kanal rilis sekarang PWA, dan browser mengunci service worker, prompt install,
> **dan `getUserMedia` (mikrofon → fitur voice)** di balik secure context. Di
> `http://IP_VPS` polos, aplikasi tidak layak dipakai. Selain itu build web
> memakai base URL relatif `/api`, jadi ia **hanya** berfungsi di belakang nginx
> ini — bukan dengan menembak `http://IP_VPS:8000` langsung.

> **Urutan baca:** Step 1–6 (backend + systemd) berlaku apa adanya. **Sebelum**
> Step 7 (nginx), kerjakan **"Deploy PWA § 1. Domain + HTTPS"** di bawah — config
> nginx menunjuk sertifikat Let's Encrypt yang belum ada di VPS baru, jadi
> `nginx -t` akan gagal kalau dijalankan lebih dulu. Step 8 dan Step 9 adalah
> **peninggalan era backend-only/IP** dan sudah digantikan; keduanya diberi
> tanda di tempatnya masing-masing.

> **Frontend React (`frontend/`) dipertahankan di repo sebagai arsip/rujukan
> desain** (Task 1e, membatalkan sebagian penghapusan Task 1b) — tidak
> dibangun, tidak dites, tidak di-gate CI, dan **tidak dideploy** di alur ini.
> Client yang di-ship = Flutter di `mobile/`, dirilis sebagai PWA saja.
> `mobile/android/` dan `mobile/ios/` (target native) tetap sudah dihapus
> (Task 1b) — APK/appbundle **tidak bisa** dibangun lagi dari repo ini;
> `flutter build web` adalah satu-satunya target build.

---

## 0. Prasyarat
- VPS Ubuntu 22.04/24.04 (Biznet NEO Lite) + IP publik + akses SSH (user root atau sudo).
- File `credentials/fortunas-service-account.json` (service account GCP, punya akses BigQuery Data Editor + Job User).
- `GEMINI_API_KEY`.
- Kode project (repo ini).

---

## 1. Login & paket dasar
```bash
ssh root@IP_VPS                      # atau user sudo-mu
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip git nginx ufw
# buat user khusus app (jangan jalankan sebagai root)
adduser --system --group --home /opt/fortunas-ai fortunas
```

## 2. Taruh kode di /opt/fortunas-ai
**Opsi A — dari Git** (kalau repo sudah di GitHub):
```bash
cd /opt
git clone <URL_REPO> fortunas-ai
chown -R fortunas:fortunas /opt/fortunas-ai
```
**Opsi B — upload dari laptop** (kalau belum ada remote). Dari PC Windows (PowerShell), kecualikan folder berat:
```powershell
# install dulu rsync via Git Bash / WSL, atau pakai scp:
scp -r "E:\Project LLM\Fortunas2\fortunas-ai" root@IP_VPS:/opt/fortunas-ai
```
> JANGAN ikut upload `.venv`, `mobile/build`, `mobile/.dart_tool`, `frontend/node_modules`, `frontend/dist` (folder `frontend/` ada di repo sebagai arsip/rujukan desain, tapi tidak dideploy — tidak relevan untuk VPS). Boleh skip `chroma_db` (RAG opsional).
Lalu: `chown -R fortunas:fortunas /opt/fortunas-ai`

## 3. Virtualenv + dependencies
```bash
cd /opt/fortunas-ai
sudo -u fortunas python3 -m venv .venv
sudo -u fortunas .venv/bin/pip install --upgrade pip
sudo -u fortunas .venv/bin/pip install -r requirements.txt
```
> Install agak lama (torch dll). Di Linux biasanya lancar.

## 4. Credentials + .env
```bash
# upload service-account JSON ke /opt/fortunas-ai/credentials/
mkdir -p /opt/fortunas-ai/credentials
# (scp file JSON ke sana), lalu:
chown -R fortunas:fortunas /opt/fortunas-ai/credentials
chmod 600 /opt/fortunas-ai/credentials/*.json

# buat .env dari contoh
cp deploy/.env.production.example .env
nano .env        # isi GEMINI_API_KEY, JWT_SECRET, path credentials, dll
# generate JWT_SECRET kuat:
openssl rand -hex 32        # tempel hasilnya ke JWT_SECRET di .env
chown fortunas:fortunas .env && chmod 600 .env
mkdir -p app/data && chown -R fortunas:fortunas app/data
```

## 5. (Opsional) Aktifkan RAG
RAG = tips UMKM untuk memperkaya rekomendasi. Tanpa ini, /ask tetap jalan (cuma tanpa "sumber").
Untuk mengaktifkan, bangun index di server (butuh internet untuk unduh model embedding):
```bash
sudo -u fortunas .venv/bin/python -m app.knowledge.ingest
```
> Kalau gagal/skip, app tetap jalan (RAG otomatis disabled, non-fatal).

## 6. systemd (auto-start + auto-restart)
```bash
cp deploy/fortunas-backend.service /etc/systemd/system/
# cek User= dan path di file itu sudah sesuai (fortunas, /opt/fortunas-ai)
systemctl daemon-reload
systemctl enable --now fortunas-backend
systemctl status fortunas-backend     # harus "active (running)"
# cek health lokal:
curl http://127.0.0.1:8000/health      # {"status":"ok",...}
```

## 7. nginx + firewall

> ⛔ **VPS baru / sertifikat belum pernah diterbitkan:** `deploy/nginx-fortunas.conf`
> sekarang berisi blok `listen 443 ssl` yang menunjuk sertifikat Let's
> Encrypt. Kalau sertifikat itu **belum ada**, `nginx -t` di bawah akan
> GAGAL (`cannot load certificate ... No such file or directory`) dan
> `&& systemctl reload nginx` tidak akan jalan. **Baca "Deploy PWA § 1.
> Domain + HTTPS" (jauh di bawah) dulu — termasuk fallback
> `certbot certonly --standalone`nya — sebelum menjalankan blok ini**, atau
> terbitkan sertifikatnya lebih dulu baru lanjut ke sini.

```bash
cp deploy/nginx-fortunas.conf /etc/nginx/sites-available/fortunas
ln -s /etc/nginx/sites-available/fortunas /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

ufw allow OpenSSH
ufw allow 80/tcp     # ACME challenge + redirect 301 ke HTTPS
ufw allow 443/tcp    # PWA + API — TANPA ini aplikasi tidak bisa diakses sama sekali
ufw --force enable
```
> Cek juga firewall/security group di panel Biznet: port 22, 80, **dan 443** harus terbuka.
> 443 bukan opsional: sejak skema same-origin, port 80 hanya redirect + ACME.

## 8. Tes dari luar

> ⚠️ **Perintah di bawah ini untuk config LAMA (backend-only, IP+HTTP).**
> Sejak `nginx-fortunas.conf` dipindah ke skema same-origin (lihat "Deploy
> PWA" di bawah), port 80 sudah tidak mem-proxy apa pun langsung — ia
> hanya melayani tantangan ACME certbot dan redirect 301 ke HTTPS, jadi
> `curl http://IP_VPS/health` di bawah akan dapat redirect, bukan respons
> backend. Kalau nginx sudah dipasang dengan config baru (Step 7) tapi
> domain/HTTPS ("Deploy PWA § 1") belum jalan, uji backend langsung dari
> SSH ke VPS: `curl http://127.0.0.1:8000/health` (lewat systemd, bukan
> nginx — sama seperti Step 6). Setelah domain + HTTPS aktif, ulangi tes
> dari luar dengan prefiks `/api/` di atas HTTPS, mis.
> `curl https://<domain>/api/health`.

Dari laptop:
```bash
curl http://IP_VPS/health
# register tenant:
curl -X POST http://IP_VPS/auth/register -H "Content-Type: application/json" \
  -d '{"email":"owner@toko.com","password":"rahasia123","business_name":"Toko Saya","business_profile":{"jenis":"warung sembako"}}'
# login → ambil access_token, lalu panggil /ask dengan header Authorization: Bearer <token>
```
**Swagger UI SENGAJA tidak dipublikasikan.** nginx mengembalikan 404 untuk `/api/docs`,
`/api/redoc`, dan `/api/openapi.json` (`app/main.py` tidak diubah — pembendungan ada di
nginx). Untuk melihat docs, buka dari **dalam** VPS lewat SSH:
`curl http://127.0.0.1:8000/docs`, atau tunnel: `ssh -L 8000:127.0.0.1:8000 <user>@<vps>`
lalu buka `http://127.0.0.1:8000/docs` di browser laptop.

## 9. HTTPS nanti (saat punya domain)

> ⚠️ **Sudah digantikan oleh "Deploy PWA § 1. Domain + HTTPS"** (di bawah,
> setelah diagram arsitektur). `nginx-fortunas.conf` sekarang memakai
> skema same-origin — satu domain untuk PWA + API (placeholder
> `FORTUNAS_DOMAIN`, di-`sed` sekali), BUKAN subdomain `api.*` terpisah
> seperti langkah 3-4 di bawah. Langkah 1-4 ini peninggalan era
> backend-only/IP — referensi historis saja, jangan diikuti untuk deploy PWA.

1. Arahkan domain (A record) ke IP_VPS.
2. Edit `server_name` di nginx ke domain.
3. `apt install certbot python3-certbot-nginx && certbot --nginx -d api.domainmu.com`
4. Mobile app ganti base URL ke `https://api.domainmu.com`.

## 10. Operasional
- **Log**: `tail -f /var/log/fortunas-backend.log` atau `journalctl -u fortunas-backend -f`
- **Restart**: `systemctl restart fortunas-backend`
- **Update kode**: `git pull` (atau upload ulang) → `systemctl restart fortunas-backend`
- **Backup**: file akun/tenant ada di `app/data/fortunas.db` (backup rutin). Data bisnis di BigQuery (managed Google).
- **Keamanan**: pastikan `.env` & credentials `chmod 600`; JWT_SECRET kuat & rahasia; pertimbangkan ganti port SSH / fail2ban.

---

## Ringkasan arsitektur produksi

> Diagram di bawah sudah versi same-origin (pasca Task 9). nginx :80 cuma
> redirect ke HTTPS + ACME challenge; API tidak lagi diproxy langsung di
> root seperti sebelumnya — lihat "Deploy PWA" untuk detail & runbooknya.

```
Browser (PWA)  ──HTTPS:443──►  nginx (VPS)  ─┬─ /            → PWA statis (/var/www/fortunas)
                                              ├─ /api/  ──(strip prefix)──► uvicorn :8000 (systemd, 2 workers)
                                              └─ /media/ (tanpa strip) ────►      │
                                                                                   ├─► BigQuery (data per-tenant: {prefix}_transactions/_customers)
                                                                                   ├─► Gemini API (LLM)
                                                                                   └─► SQLite app/data/fortunas.db (akun & tenant)

nginx :80  ──►  redirect 301 ke HTTPS (kecuali /.well-known/acme-challenge/ untuk certbot)
```

---

## Deploy PWA (kanal rilis)

PWA dan API berada di **satu origin**. nginx menyajikan file statis di `/` dan
mem-proxy API di `/api/` — backend tidak diubah.

### 1. Domain + HTTPS (⛔ WAJIB, kerjakan lebih dulu)

Tanpa HTTPS: service worker tidak teregistrasi, tidak ada prompt install, dan
**mikrofon diblokir sehingga fitur voice mati**. Ini bukan penyempurnaan —
tanpa ini PWA tidak layak dipakai.

```bash
# 1. Arahkan domain ke IP VPS (DuckDNS gratis, atau A record di registrar)
#    contoh: fortunas.duckdns.org → <IP VPS>

# 2. Ganti placeholder di config (4 kemunculan)
sudo sed -i 's/FORTUNAS_DOMAIN/fortunas.duckdns.org/g' \
  /etc/nginx/sites-available/fortunas

# 3. Terbitkan sertifikat
# (mkdir di bawah untuk fallback webroot mode; --nginx tidak memakainya,
#  tapi murah untuk disiapkan sekarang — lihat komentar di nginx-fortunas.conf)
sudo mkdir -p /var/www/certbot
sudo certbot --nginx -d fortunas.duckdns.org

# 4. Uji perpanjangan otomatis
sudo certbot renew --dry-run
```

> **Jebakan bootstrap pertama kali:** `deploy/nginx-fortunas.conf` sudah
> berisi blok `listen 443 ssl` yang menunjuk ke sertifikat Let's Encrypt.
> Kalau sertifikat itu **belum pernah diterbitkan**, `nginx -t` / reload apa
> pun (termasuk yang dicoba internal oleh certbot) akan gagal dengan
> `cannot load certificate ... No such file or directory` — nginx tidak
> bisa memuat config yang menunjuk sertifikat kosong. Kalau `certbot --nginx`
> gagal karena ini, terbitkan sertifikat dulu tanpa nginx aktif:
> `sudo systemctl stop nginx && sudo certbot certonly --standalone -d fortunas.duckdns.org && sudo systemctl start nginx`
> — setelah file sertifikat ada, reload nginx dengan config penuh di atas
> akan berhasil, dan `certbot --nginx`/`certbot renew` berikutnya berjalan normal.

### 2. Build & unggah PWA

**Build** (di laptop developer):

```bash
cd mobile
flutter build web --release --no-web-resources-cdn
```

> **⛔ `--no-web-resources-cdn` WAJIB, jangan dihilangkan.** Tanpa flag itu
> `flutter_bootstrap.js` memancarkan `buildConfig` ber-`engineRevision` tanpa
> `useLocalCanvasKit`, sehingga loader mengambil CanvasKit dari
> `https://www.gstatic.com/flutter-canvaskit/<engineRevision>/canvaskit.js` saat
> runtime. Empat akibatnya semuanya membatalkan klaim yang dipegang produk ini:
> 1. **Cold load offline tidak bisa boot.** `flutter_service_worker.js` hanya
>    meng-cache resource same-origin, jadi CanvasKit tidak pernah masuk cache.
> 2. **Ada script pihak ketiga yang disuntik saat runtime**, walau `index.html`
>    sendiri tidak memuat script eksternal apa pun.
> 3. Angka payload jadi bohong: `canvaskit.wasm` dihitung sebagai payload origin
>    padahal tidak pernah diminta dari origin ini.
> 4. Blok `.wasm` (`default_type application/wasm` + gzip) di
>    `nginx-fortunas.conf` jadi mati — tidak ada `.wasm` yang pernah diminta.
>
> Ditambah: satu request pihak ketiga per cold load mengirim IP setiap UMKM ke
> Google — bersinggungan dengan narasi UU PDP proyek ini. Flag yang sama sudah
> dipasang di gate CI (`.github/workflows/ci.yml`), supaya CI mem-build persis
> apa yang dideploy.
>
> **Cek cepat setelah build** — harus mencetak satu baris:
> ```bash
> grep -o '"useLocalCanvasKit":true' build/web/flutter_bootstrap.js
> ```
> Kalau kosong, flag-nya tidak terpakai. Jangan pakai `grep gstatic` sebagai
> cek: string `www.gstatic.com` **tetap ada** di loader sebagai cabang `else`
> (`…useLocalCanvasKit?…:_("https://www.gstatic.com/flutter-canvaskit"…)`), jadi
> keberadaannya tidak membuktikan apa pun. Yang menentukan adalah flag
> `useLocalCanvasKit` di `_flutter.buildConfig`.

**Unggah.** Direktori tujuan harus dibuat **di VPS** lebih dulu (perintah
`mkdir`/`chown` di bawah jalan lewat `ssh`, BUKAN di laptop) dan dimiliki oleh
user SSH-mu, kalau tidak `rsync` sebagai user biasa akan gagal
`permission denied` di `/var/www/`. nginx berjalan sebagai `www-data` dan hanya
butuh hak **baca** — `755`/`644` sudah cukup, jangan `chown` ke `www-data`.

```bash
# 1. Siapkan direktori DI VPS (perhatikan: ini di dalam ssh)
ssh <user>@<vps> 'sudo mkdir -p /var/www/fortunas && sudo chown -R <user>:<user> /var/www/fortunas && sudo chmod 755 /var/www/fortunas'

# 2. DRY-RUN dulu — WAJIB. `--delete` menghapus apa pun di sisi tujuan yang
#    tidak ada di sumber; salah ketik path tujuan = penghapusan tanpa jaring.
#    Baca daftarnya: harus berisi file build/web, dan "deleting …" tidak boleh
#    menyebut apa pun di luar deploy PWA sebelumnya.
rsync -av --delete --dry-run build/web/ <user>@<vps>:/var/www/fortunas/

# 3. Baru jalankan sungguhan
rsync -av --delete build/web/ <user>@<vps>:/var/www/fortunas/
```

> Dari Windows (branch ini dibangun di Windows): **tidak ada `sudo` di laptop**,
> dan `rsync` tidak ada di PowerShell/cmd — jalankan dua perintah `rsync` di atas
> dari **Git Bash** atau **WSL**. Alternatif tanpa rsync:
> `scp -r build/web/* <user>@<vps>:/var/www/fortunas/` (tapi `scp` **tidak**
> menghapus file lama, jadi hapus manual dulu:
> `ssh <user>@<vps> 'rm -rf /var/www/fortunas/*'`).

> **⚠ Docroot ini bukan tempat penitipan file.** `/var/www/fortunas` satu origin
> dengan API, dan **token JWT UMKM hidup di `localStorage` origin itu**. Apa pun
> yang disajikan dari sini — halaman statis yang tidak berhubungan, HTML hasil
> upload, direktori listing (`autoindex`) — mewarisi hak baca token sesi
> **setiap** UMKM. Isi `/var/www/fortunas` HANYA hasil `flutter build web`.

`build/web` berisi `.symbols` (~3,8 MB) yang tidak pernah diserve dan kedua varian
canvaskit (`canvaskit/` untuk Firefox/Safari, `canvaskit/chromium/` untuk
Chrome/Edge). Boleh dibiarkan; nginx hanya mengirim yang diminta browser.

### 3. Verifikasi setelah deploy

- `https://<domain>/` memuat aplikasi; tab bertuliskan **Fortunas AI**
- DevTools → Application → Service Workers: `activated`
- DevTools → Application → Manifest: nol peringatan installability
- Tekan tombol mic → browser meminta izin mikrofon (**bukti secure context bekerja**)
- Login berhasil (membuktikan proxy `/api/` benar)
- Gambar produk tampil (membuktikan proxy `/media/` benar)
- **Nol request ke host pihak ketiga.** DevTools → Network, filter kolom Domain: semua
  request harus ke `<domain>` sendiri. Kalau ada `www.gstatic.com`, build-nya dibangun tanpa
  `--no-web-resources-cdn` — build ulang.
- **Boot offline.** Load sekali online sampai selesai, lalu DevTools → Network → **Offline**
  → reload. Aplikasi harus tetap boot. (Load *pertama kali* memang butuh jaringan: resource
  non-CORE seperti `canvaskit/*` dan font baru di-cache saat pertama diminta.)
- **Header cache benar** — `flutter_bootstrap.js` dan `main.dart.js` harus `no-cache`,
  bukan `max-age=2592000`:
  ```bash
  for f in / index.html flutter_bootstrap.js main.dart.js manifest.json flutter_service_worker.js; do
    echo "== $f"; curl -sI "https://<domain>/$f" | grep -i -E 'cache-control|strict-transport'
  done
  ```
- **HSTS ada di dokumen utama** (bukan cuma di `/api/`):
  `curl -sI https://<domain>/index.html | grep -i strict-transport` → harus muncul.
  Kalau kosong, `add_header` di `location = /index.html` menimpa warisan server-level —
  baris HSTS di blok itu hilang (lihat komentar jebakan di `nginx-fortunas.conf`).
- **Swagger tidak publik:** ketiga perintah ini harus balas `404`:
  ```bash
  curl -s -o /dev/null -w '%{http_code}\n' https://<domain>/api/docs
  curl -s -o /dev/null -w '%{http_code}\n' https://<domain>/api/redoc
  curl -s -o /dev/null -w '%{http_code}\n' https://<domain>/api/openapi.json
  ```
- **API tetap hidup:** `curl -s https://<domain>/api/health` → `{"status":"ok",...}`
  (membuktikan blok 404 di atas tidak kebablasan memblokir seluruh `/api/`).
