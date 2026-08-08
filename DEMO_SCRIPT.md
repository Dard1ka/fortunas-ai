# Fortunas AI — Demo Script (React PWA)

> Ditulis ulang di Gate D (ADR-0002, 2026-08-08): klien = **React `frontend/`**,
> live di **https://app.fortunas.id**. LLM aktif = **Gemini 2.5 Flash** (cloud);
> jalur Ollama/Qwen3 lokal diarsipkan (`profiles: ["archive"]` di compose).

## Persiapan Sebelum Demo

### 🌐 Cara 0 (paling gampang): pakai produksi

Buka **https://app.fortunas.id** — tidak perlu setup apa pun. HTTPS aktif, jadi
mic (voice) dan install PWA berfungsi. Login dengan akun demo tim (JANGAN pakai
tenant uji `toko_uji_*`).

### 🐳 Cara 1: Docker (backend) + Vite dev (frontend)

```bash
# Pastikan .env terisi (GEMINI_API_KEY, JWT_SECRET, BIGQUERY_*) dan credentials/ ada
docker compose up -d           # backend di :8000
docker compose ps              # fortunas_backend STATUS = running

cd frontend
npm ci
npm run dev                    # buka http://localhost:3000 (/api di-proxy ke :8000)
```

> Mic butuh secure context: untuk uji voice dari HP di jaringan yang sama,
> pakai `npm run dev:https` (mkcert).

### ⚙️ Cara 2: Manual (tanpa Docker)

```bash
# 1. Backend
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# 2. Frontend (terminal baru)
cd frontend
npm run dev
```

---

## Skenario Demo (7 skenario, ~12 menit)

### Skenario 1: Customer Loyal (Repeat Customer)
**Tujuan**: AI mengidentifikasi pelanggan yang sering belanja

1. Di Beranda, klik chip contoh **"Analisis Pelanggan Loyal"** (atau ketik
   "Siapa customer yang paling sering beli?") → **Analisis**
2. Tunggu hasil (produksi terukur ±3–4 detik)

**Poin ke juri**: intent dikenali dari bahasa natural → SQL per-tenant ke
BigQuery → LLM menginterpretasi jadi insight + rekomendasi; jawaban selalu
grounded pada data toko itu sendiri.

### Skenario 2: Jam Ramai (Peak Hour)
Ketik **"Kapan waktu paling ramai?"** → Analisis.
Diskusi: siapkan stok & target promo pada jam ramai.

### Skenario 3: Produk Bundling (Market Basket)
Ketik **"Produk apa yang sering dibeli bersama?"** → Analisis.
Diskusi: paket bundling berdasarkan data, bukan feeling.

### Skenario 4: Kasir + Kelola Produk (alur transaksi nyata)
1. **Profil → Kelola Produk** → tambah 1 produk (nama, harga, foto)
2. **Beranda → Kasir** → ketik nama produk → autocomplete menyarankan produk
   yang baru dibuat → simpan transaksi multi-item

**Poin**: data analitik lahir dari operasional sehari-hari, tanpa entry ganda.

### Skenario 5: Voice multi-item (HIGHLIGHT teknis)
1. Tekan tombol **mic** → ucapkan SATU kalimat berisi beberapa produk, mis.
   *"sabun cuci 10 harga 8.500, minyak goreng 5 harga 20.000, dan beras dua
   karung enam puluh ribu"*
2. Layar konfirmasi menampilkan 3 baris item (bisa dikoreksi) → simpan

**Poin**: parser lokal di perangkat (angka Bahasa Indonesia, "dua karung enam
puluh ribu" → 2 × Rp60.000), bekerja tanpa memanggil LLM.

### Skenario 6: Pesanan online + QRIS (alur pelanggan)
1. Jendela private: **app.fortunas.id/order** → masukkan kode toko (mis. `KDR-001`)
2. Pilih menu → **Pesan** → isi nama & HP → QRIS tampil → **"Saya sudah bayar"**
3. Kembali sebagai UMKM: Beranda menampilkan badge **"1 pesanan menunggu
   diterima"** → **Pesanan Masuk** → Terima → Selesai

**Poin**: pelanggan tanpa akun & tanpa aplikasi; UMKM memverifikasi dana lalu
satu tap — penjualan otomatis tercatat ke BigQuery.

### Skenario 7: Briefing Otomatis (WOW-moment penutup)
Tab **Briefing** → **Mulai Briefing** → 11 seksi analisis + executive summary.
Diskusi: "buka toko pagi, langsung dapat briefing bisnis — pembeda dari
dashboard biasa."

---

## Tips Presentasi

1. **Mulai dari masalah**: "UMKM punya data tapi tidak punya data analyst."
2. **Urutan di atas sudah naik-turun ritmenya** — analitik → operasional →
   voice → pelanggan → briefing sebagai penutup.
3. **Jika LLM lambat**: Gemini = API cloud; lambat berarti latensi jaringan.
4. **Jika error**: tunjukkan error handling yang sopan (Bahasa Indonesia) +
   agent trace.
5. **JANGAN demo pakai tenant uji** `toko_uji_jangan_dipakai` — buat/gunakan
   akun demo tim.
