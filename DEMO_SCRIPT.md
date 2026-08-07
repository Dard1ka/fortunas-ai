# Fortunas AI — Demo Script

> **Catatan (Task 1d, 2026-08-07):** Setup di bawah ini sudah usang di dua hal —
> **(1)** LLM aktif produksi sekarang **Gemini 2.5 Flash**, bukan Ollama/Qwen3
> lokal (Ollama masih ada di `docker-compose.yml` tapi diarsipkan di balik
> `profiles: ["archive"]`, dipilih sengaja lewat `LLM_PROVIDER=ollama`); dan
> **(2)** klien React `frontend/` sudah **dihapus** dari repo (Task 1b) — klien
> yang di-ship sekarang adalah **Flutter web (PWA)** dari `mobile/`. Langkah di
> bawah ditulis ulang supaya cocok dengan repo saat ini.

## Persiapan Sebelum Demo

### 🐳 Cara 1: Docker (backend saja — Gemini, tanpa Ollama)

```bash
# Pastikan .env sudah diisi (GEMINI_API_KEY, JWT_SECRET, BIGQUERY_*) dan credentials/ ada
docker compose up -d           # start backend (background)
docker compose ps              # cek container fortunas_backend STATUS = running

# Jalankan PWA terpisah (bukan di dalam Docker):
cd mobile
flutter run -d chrome --dart-define=FORTUNAS_API=http://127.0.0.1:8000
```

> Ollama TIDAK perlu dinyalakan untuk demo — LLM aktif adalah Gemini (API cloud).
> Kalau memang mau demo jalur lokal arsip: `docker compose --profile archive up ollama`
> + `make pull-model` + set `LLM_PROVIDER=ollama` di `.env`.

### ⚙️ Cara 2: Manual (tanpa Docker)

```bash
# 1. Jalankan backend (Gemini API, tidak butuh Ollama)
cd fortunas-ai
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# 2. Jalankan PWA (terminal baru)
cd mobile
flutter run -d chrome --dart-define=FORTUNAS_API=http://127.0.0.1:8000
```

---

## Skenario Demo (5 skenario, ~10 menit)

### Skenario 1: Customer Loyal (Repeat Customer)
**Tujuan**: Tunjukkan AI bisa identifikasi pelanggan yang sering belanja

**Langkah**:
1. Klik contoh pertanyaan: **"Siapa customer yang paling sering beli?"**
2. Klik **Analisis**
3. Tunggu hasil (~15-30 detik)

**Yang ditunjukkan ke juri**:
- AI mengenali intent "repeat customer" dari bahasa natural
- Query SQL otomatis dijalankan ke BigQuery
- LLM menginterpretasi data menjadi insight yang mudah dipahami
- Ada 3 temuan + 3 rekomendasi spesifik
- Agent trace menunjukkan step-by-step proses

---

### Skenario 2: Jam Ramai (Peak Hour)
**Tujuan**: Tunjukkan analisis waktu transaksi

**Langkah**:
1. Klik **"Tanya pertanyaan baru"**
2. Ketik: **"Kapan waktu paling ramai?"**
3. Klik Analisis

**Poin diskusi**:
- "Pemilik UMKM bisa tahu kapan harus siapkan stok lebih"
- "Promo bisa ditargetkan pada jam ramai"

---

### Skenario 3: Produk Bundling
**Tujuan**: Tunjukkan market basket analysis

**Langkah**:
1. Klik pertanyaan baru
2. Ketik: **"Produk apa yang sering dibeli bersama?"**
3. Klik Analisis

**Poin diskusi**:
- "AI menemukan pasangan produk yang sering dibeli bersamaan"
- "UMKM bisa buat paket bundling berdasarkan data, bukan feeling"

---

### Skenario 4: High-Value Customer
**Tujuan**: Identifikasi customer bernilai tinggi

**Langkah**:
1. Klik pertanyaan baru
2. Klik contoh: **"Siapa customer dengan belanja tertinggi?"**
3. Klik Analisis

**Poin diskusi**:
- "Customer bernilai tinggi perlu treatment khusus"
- "AI kasih rekomendasi spesifik per customer"

---

### Skenario 5: Briefing Otomatis (HIGHLIGHT)
**Tujuan**: Tunjukkan fitur unggulan — auto-analysis tanpa perlu bertanya

**Langkah**:
1. Klik tab **"Briefing Bisnis"**
2. Klik **"Mulai Briefing Otomatis"**
3. Tunggu (~2-5 menit, seluruh 11 analisis terdaftar + executive summary — lihat `app/analysis_registry.py`)

**Poin diskusi**:
- "Ini yang membedakan Fortunas dari dashboard biasa"
- "Pemilik UMKM buka pagi, langsung dapat briefing bisnis"
- "Executive summary merangkum semua insight jadi 2-3 kalimat"
- "Setiap section bisa di-expand untuk detail"

---

## Tips Presentasi

1. **Mulai dari masalah**: "UMKM punya data tapi tidak punya data analyst"
2. **Demo yang smooth**: Buka semua skenario berurutan, jangan lompat-lompat
3. **Briefing terakhir**: Ini wow-moment, simpan untuk penutup
4. **Jika LLM lambat**: LLM aktif adalah Gemini 2.5 Flash (API cloud) — lambat biasanya karena latensi jaringan, bukan komputasi lokal. Jalur lokal (Ollama/Qwen3) masih ada sebagai arsip kalau perlu demo tanpa API key.
5. **Jika error**: Tunjukkan error handling yang graceful, jelaskan agent trace
