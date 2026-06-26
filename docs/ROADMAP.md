# Fortunas AI — Roadmap Produk & Eksekusi

> **Tujuan dokumen:** supaya **semua anggota tim paham** dalam 5 menit — kita di mana sekarang, mau ke mana, dan urutan kerjanya.
> **Update:** 25 Juni 2026 · **Sumber kebenaran kode:** `github.com/Dard1ka/fortunas-ai` @ `main`
> **Detail harian:** lihat [`PLAN_EVERY_DEV.md`](./PLAN_EVERY_DEV.md)

---

## TL;DR

Fortunas AI berubah dari *alat analitik untuk UMKM* → *satu aplikasi 2 peran (Customer + UMKM)* dengan loyalty bertenaga AI. **4 minggu ke depan (29 Jun – 24 Jul)** kita bangun **fondasinya** (8 fitur MVP) untuk submit MIS Grant. Fitur loyalty penuh (poin, promo, notifikasi) menyusul di **v5.1 setelah submit**.

---

## 📊 Status Aktual (per 26 Juni 2026)

> Dikerjakan lebih awal dari window 29 Jun (estafet ahead-of-schedule). **4 PR sudah merged ke `main`.** Status: ✅ selesai · 🟡 sebagian · ❌ belum.

**Yang sudah selesai & merged ke `main`:**

| Tahap | Pekerjaan | PR / commit |
|---|---|---|
| Day 1 | Kontrak API (Pydantic `schemas.py` + `API_CONTRACTS.md`) + CI (ruff/pytest) + PR template | #1, #2 |
| Day 2 | PostgreSQL foundation (SQLAlchemy 2.0 + Alembic, **7 tabel** termasuk skema customer/DPA/device) | #3 (`345b667`) |
| Day 3 | **DPA "pagar AI" backend** — guardrail deterministik Pre+Post + `GET/PUT /umkm/dpa` + inject prompt | #4 (`5d28ecd`) |
| — | Rapikan handoff day-03 (doc) | #5 |
| Day 4 | **Customer JWT + QR identity backend** — bootstrap (Firebase seam) + QR signed 90s single-use + scan→auto-membership | #7 |
| Day 9 (slice 1) | **Briefing 5-analisis UI** — tampilkan semua 5 analisis incl. `top_product`; layout 2-col + kartu ganjil full-width (`pairRows`); identitas flame/warning | PR #13 |

**8 Fitur MVP — peta done/belum:**

