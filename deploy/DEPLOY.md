# Deploy Fortunas AI ke VPS (Ubuntu) — PWA + API satu origin, HTTPS wajib

Panduan langkah demi langkah. Target akhir: **satu domain HTTPS**
(`app.fortunas.id`) menyajikan aplikasi (PWA **React + Vite**, `frontend/`) di
`/` dan mem-proxy API di `/api/` — keduanya dari nginx yang sama,
`deploy/nginx-fortunas.conf`. Backend tidak diubah sama sekali; trailing slash
pada `proxy_pass` yang memotong prefiks `/api`.

> **⛔ HTTPS + domain bukan langkah opsional di akhir — ia PRASYARAT.**
> Kanal rilis sekarang PWA, dan browser mengunci service worker, prompt install,
> **dan `getUserMedia` (mikrofon → fitur voice)** di balik secure context. Di
> `http://IP_VPS` polos, aplikasi tidak layak dipakai. Selain itu build web
> memakai base URL relatif `/api`, jadi ia **hanya** berfungsi di belakang nginx
> ini — bukan dengan menembak `http://IP_VPS:8000` langsung.

> **Urutan baca:** Step 1–6 (backend + systemd) berlaku apa adanya. Step 7
> **memasang** config nginx (cp + sed) tapi **TIDAK me-reload-nya** — blok 443
> menunjuk sertifikat Let's Encrypt yang belum ada di VPS baru, jadi `nginx -t`
> pasti gagal di titik itu. Aktivasi terjadi di **"Deploy PWA § 1. Domain +
> HTTPS"**: terbitkan sertifikat dulu (jalur `certonly --standalone`), baru
> `nginx -t && reload`. Step 8 dan Step 9 adalah **peninggalan era
> backend-only/IP** dan sudah digantikan; keduanya diberi tanda di tempatnya
> masing-masing.

> **Klien produksi = React 19 + Vite di `frontend/`** (ADR-0002,
> `docs/adr/0002-react-production-client.md`): dibangun, dites, dan di-gate CI
> (`Frontend (lint + test + build)`). Flutter di `mobile/` **deprecated** —
> cadangan demo sampai Gate D, TIDAK dideploy di alur ini dan TIDAK menerima
> fitur baru. Build yang diunggah ke docroot = `frontend/dist/`.

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
> JANGAN ikut upload `.venv`, `mobile/build`, `mobile/.dart_tool`, `frontend/node_modules`, `frontend/dist` (frontend TIDAK dibangun di VPS — build di laptop dev, hanya hasil `frontend/dist/` yang di-rsync ke docroot, lihat "Deploy PWA § 2"). Boleh skip `chroma_db` (RAG opsional).
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

## 7. nginx + firewall (pasang config — AKTIVASI baru di "Deploy PWA § 1")

> ⛔ **Blok ini sengaja TIDAK menjalankan `nginx -t`/reload.**
> `deploy/nginx-fortunas.conf` berisi blok `listen 443 ssl` yang menunjuk
> sertifikat Let's Encrypt. Di VPS baru sertifikat itu **belum ada**, jadi
> `nginx -t` pasti GAGAL (`cannot load certificate ... No such file or
> directory`). Urutannya: pasang file di sini → terbitkan sertifikat di
> **"Deploy PWA § 1. Domain + HTTPS"** → baru `nginx -t && reload` (ada di § 1).

> ⚠ **VPS existing yang masih menyajikan demo lewat IP** (config lama mem-proxy
> `http://<IP>/` langsung ke backend): JANGAN menimpa site lama dan JANGAN
> menghapus `default` — pasang config baru sebagai **site terpisah** supaya
> demo IP tetap hidup. Langkah persisnya ada di runbook redeploy (folder induk
> `Fortunas/REDEPLOY_VPS_RUNBOOK.md`, seksi R3-2). Blok di bawah ini untuk
> **VPS baru/bersih**.

