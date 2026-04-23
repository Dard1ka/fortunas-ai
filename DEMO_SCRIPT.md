# Fortunas AI — Demo Script

## Persiapan Sebelum Demo

### 🐳 Cara 1: Docker (Recommended — v2.0.0+)

```bash
# Pastikan .env sudah diisi dan credentials/ ada
docker compose up -d           # start semua services (background)
docker compose ps              # cek semua container STATUS = running

# Pull model jika belum pernah (sekali saja)
docker compose exec ollama ollama pull qwen3:8b

# Buka browser
# http://localhost:3000
```

> Model Qwen3:8b otomatis ter-load. Tunggu ~30 detik setelah container up sebelum demo.

### ⚙️ Cara 2: Manual (tanpa Docker)

```bash
# 1. Pastikan Ollama running dengan model qwen3:8b
ollama serve
ollama pull qwen3:8b   # jika belum ada

# 2. Jalankan backend
cd Fortunas
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# 3. Jalankan frontend (terminal baru)
cd Fortunas/frontend
npm run dev

# 4. Buka browser: http://localhost:3000
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
3. Tunggu (~2-5 menit, semua 4 analisis + executive summary)

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
4. **Jika LLM lambat**: Jelaskan bahwa ini local LLM di laptop biasa, di production bisa lebih cepat
5. **Jika error**: Tunjukkan error handling yang graceful, jelaskan agent trace