| Fitur MVP | Status | Catatan |
|---|---|---|
| 1. Login UMKM + HTTPS | 🟡 sebagian | Auth backend ✅ + **layar Login/Register Flutter ✅ (auth gate + token secure-storage + Profile akun) — PR #10**. Belum: HTTPS/domain VPS |
| 2. PostgreSQL | ✅ selesai | PR #3. Cutover Postgres prod (smoke asli) masih nunggu kredensial |
| 3. Customer login HP + OTP | 🟡 sebagian | Backend bootstrap + Firebase seam ✅ (Day 4, dev stub `FORTUNAS_DEV_AUTH=1`). **Belum:** Firebase real wiring + 3 layar mobile |
| 4. QR identitas customer | 🟡 backend ✅ | **Backend SELESAI (Day 4, PR #7)**: QR signed 90s single-use + `POST /customer/qr/session`. Sisa: render QR di mobile |
| 5. Scan QR → auto-member | 🟡 backend ✅ | **Backend SELESAI (Day 4, PR #7)**: `POST /umkm/customer/scan/validate` + auto-membership. Sisa: scanner UI mobile |
| 6. Checkout nyambung customer | 🟡 backend ✅ | **Backend SELESAI (Day 5, PR #8)**: POST /checkout/confirm multi-item + opt-in QR loyalty link (best-effort SETELAH sale). Sisa: UI mobile + kolom BQ enriched |
| 7. DPA jadi "pagar" AI | ✅ selesai | **Backend SELESAI (PR #4)** + **UI mobile DPA (view+edit, chip editor, password confirm) — PR #12** |
| 8. Analisis `top_product` | ✅ selesai | **SELESAI (Day 6, PR #9)**: analisis ke-5 — produk terlaris rank by **omzet** (+ `total_qty` per baris), intent routing (guard vs bundle), prompt+RAG+fallback parity, briefing jadi 5 analisis. 100% credential-free |

**Fondasi yang sudah berdiri (JANGAN rebuild):** v4.0 (FastAPI multi-tenant, auth UMKM bcrypt+JWT, Gemini 2.5 Flash + RAG + 4 analisis, Flutter skeleton, React demo) + kontrak API + CI + PostgreSQL + DPA backend.

**Berikutnya (credential-free, urutan saran):** ~~Customer JWT + QR identity backend (#4/#5)~~ ✅ **Day 4 (PR #7)** → ~~checkout endpoint (#6)~~ ✅ **Day 5 (PR #8)** → ~~analisis `top_product` (#8)~~ ✅ **Day 6 (PR #9)** → ~~UI mobile Login UMKM (#1)~~ ✅ **(PR #10)** → ~~UI mobile DPA (#7)~~ ✅ **(PR #12)** → ~~Briefing 5-analisis UI~~ ✅ **(PR #13, Day 9 slice 1)**. Semua backend credential-free selesai. UI mobile (customer/QR) = track Flutter terpisah.

---

## 🧭 Legend status

| Simbol | Arti |
|---|---|
| ✅ | Sudah ada / selesai |
| 🔨 | Dikerjakan di MVP (29 Jun – 24 Jul) |
| 🕒 | Ditunda ke v5.1 (setelah submit) |
| 🔮 | Visi jangka panjang |

---

## 📍 Posisi sekarang — v4.0 (Juni 2026)

Yang **sudah berdiri** (jangan dibangun ulang):

- ✅ Backend FastAPI multi-tenant — BigQuery tabel per tenant, `TenantContext` dari JWT
- ✅ Auth UMKM email/password (bcrypt + JWT) — **dipakai web demo React**
- ✅ LLM **Gemini 2.5 Flash** (`app/llm_provider.py`) + RAG (ChromaDB) + **4 analisis** (repeat_customer, high_value_customer, peak_hour, bundle_opportunity)
- ✅ Aplikasi **Flutter** — kerangka layar (home, briefing, history, profile) + alur voice transaction
- ✅ Web demo React — sudah login/ask/voice

Yang **belum ada** (jadi target MVP): login di aplikasi HP, database produksi (PostgreSQL), seluruh sisi Customer, QR, DPA guardrail.

---

## 🗓️ Timeline ringkas

```
 SEKARANG         MINGGU 1         MINGGU 2          MINGGU 3          MINGGU 4
 v4.0 ✅    ──►   Fondasi    ──►   Customer + QR ──► DPA + Analitik ─► Polish + SUBMIT 🎯
 (29 Jun)         (s/d 03 Jul)     (s/d 10 Jul)      (s/d 17 Jul)      (24 Jul)
                  tag v5.0-w1      tag v5.0-w2       tag v5.0-w3       tag v5.0-mvp
 │                                                                          │
 └────────────────────── MVP — 4 minggu (8 fitur fondasi) ─────────────────┘
                                                                            │
                                                          v5.1 🕒 ──► v6+ 🔮
                                                   (poin, promo, FCM,   (poin universal,
                                                    9 analisis lain)     coalition, dll)
```

---

## 🔨 FASE MVP — 29 Juni s/d 24 Juli 2026

Model kerja: **3 dev rotasi/estafet per hari** (A→B→C). Tiap akhir hari wajib tulis catatan di [`docs/handoff/`](./handoff/). Detail per hari ada di [`PLAN_EVERY_DEV.md`](./PLAN_EVERY_DEV.md).

### Minggu 1 — Fondasi (Hari 1–5) → `v5.0.0-week1`
**Tujuan:** server siap, aplikasi UMKM bisa login.

| Fitur MVP | Isi |
|---|---|
| 🟡 **1. Login UMKM + HTTPS** | Auth backend ✅ (v4.0). Belum: layar login/register Flutter, token storage, HTTPS/domain di VPS |
| ✅ **2. PostgreSQL** | Migrasi SQLite → Postgres, Alembic, 7 tabel — **selesai (PR #3)** |
| 🔨 *(mulai)* Customer bootstrap | Endpoint backend untuk akun customer |

### Minggu 2 — Customer Auth + QR (Hari 6–10) → `v5.0.0-week2`
**Tujuan:** customer bisa daftar, punya QR, dan transaksinya tercatat.

| Fitur MVP | Isi |
|---|---|
| 🔨 **3. Customer login HP + OTP** | Firebase Phone Auth, 3 layar (HP → OTP → profil) |
| 🔨 **4. QR identitas customer** | Token QR aman 90 detik + render di app |
| 🔨 **5. Scan QR → auto-member** | Scanner UMKM + validasi + buat membership |
| 🔨 **6. Checkout nyambung customer** | Kolom BQ `CustomerUserID`/`TenantID`, riwayat lintas-toko |

### Minggu 3 — DPA + Analitik (Hari 11–15) → `v5.0.0-week3`
**Tujuan:** AI patuh aturan toko + 1 analisis baru.

| Fitur MVP | Isi |
|---|---|
| ✅ **7. DPA jadi "pagar" AI** | Backend ✅ **selesai (PR #4)**: simpan DPA, cek deterministik Pre+Post, inject prompt. **UI mobile DPA SELESAI (PR #12)**: layar view+edit, chip editor, password confirm inline. |
| ✅ **8. Analisis `top_product`** | **SELESAI (Day 6, PR #9)** — produk terlaris rank by **omzet** (+ `total_qty`/baris), briefing jadi 5 analisis |
| 🔨 Polish + E2E test | Uji alur penuh UMKM & Customer |

### Minggu 4 — Polish + Submission (Hari 16–20) → `v5.0.0-mvp-submission`
**Tujuan:** zero bug critical, dokumentasi, build APK, **submit ke MIS Grant**.

- 🔨 Fix bug + rate limiting + audit keamanan
- 🔨 Build APK release + test di device fisik
- 🔨 Dokumentasi (README, guide, demo script) + rekam demo
- 🎯 **SUBMIT** (Hari 20, Dev B + C kerja bareng)

---

## 🕒 SETELAH SUBMIT — v5.1 (backlog prioritas)

Fitur ini **sengaja ditunda** dari MVP (tenaga 3 dev terbatas). Urutan saran:

1. 🕒 **Points ledger + saldo poin** (fondasi loyalty)
2. 🕒 **Promo generator + spin wheel** ← fitur paling "wow" untuk demo *(pertimbangkan versi tipis masuk MVP — lihat catatan keputusan)*
3. 🕒 **FCM push notification** (briefing pagi, promo belum dipakai)
4. 🕒 **Scheduler briefing per-tenant**
5. 🕒 **9 analisis sisanya** (revenue_trend, customer_segmentation, churn_risk, slow_moving, demand_forecast, average_basket, inventory_alert, price_sensitivity, promo_effectiveness)
6. 🕒 Dark theme, verifikasi email edit DPA, Whisper STT, mode offline

---

## 🔮 VISI JANGKA PANJANG — v6+

- 🔮 **Poin universal lintas-UMKM** dengan model settlement (coalition loyalty — operator pegang ledger & liability)
- 🔮 Promo effectiveness analytics (butuh data redemption real dulu)
- 🔮 Inventory management (butuh tabel stok)
- 🔮 Cloud Scheduler + Cloud Tasks, Secret Manager, observability (Sentry)

---

## 🔑 Keputusan & prinsip kunci (wajib semua tim tahu)

1. **GitHub = sumber kebenaran.** Kalau proposal lama vs kode berbeda → ikuti kode di `main`.
2. **LLM = Gemini** (bukan Qwen3 lokal). ⚠️ Ini bertentangan dengan klaim "LLM lokal / data tidak keluar server (UU PDP)" di proposal → **narasi paper perlu diredaksi**.
3. **Pemisahan data:** BigQuery = analitik & histori transaksi · PostgreSQL = state aplikasi (akun, poin, promo). Jangan campur.
4. **DPA bukan sekadar teks di prompt** — harus dicek deterministik di kode sebelum panggil Gemini (prompt saja tidak cukup aman).
5. **Jaga alur lama jangan rusak** — checkout/voice existing tetap jalan; scan customer bersifat opsional dulu.

### Default yang masih perlu dikonfirmasi tim
*(rincian + alasan ada di dokumen rekomendasi keputusan bisnis)*

| Topik | Usulan default |
|---|---|
| Cara dapat poin | Per rupiah (mis. 1 poin / Rp 10.000) |
| Masa berlaku QR | 90 detik, sekali pakai |
| Masa berlaku promo | 7 hari |
| Min. poin untuk promo | Kalibrasi vs nilai spin (±Rp 22.250/promo) |
| Scan checkout | Opsional dulu (hanya untuk poin/promo) |
| Pembagian Dev A/B/C | **Belum dipetakan** → tentukan siapa |

---

## 📚 Dokumen terkait

- [`PLAN_EVERY_DEV.md`](./PLAN_EVERY_DEV.md) — rencana detail per hari (20 hari)
- [`docs/handoff/`](./handoff/) — catatan estafet harian
- [`FORTUNAS_REQUIREMENTS_UPDATE.md`](./FORTUNAS_REQUIREMENTS_UPDATE.md) — requirements penuh (visi lengkap)
- `README.md` — status teknis & cara setup