```bash
cp deploy/nginx-fortunas.conf /etc/nginx/sites-available/fortunas
sed -i 's/FORTUNAS_DOMAIN/app.fortunas.id/g' /etc/nginx/sites-available/fortunas
grep -c FORTUNAS_DOMAIN /etc/nginx/sites-available/fortunas   # harus 0 (semua terganti)
ln -s /etc/nginx/sites-available/fortunas /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
# JANGAN `nginx -t` / reload di sini — lihat kotak peringatan di atas.

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
# 0. Prasyarat: config sudah dipasang + di-sed di Step 7 (file
#    /etc/nginx/sites-available/fortunas ada, placeholder sudah terganti).

# 1. Arahkan domain ke IP VPS — A record `app` di zona fortunas.id → IP VPS
#    verifikasi dari laptop: curl -s -o /dev/null -w "%{remote_ip}\n" http://app.fortunas.id

# 2. Terbitkan sertifikat PERTAMA KALI — jalur standalone.
#    (certbot --nginx TIDAK bisa dipakai di titik ini: config yang ter-enable
#     menunjuk file sertifikat yang belum ada, nginx menolak me-load-nya.
#     nginx berhenti sebentar selama penerbitan.)
sudo apt install -y certbot python3-certbot-nginx    # kalau belum terpasang
sudo mkdir -p /var/www/certbot                       # disiapkan utk webroot mode kelak
sudo systemctl stop nginx
sudo certbot certonly --standalone -d app.fortunas.id
sudo systemctl start nginx

# 3. AKTIVASI config (file sertifikat kini ada → nginx mau me-load-nya)
sudo nginx -t && sudo systemctl reload nginx

# 4. Uji perpanjangan otomatis (renewal TIDAK butuh stop nginx lagi)
sudo certbot renew --dry-run
```

> **Kenapa standalone dulu, bukan `certbot --nginx`:** config di atas berisi
> blok `listen 443 ssl` yang menunjuk sertifikat Let's Encrypt. Selama
> sertifikat **belum pernah diterbitkan**, `nginx -t` / reload apa pun
> (termasuk yang dicoba internal oleh `certbot --nginx`) gagal dengan
> `cannot load certificate ... No such file or directory` — nginx tidak bisa
> memuat config yang menunjuk sertifikat kosong. Karena itu penerbitan pertama
> memakai `certonly --standalone` (nginx dimatikan sebentar). **Setelah** file
> sertifikat ada, `certbot --nginx -d app.fortunas.id` dan `certbot renew`
> berjalan normal untuk seterusnya.

### 2. Build & unggah PWA

**Build** (di laptop developer — **byte-identik dengan perintah CI**, job
`Frontend (lint + test + build)`):

```bash
cd frontend
npm ci          # lockfile-pinned; Node >= 20.19 (CI pakai Node 22)
npm run build   # hasil di frontend/dist/
```

> **⛔ Cek pasca-build WAJIB — nol request pihak ketiga.** Font di-self-host
> (subset woff2 ber-hash di `dist/assets/`), jadi grep berikut harus **KOSONG**:
> ```bash
> grep -R "fonts.googleapis" dist/
> ```
> Kalau ada match, ada regresi yang memuat font dari Google saat runtime.
> Akibatnya: (a) IP setiap UMKM terkirim ke Google di tiap cold load —
> bersinggungan dengan narasi UU PDP proyek ini; (b) cold load offline tidak
> bisa boot (service worker hanya meng-cache resource same-origin). Build ulang
> setelah regresinya diperbaiki — jangan deploy build yang gagal cek ini.
>
> Cek kelengkapan rantai boot PWA (empat file wajib ada):
> ```bash
> ls dist/index.html dist/manifest.webmanifest dist/sw.js dist/registerSW.js
> ```

**Unggah.** Direktori tujuan harus dibuat **di VPS** lebih dulu (perintah
`mkdir`/`chown` di bawah jalan lewat `ssh`, BUKAN di laptop) dan dimiliki oleh
user SSH-mu, kalau tidak `rsync` sebagai user biasa akan gagal
`permission denied` di `/var/www/`. nginx berjalan sebagai `www-data` dan hanya
butuh hak **baca** — `755`/`644` sudah cukup, jangan `chown` ke `www-data`.

```bash
# (jalankan dari ROOT repo — kalau masih di dalam frontend/ setelah build,
#  `cd ..` dulu: path sumber di bawah adalah frontend/dist/ relatif root)

# 1. Siapkan direktori DI VPS (perhatikan: ini di dalam ssh)
ssh <user>@<vps> 'sudo mkdir -p /var/www/fortunas && sudo chown -R <user>:<user> /var/www/fortunas && sudo chmod 755 /var/www/fortunas'

# 2. DRY-RUN dulu — WAJIB. `--delete` menghapus apa pun di sisi tujuan yang
#    tidak ada di sumber; salah ketik path tujuan = penghapusan tanpa jaring.
#    Baca daftarnya: harus berisi file frontend/dist (index.html, assets/,
#    sw.js…), dan "deleting …" tidak boleh menyebut apa pun di luar deploy
#    PWA sebelumnya.
rsync -av --delete --dry-run frontend/dist/ <user>@<vps>:/var/www/fortunas/

# 3. Baru jalankan sungguhan
rsync -av --delete frontend/dist/ <user>@<vps>:/var/www/fortunas/
```

