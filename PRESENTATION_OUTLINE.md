# Fortunas AI — Presentation Outline

## 1. Problem Statement
UMKM di Indonesia menghasilkan data transaksi setiap hari, tetapi:
- Tidak punya data analyst untuk mengolah data
- Keputusan bisnis masih berdasarkan "feeling", bukan data
- Tools analytics yang ada terlalu mahal dan teknis untuk UMKM

**Pertanyaan kunci**: Bagaimana UMKM bisa mendapat insight dari data mereka sendiri tanpa perlu keahlian teknis?

## 2. Solution
**Fortunas AI** — AI agent yang menjadi "business advisor pribadi" untuk UMKM.

- Tanya dalam bahasa natural (Bahasa Indonesia)
- AI otomatis analisis data transaksi
- Hasil berupa insight + rekomendasi yang actionable
- Briefing otomatis — AI proaktif menganalisis tanpa perlu bertanya
- Real-time streaming — hasil muncul saat setiap analisis selesai

## 3. Arsitektur

```
User (Bahasa Natural)
  |
  v
Intent Router (keyword matching + disambiguator)
  |
  v
SQL Agent (query template dari QUERY_MAP)
  |
  v
BigQuery (execute query, return rows)
  |
  v
Local LLM / Ollama (interpret results → insight + rekomendasi)
  |
  v
Frontend (React — glassmorphism dark theme, accessible)
```

## 4. Core Features

| Fitur | Deskripsi |
|-------|-----------|
| Natural Language Query | Tanya pakai bahasa sehari-hari |
| 4 Analisis Inti | Repeat customer, peak hour, bundling, high-value customer |
| AI Interpretation | LLM ubah data mentah jadi insight bisnis natural language |
| Auto Recommendation | Setiap analisis disertai 3 saran actionable |
| Briefing Otomatis | Satu klik, semua analisis + executive summary |
| SSE Live Streaming | Hasil briefing muncul incremental via Server-Sent Events |
| Pipeline Visualization | Step-by-step progress saat menunggu analisis |
| Agent Trace | Transparansi proses AI step-by-step |
| Accessibility | WCAG AA contrast, keyboard nav, reduced motion, screen reader |

## 5. Tech Stack

| Layer | Teknologi |
|-------|-----------|
| Frontend | React + Vite |
| Backend | FastAPI (Python) |
| Database | Google BigQuery |
| AI/LLM | Ollama (Qwen3:8b, local) |
| Streaming | Server-Sent Events (SSE) |
| Agent Logic | Intent routing + SQL agent |

**Kenapa Local LLM?**
- Data UMKM sensitif, tidak perlu dikirim ke cloud
- Bisa jalan di laptop biasa (8GB+ RAM)
- Gratis, tidak ada biaya API

## 6. Value Proposition

1. **Aksesibilitas**: UMKM tidak perlu hire data analyst
2. **Privasi**: Data tetap di lokal, LLM jalan di laptop sendiri
3. **Actionable**: Bukan cuma angka, tapi saran yang bisa langsung diterapkan
4. **Proaktif**: Briefing otomatis — AI yang inisiatif, bukan menunggu pertanyaan
5. **Real-time**: SSE streaming — lihat hasil satu per satu, tidak menunggu semua selesai
6. **Inclusive**: Accessible untuk user dengan gangguan penglihatan (WCAG AA)
7. **Scalable**: Arsitektur siap migrasi ke Rust untuk production

## 7. Demo
*(Lihat DEMO_SCRIPT.md untuk detail)*

5 skenario live demo:
1. Identifikasi customer loyal — lihat pipeline step-by-step
2. Analisis jam ramai
3. Rekomendasi bundling produk
4. Identifikasi high-value customer
5. **Briefing otomatis** (highlight) — live streaming results

## 8. Future Development

| Fase | Rencana |
|------|---------|
| Short-term | Tambah analisis (churn prediction, seasonal trend) |
| Medium-term | Migrasi backend ke Rust (Axum + SQLx) untuk performa |
| Long-term | Multi-tenant SaaS untuk banyak UMKM |
| Enhancement | Dashboard visual (chart, graph), export PDF |
| AI | Upgrade ke model lebih besar, fine-tuning untuk domain UMKM |
