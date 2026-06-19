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
```
Mobile App  ──HTTP──►  nginx :80 (VPS)  ──►  uvicorn :8000 (systemd, 2 workers)
                                               │
                                               ├─► BigQuery (data per-tenant: {prefix}_transactions/_customers)
                                               ├─► Gemini API (LLM)
                                               └─► SQLite app/data/fortunas.db (akun & tenant)
```