> Dari Windows: **tidak ada `sudo` di laptop**, dan `rsync` tidak ada di
> PowerShell/cmd — jalankan dua perintah `rsync` di atas dari **Git Bash** atau
> **WSL**. Alternatif tanpa rsync:
> `scp -r frontend/dist/* <user>@<vps>:/var/www/fortunas/` (tapi `scp` **tidak**
> menghapus file lama, jadi hapus manual dulu:
> `ssh <user>@<vps> 'rm -rf /var/www/fortunas/*'` — penting karena aset Vite
> ber-hash: file build lama yang tertinggal tidak pernah tertimpa namanya).

> **⚠ Docroot ini bukan tempat penitipan file.** `/var/www/fortunas` satu origin
> dengan API, dan **token JWT UMKM hidup di `localStorage` origin itu**. Apa pun
> yang disajikan dari sini — halaman statis yang tidak berhubungan, HTML hasil
> upload, direktori listing (`autoindex`) — mewarisi hak baca token sesi
> **setiap** UMKM. Isi `/var/www/fortunas` HANYA hasil `npm run build`
> (`frontend/dist/`).

### 3. Verifikasi setelah deploy

> **⚠ Jebakan SW basi saat verifikasi:** service worker `autoUpdate` bisa
> menyajikan build LAMA di kunjungan pertama pasca-deploy (SW lama masih
> memegang precache-nya sampai SW baru selesai install + halaman di-reload).
> Saat memverifikasi build baru: DevTools → Application → Service Workers →
> **Unregister** + Storage → **Clear site data**, lalu hard-reload — atau buka
> lewat jendela private. Pengguna biasa tidak perlu ini (update terpasang
> otomatis di navigasi berikutnya); ini hanya soal *kapan verifikatormu
> melihat* build baru.

- `https://app.fortunas.id/` memuat aplikasi; tab bertuliskan **Fortunas AI**
- DevTools → Application → Service Workers: `activated` (file `sw.js`)
- DevTools → Application → Manifest: nol peringatan installability
  (`manifest.webmanifest`, theme_color `#6D5EF7`)
- Tekan tombol mic → browser meminta izin mikrofon (**bukti secure context bekerja**)
- Login berhasil (membuktikan proxy `/api/` benar)
- Gambar produk tampil (membuktikan proxy `/media/` benar)
- **Nol request ke host pihak ketiga.** DevTools → Network, filter kolom Domain:
  semua request harus ke `app.fortunas.id` sendiri. Kalau ada
  `fonts.googleapis.com`/`fonts.gstatic.com`, build gagal cek § 2 — build ulang.
- **Boot offline.** Load sekali online sampai selesai, lalu DevTools → Network →
  **Offline** → reload. Aplikasi harus tetap boot (app shell + font woff2 masuk
  precache SW). Load *pertama kali* memang butuh jaringan — itu benar, bukan bug.
- **Header cache benar** — rantai boot `no-cache`, aset ber-hash `immutable`:
  ```bash
  # empat file rantai boot → harus Cache-Control: no-cache
  for f in index.html manifest.webmanifest sw.js registerSW.js; do
    echo "== $f"; curl -sI "https://app.fortunas.id/$f" | grep -i -E 'cache-control|strict-transport'
  done
  # satu aset ber-hash (ambil nama dari sumber index.html) → harus public, immutable
  ASET=$(curl -s https://app.fortunas.id/index.html | grep -o '/assets/index-[^"]*\.js' | head -1)
  echo "== $ASET"; curl -sI "https://app.fortunas.id$ASET" | grep -i -E 'cache-control|strict-transport'
  ```
- **SPA fallback jalan** (React Router pakai path riil): deep-link langsung ke
  rute dalam harus balas 200 dan me-render app, bukan 404:
  `curl -s -o /dev/null -w '%{http_code}\n' https://app.fortunas.id/briefing` → `200`.
- **HSTS ada di dokumen utama** (bukan cuma di `/api/`):
  `curl -sI https://app.fortunas.id/index.html | grep -i strict-transport` → harus muncul.
  Kalau kosong, `add_header` di `location = /index.html` menimpa warisan server-level —
  baris HSTS di blok itu hilang (lihat komentar jebakan di `nginx-fortunas.conf`).
- **Swagger tidak publik:** ketiga perintah ini harus balas `404`:
  ```bash
  curl -s -o /dev/null -w '%{http_code}\n' https://app.fortunas.id/api/docs
  curl -s -o /dev/null -w '%{http_code}\n' https://app.fortunas.id/api/redoc
  curl -s -o /dev/null -w '%{http_code}\n' https://app.fortunas.id/api/openapi.json
  ```
- **API tetap hidup + versi kode benar:**
  `curl -s https://app.fortunas.id/api/health` → `{"status":"ok",...}` dan
  `curl -s https://app.fortunas.id/api/analyses | python3 -c "import json,sys;print(len(json.load(sys.stdin)['available_analyses']))"`
  → **11** (kalau 4, backend VPS belum di-redeploy ke `main` — lihat runbook
  redeploy di folder induk).
