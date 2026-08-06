# Deploy Fortunas AI Backend ke VPS (Biznet, Ubuntu, IP + HTTP)

Panduan langkah demi langkah. Target: backend API jalan di VPS, diakses mobile app
via `http://IP_VPS/...`. HTTPS + domain menyusul (lihat bagian akhir).

> Catatan: ini deploy **backend (API) saja**. Frontend React tidak dideploy
> (client final = mobile app). Mobile app konek ke `http://IP_VPS`.

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
> JANGAN ikut upload `.venv`, `frontend/node_modules`. Boleh skip `chroma_db` (RAG opsional).
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
ufw allow 80/tcp
ufw --force enable
```
> Cek juga firewall/security group di panel Biznet: port 22 & 80 harus terbuka.

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
Swagger UI: `http://IP_VPS/docs`

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

```bash
cd mobile
flutter build web --release
sudo mkdir -p /var/www/fortunas
rsync -av --delete build/web/ <user>@<vps>:/var/www/fortunas/
```

`build/web` berisi `.symbols` (~3,8 MB) yang tidak pernah diserve dan kedua varian
canvaskit. Boleh dibiarkan; nginx hanya mengirim yang diminta browser.

### 3. Verifikasi setelah deploy

- `https://<domain>/` memuat aplikasi; tab bertuliskan **Fortunas AI**
- DevTools → Application → Service Workers: `activated`
- DevTools → Application → Manifest: nol peringatan installability
- Tekan tombol mic → browser meminta izin mikrofon (**bukti secure context bekerja**)
- Login berhasil (membuktikan proxy `/api/` benar)
- Gambar produk tampil (membuktikan proxy `/media/` benar)
