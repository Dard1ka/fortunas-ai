# Fortunas AI — Plan Rotasi 3 Developer (Estafet Harian)

> **Model:** 3 developer bekerja **bergantian per hari** (relay/estafet)
> **Periode:** 20 hari kerja (4 minggu), Senin 2026-06-29 → Jumat 2026-07-24
> **Throughput total:** 20 person-days (vs 60 jika paralel)
> **Submit:** Jumat 2026-07-24

---

## ⚠️ PERINGATAN PENTING tentang Model Rotasi

### Trade-off yang Harus Diterima
**Pro:**
- Setiap dev fokus 1 hari penuh (deep work tanpa interupsi)
- Tidak ada merge conflict (cuma 1 dev push per hari)
- Cocok kalau dev punya kesibukan lain di hari lain
- Cocok untuk dev yang baru belajar — handoff = belajar dari kerja teman

**Kontra:**
- **Total throughput = 1/3 dari model paralel** (20 person-days vs 60)
- **Handoff overhead** 30–60 menit/hari (baca catatan dev kemarin, pull branch, run setup)
- **Context switch cost** — dev hari ini mungkin baru ingat code 3 hari lalu yang dia tulis
- **Bug discovered late** — dev kemarin sudah pulang, dev hari ini harus fix sendiri
- **Setiap dev harus full-stack** — tidak bisa specialize backend-only / mobile-only

### Konsekuensi Scope
**Scope MVP dipangkas dari 8 fitur jadi 5 fitur:**

| Fitur | Paralel 3-Dev | Rotasi 3-Dev |
|---|---|---|
| Mobile UMKM auth + HTTPS | ✅ | ✅ |
| PostgreSQL migration | ✅ | ✅ |
| Customer phone OTP + QR | ✅ | ✅ |
| Checkout dengan customer link | ✅ | ✅ |
| DPA basic (text only, tanpa AI guardrail) | ✅ | ⚠️ Simplified |
| Points ledger + balance | ✅ | ❌ DROP |
| Promo generator + spin wheel | ✅ | ❌ DROP |
| FCM push notification | ✅ | ❌ DROP |
| 3 analisis baru | ✅ | ⚠️ Hanya 1 (`top_product`) |

**Kalau scope penuh tetap dipaksakan dalam 4 minggu rotasi → tidak akan selesai.** Plan ini fokus pada **MVP minimum demonstrable** untuk MIS Grant submission.

---

## 👥 Jadwal Rotasi 20 Hari

Pola: **A → B → C → A → B → C → ...**

| Hari | Tanggal | Dev | Hari | Tanggal | Dev |
|---|---|---|---|---|---|
| 1 | Sen 06-29 | **A** | 11 | Sen 07-13 | **B** |
| 2 | Sel 06-30 | **B** | 12 | Sel 07-14 | **C** |
| 3 | Rab 07-01 | **C** | 13 | Rab 07-15 | **A** |
| 4 | Kam 07-02 | **A** | 14 | Kam 07-16 | **B** |
| 5 | Jum 07-03 | **B** | 15 | Jum 07-17 | **C** |
| 6 | Sen 07-06 | **C** | 16 | Sen 07-20 | **A** |
| 7 | Sel 07-07 | **A** | 17 | Sel 07-21 | **B** |
| 8 | Rab 07-08 | **B** | 18 | Rab 07-22 | **C** |
| 9 | Kam 07-09 | **C** | 19 | Kam 07-23 | **A** |
| 10 | Jum 07-10 | **A** | 20 | Jum 07-24 | **B + C** |

**Total hari per dev:** Dev A = 7 hari · Dev B = 7 hari · Dev C = 6 hari
**Submission Day (Hari 20):** Dev B + C kerja bareng (1 hari special) untuk packaging & submit

---

## 📝 Handoff Protocol (WAJIB Setiap Akhir Hari)

Sebelum logout, dev hari ini **WAJIB** tulis `docs/handoff/day-XX.md`:

```markdown
# Handoff Day XX → Day XX+1

**Dev hari ini:** [nama]
**Dev besok:** [nama]

## ✅ Selesai hari ini
- [task 1 dengan branch + commit hash]
- [task 2]

## ⏳ Belum selesai (untuk besok)
- [task X — sudah jalan ke step Y, file di branch `feat/...`]

## 🔴 Blocker / Bug ditemukan
- [bug 1: gejala + langkah reproduksi + dugaan penyebab]

## 📦 State branch
- Current: `feat/...`
- Push terakhir: [hash + waktu]
- PR open: [link kalau ada]

## 🎯 Goal besok
- [goal jelas yang harus dicapai dev besok]

## 📌 Catatan tambahan
- [credential/config baru kalau ada]
- [decision yang diambil + alasan]
```

**Jam pagi (09:00–09:30) hari berikutnya:** Dev baru WAJIB:
1. Baca `docs/handoff/day-XX.md`
2. `git pull` + checkout branch yang sedang aktif
3. Run setup local (`pip install`, `flutter pub get` kalau perlu)
4. Smoke test current state
5. **Baru mulai coding goal hari ini**

---

## 🛠 Tools & Layanan (Setiap Dev Harus Install)

Karena rotasi, **SEMUA dev harus full-stack**. Tools wajib di laptop masing-masing:

### Lokal
| Tool | Tujuan | Wajib? |
|---|---|---|
| **Python 3.12** | Backend | ✅ |
| **Flutter SDK 3.27+** | Mobile | ✅ |
| **Node 20+** | Frontend React (kalau perlu cek) | ✅ |
| **PostgreSQL 15** atau Docker | DB lokal | ✅ |
| **Git + GitHub CLI (`gh`)** | Version control | ✅ |
| **VS Code** + extensions: Python, Dart, Flutter, GitLens | Editor | ✅ |
| **Android Studio + AVD** | Test mobile | ✅ |
| **DBeaver** | DB GUI | ✅ |
| **Postman / Bruno** | API testing | ✅ |
| **Chrome / Edge** | Frontend test + Web Speech API | ✅ |

### Akun & Akses
| Layanan | Untuk | Siapa Akses |
|---|---|---|
| **GitHub repo Fortunas AI** | Code + Issue + PR | Semua 3 dev |
| **VPS Ubuntu (SSH)** | Deploy backend | Semua 3 dev (key per orang) |
| **Firebase Console** project `fortunas-ai-mobile` | Phone Auth + FCM | Semua 3 dev sebagai admin |
| **Google Cloud Console** project `fortunasai` | BigQuery + service account | Semua 3 dev sebagai editor |
| **Gemini API key** | LLM call | Backend `.env` (shared) |
| **Domain registrar** atau **DuckDNS** | HTTPS domain | Dev yang setup (Hari 3) |
| **Slack/WhatsApp grup** | Komunikasi async | Semua 3 dev |

### Library yang Akan Dipakai
**Backend (pip):** `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `psycopg2-binary`, `pydantic`, `bcrypt`, `PyJWT`, `firebase-admin`, `google-cloud-bigquery`, `chromadb`, `sentence-transformers`, `requests`

**Mobile (pubspec):** `flutter_riverpod`, `go_router`, `dio`, `flutter_secure_storage`, `firebase_core`, `firebase_auth`, `qr_flutter`, `mobile_scanner`, `permission_handler`, `speech_to_text`, `google_fonts`, `intl`

---

# 📅 DETAIL PER HARI

## MINGGU 1 — Foundation (Hari 1–5)

---

### 🗓 Hari 1 (Sen 2026-06-29) — Dev A
**Goal:** Repo siap, branching strategy aktif, kontrak API ditulis, Dev B & C tahu apa yang harus dilanjutkan.

**Tools dipakai:** Git + GitHub CLI · VS Code · `gh repo edit` · OpenSSL (generate JWT secret)

**Steps:**
1. Setup repo: buat branch `dev`, branch protection rules untuk `main` di GitHub Settings
2. Tulis PR template `.github/pull_request_template.md` dengan checklist
3. Setup CI workflow `.github/workflows/ci.yml` — ruff (Python lint) + `flutter analyze` + pytest smoke
4. Tulis SEMUA kontrak Pydantic baru di `app/schemas.py`:
   - `CustomerBootstrapRequest/Response`
   - `QRSessionResponse`, `QRValidateRequest/Response`
   - `CheckoutConfirmRequest/Response`
   - `DPAPayload`, `DeviceTokenRequest`
5. Translate ke `mobile/lib/api/models.dart` (DTO Dart matching)
6. Tulis `docs/API_CONTRACTS.md` — daftar semua endpoint + payload sample curl
7. Tulis `docs/handoff/day-01.md` (handoff ke Dev B)

**Deliverable:** Branch `feat/foundation-contracts` merged ke `dev`

---

### 🗓 Hari 2 (Sel 2026-06-30) — Dev B
**Goal:** PostgreSQL siap lokal + di VPS, schema auth termigrasi.

**Tools dipakai:** PostgreSQL 15 · DBeaver · `alembic` · `psycopg2` · SSH ke VPS · Git

**Steps:**
1. Baca `docs/handoff/day-01.md`, pull branch `dev`
2. Install PostgreSQL 15 lokal + DBeaver
3. Buat database `fortunas_app_dev` + user `fortunas_app`
4. Update `requirements.txt`: `psycopg2-binary`, `sqlalchemy>=2.0`, `alembic`
5. Buat `app/db_pg.py` — SessionLocal factory + base
6. `alembic init app/migrations`, config DB URL
7. Migration 001: `tenants`, `tenant_users`, `tenant_settings`
8. Tulis `scripts/migrate_sqlite_to_pg.py` — copy data SQLite → Postgres
9. Refactor `app/db.py` jadi wrapper Postgres
10. Smoke test: register + login UMKM masih jalan lokal
11. SSH ke VPS, install postgresql-15, buat DB production
12. Tulis `docs/handoff/day-02.md` (handoff ke Dev C)

**Deliverable:** Branch `feat/pg-foundation` merged ke `dev`

---

### 🗓 Hari 3 (Rab 2026-07-01) — Dev C
**Goal:** HTTPS aktif di VPS + skema operational state lengkap di Postgres.

**Tools dipakai:** SSH · certbot · nginx · DuckDNS (atau domain registrar) · Alembic

**Steps:**
1. Baca handoff Hari 2, pull branch
2. Setup domain: pakai DuckDNS gratis (`fortunas.duckdns.org`) atau beli `.com`
3. Update DNS A record → IP VPS
4. SSH VPS, install certbot: `apt install certbot python3-certbot-nginx`
5. Update `/etc/nginx/sites-available/fortunas` dengan domain
6. Run `certbot --nginx -d fortunas.duckdns.org` → auto-config SSL
7. Test endpoint via HTTPS: `curl https://fortunas.duckdns.org/health`
8. Rotate `GEMINI_API_KEY` (generate di Google AI Studio), update `.env` lokal + VPS
9. Set repo GitHub jadi private
10. Migration 002: `customer_users`, `customer_tenant_memberships`
11. Migration 003: `tenant_dpa_policies`, `device_tokens`
12. Index strategis: `firebase_uid`, `phone_number`
13. Repository skeleton: `customer_repo.py`, `dpa_repo.py`
14. Tulis `docs/handoff/day-03.md` (handoff ke Dev A)

**Deliverable:** HTTPS live + branch `feat/pg-app-state` merged

---

### 🗓 Hari 4 (Kam 2026-07-02) — Dev A
**Goal:** Mobile UMKM bisa login + register dari Flutter, terhubung HTTPS VPS.

**Tools dipakai:** Flutter · Android Studio emulator · Postman · `flutter_secure_storage`

**Steps:**
1. Baca handoff Hari 3, pull branch
2. Update `mobile/pubspec.yaml`: tambah `flutter_secure_storage`, `dio` interceptor
3. Buat `mobile/lib/auth/auth_store.dart` — wrapper secure storage
4. Buat `mobile/lib/auth/auth_provider.dart` — Riverpod state
5. Refactor `mobile/lib/api/client.dart` — Dio interceptor auto-Bearer + auto-401-logout
6. Tambah method `register/login/me` di `client.dart`
7. `mobile/lib/screens/auth/login_screen.dart` — form email + password
8. `mobile/lib/screens/auth/register_screen.dart` — form business_name, email, password
9. Validasi client-side + error humanizer Bahasa Indonesia
10. Update `mobile/lib/app.dart` — go_router redirect ke `/login` kalau token kosong
11. Test register baru di HTTPS VPS via Android emulator
12. Test login + logout flow
13. Tulis `docs/handoff/day-04.md`

**Deliverable:** Branch `feat/mob-umkm-auth` merged

---

### 🗓 Hari 5 (Jum 2026-07-03) — Dev B
> **✅ Aktual (ahead-of-schedule):** `feat/checkout-confirm` — POST /checkout/confirm multi-item + opt-in QR loyalty link (best-effort SETELAH sale). 19 test baru (suite 125 hijau), BQ di balik seam lazy (default-safe), nol dep CI baru.

**Goal:** Polish mobile UMKM + customer bootstrap endpoint backend siap.

**Tools dipakai:** Flutter · firebase-admin Python · Postman

**Steps:**
1. Baca handoff Hari 4, pull branch
2. Test register UMKM di production VPS HTTPS — pastikan no regression
3. Profile screen UMKM: show `tenant_name`, `email`, `table_prefix` dari `/auth/me`
4. Logout button + redirect ke `/login`
5. Fix UX bugs hasil E2E
6. **Switch ke backend:** install `firebase-admin` Python SDK
7. Buat `app/core/firebase_auth.py` — `verify_id_token()` wrapper (return uid + phone)
8. Endpoint skeleton `app/api/routes/customer_auth.py`:
   - `POST /customer/auth/bootstrap` — verify Firebase ID token → upsert `customer_users` → return internal JWT
9. Endpoint `GET /customer/me`, `PUT /customer/me`
10. **Deploy backend ke VPS** + smoke test
11. **Merge `dev` → `main`, tag `v5.0.0-week1`**
12. Tulis `docs/handoff/day-05.md` (handoff ke Dev C minggu depan)

**Deliverable:** Release `v5.0.0-week1` + customer auth endpoint live

---

## MINGGU 2 — Customer Auth + QR (Hari 6–10)

> **✅ Aktual (ahead-of-schedule, 2026-06-26):** Mobile Login UMKM (fitur #1 — layar Flutter) selesai sebagai dedicated session sebelum window Minggu 2. Auth backend sudah merged (v4.0); sesi ini menambahkan layar Login/Register Flutter, auth gate (go_router redirect), token secure-storage, Dio interceptor auto-Bearer + auto-401-logout, dan Profile akun (tampil `tenant_name` + email + Keluar). 26 test hijau, analyze bersih. PR #10. QR-mobile (fitur #3–#5 sisi layar) tetap di jadwal Minggu 2.

---

### 🗓 Hari 6 (Sen 2026-07-06) — Dev C
**Goal:** Firebase project siap, mobile customer phone OTP flow jalan.

**Tools dipakai:** Firebase Console · Flutter · `firebase_core`, `firebase_auth`

**Steps:**
1. Baca handoff Hari 5
2. Buat Firebase project `fortunas-ai-mobile` di console
3. Enable Phone Authentication + Cloud Messaging
4. Tambah app Android — download `google-services.json` → `mobile/android/app/`
5. Tambah app iOS — download `GoogleService-Info.plist` → `mobile/ios/Runner/`
6. Place service account JSON di `credentials/firebase-admin.json` (gitignored)
7. Update `mobile/pubspec.yaml`: tambah `firebase_core`, `firebase_auth`
8. Init Firebase di `mobile/lib/main.dart`
9. `mobile/lib/screens/customer/phone_login_screen.dart` — input HP (+62)
10. `mobile/lib/screens/customer/otp_verify_screen.dart` — 6-digit OTP + resend timer
11. `mobile/lib/screens/customer/complete_profile_screen.dart` — username + birth_date
12. Test flow phone OTP di emulator pakai nomor Firebase test
13. Wire ke `/customer/auth/bootstrap` (endpoint Dev B Hari 5)
14. Tulis `docs/handoff/day-06.md`

**Deliverable:** Branch `feat/mob-customer-otp` merged

---

### 🗓 Hari 7 (Sel 2026-07-07) — Dev A
**Goal:** QR session backend ditulis, customer QR identity screen render.

**Tools dipakai:** Python `PyJWT` · Flutter · `qr_flutter`

**Steps:**
1. Baca handoff Hari 6
2. `app/services/qr_service.py` — sign/verify JWT 2 menit (claims: `customer_user_id`, `nonce`, `type=identity`)
3. Endpoint `POST /customer/qr/session` — return payload + expires_at
4. Unit test QR: sign → verify → expired → tampered scenarios
5. Update `mobile/pubspec.yaml`: tambah `qr_flutter`
6. `mobile/lib/screens/customer/qr_identity_screen.dart`:
   - Fetch `/customer/qr/session`
   - Render QR besar
   - Countdown timer 90s, auto-refresh sebelum expire
7. Test customer login → buka QR screen → QR render
8. Tulis `docs/handoff/day-07.md`

**Deliverable:** Branch `feat/qr-identity` merged

---

### 🗓 Hari 8 (Rab 2026-07-08) — Dev B
**Goal:** UMKM bisa scan QR customer, validate ke backend.

**Tools dipakai:** Flutter · `mobile_scanner` · `permission_handler` · Postman

**Steps:**
1. Baca handoff Hari 7
2. Update `mobile/pubspec.yaml`: tambah `mobile_scanner`, `permission_handler`
3. Permission camera di `mobile/android/app/src/main/AndroidManifest.xml`
4. `mobile/lib/screens/umkm/scan_customer_screen.dart` — camera scanner UI
5. On detect → POST `/umkm/customer/scan/validate`
6. **Backend:** Endpoint `POST /umkm/customer/scan/validate`:
   - Verify QR token
   - Cek `customer_tenant_memberships` — auto-insert kalau first visit
   - Return customer profile + membership status
7. Show customer info card setelah scan sukses
8. Error handling: QR expired, invalid, no camera
9. Test scan di device fisik (camera tidak jalan di emulator)
10. Tulis `docs/handoff/day-08.md`

**Deliverable:** Branch `feat/scan-customer` merged

---

### 🗓 Hari 9 (Kam 2026-07-09) — Dev C
**Goal:** Checkout endpoint enriched + voice flow integrate scan.

**Tools dipakai:** Python · `google-cloud-bigquery` · Flutter

**Steps:**
1. Baca handoff Hari 8
2. **Backend:** Update `POST /checkout/confirm`:
   - Terima optional `customer_qr_token`
   - Verify QR
   - Auto-create membership kalau first visit
   - Insert ke BQ `{prefix}_transactions` dengan kolom enriched
3. Script `scripts/bq_add_columns.py` — ALTER ADD COLUMN `CustomerUserID STRING`, `TenantID INT64`, `CheckoutSource STRING` di tabel tenant existing
4. Run script di staging BQ
5. Update `app/services/wa_pipeline_structured.py` untuk include kolom baru
6. **Mobile:** Update `mobile/lib/voice/voice_parsed.dart`:
   - Tambah tombol "Scan Pelanggan" sebelum confirm
   - Bottom sheet scan flow
   - Attach `customer_qr_token` ke payload
   - Show badge "Member sejak..." setelah scan
7. Test E2E: voice transaction + customer scan → BQ insert dengan customer link
8. Tulis `docs/handoff/day-09.md`

**Deliverable:** Branch `feat/checkout-integration` merged

---

### 🗓 Hari 10 (Jum 2026-07-10) — Dev A
**Goal:** Customer home + history endpoint + UI lengkap.

**Tools dipakai:** Python · BigQuery · Flutter

**Steps:**
1. Baca handoff Hari 9
2. **Backend:**
   - `GET /customer/transactions?limit=20&cursor=...` — query BQ lintas tenant `WHERE CustomerUserID = ?`
   - Aggregate per UMKM
   - `GET /customer/home` — UMKM visited + last_tx + placeholder fields
3. **Mobile:**
   - `customer/home_screen.dart` — kartu summary
   - `customer/history_screen.dart` — list grouped per UMKM
   - `customer/customer_bottom_nav.dart` — 5 tab (Beranda, History, Scan, Profile + placeholder Points)
   - Pull-to-refresh + loading skeleton + empty state
4. Test customer journey: login → scan UMKM A → checkout → cek history customer
5. **Deploy backend ke VPS** + smoke test production
6. **Merge `dev` → `main`, tag `v5.0.0-week2`**
7. Tulis `docs/handoff/day-10.md`

**Deliverable:** Release `v5.0.0-week2`

---

## MINGGU 3 — DPA + Analisis + E2E Polish (Hari 11–15)

---

### 🗓 Hari 11 (Sen 2026-07-13) — Dev B
**Goal:** DPA backend siap, jadi prompt constraint untuk Gemini.

**Tools dipakai:** Python · Alembic · Postman

**Steps:**
1. Baca handoff Hari 10
2. Endpoint `GET /umkm/dpa` — return current dari `tenant_dpa_policies`
3. Endpoint `PUT /umkm/dpa` — pakai password confirm (bukan email OTP untuk MVP simplified)
4. Update `app/prompt_builder.py`:
   - Kalau `tenant.dpa_policy` ada → prepend HARD CONSTRAINT block sebelum RAG context
   - Format: "ATURAN WAJIB DARI BISNIS: [raw_text]. Jangan rekomendasi yang melanggar."
5. Smoke test: register tenant → isi DPA "tidak jual rokok" → ask "promo rokok" → AI refuse
6. Tulis `docs/handoff/day-11.md`

**Deliverable:** Branch `feat/dpa-backend` merged

---

### 🗓 Hari 12 (Sel 2026-07-14) — Dev C
**Goal:** DPA UI di mobile UMKM (onboarding + edit).

**Tools dipakai:** Flutter

**Steps:**
1. Baca handoff Hari 11
2. `umkm/dpa_onboarding_screen.dart` — tampil first login UMKM kalau DPA kosong (force fill)
3. Field: `raw_text` textarea besar, `allowed_rules` chips input, `forbidden_rules` chips input
4. `umkm/dpa_edit_screen.dart` — di profile menu, modal password confirm sebelum simpan
5. Show DPA summary di profile screen (preview 2 baris)
6. Test DPA flow E2E: register UMKM → onboarding tampil → fill → simpan → verifikasi di backend
7. Test edit dari profile → password confirm → simpan
8. Tulis `docs/handoff/day-12.md`

**Deliverable:** Branch `feat/dpa-ui` merged

---

### 🗓 Hari 13 (Rab 2026-07-15) — Dev A
**Goal:** Analisis baru `top_product` siap dipakai di briefing.

> ✅ **SELESAI (Day 6, 2026-06-26, ahead-of-schedule).** Implementasi final ≠ sketsa di bawah: SATU analisis rank by **omzet** (`ORDER BY total_omzet DESC`) dengan `total_qty` per baris (bukan 2 list qty+revenue terpisah). Label "Analisis Produk Terlaris". Termasuk fallback parity di `llm_service.py` + 12 unit test baru (queries/registry/intent/prompt/briefing). Detail: spec `Fortunas/brainstorming/specs/2026-06-26-top-product-analysis-design.md`.

**Tools dipakai:** Python · BigQuery · `/ask` endpoint testing

**Steps:**
1. Baca handoff Hari 12
2. SQL builder `_top_product_sql(tx)` di `app/queries.py`:
   - SUM(Quantity) per Description (top 10 by qty)
   - SUM(Quantity*Price) per Description (top 10 by revenue)
   - Output: 2 list dalam satu response
3. Entry di `app/analysis_registry.py`:
   ```python
   "top_product": {"label": "Analisis Produk Paling Laku", "enabled": True}
   ```
4. Intent rules di `app/intent_mapper.py`:
   - `strong_phrases`: "produk paling laku", "best seller", "barang sering keluar", "barang paling laris"
   - `keywords`: "laku", "best seller", "laris", "paling banyak terjual"
5. Cabang prompt builder kalau dibutuhkan struktur khusus
6. Test via `/ask`: "produk apa yang paling laku bulan ini?"
7. Update briefing untuk include 5 analisis (4 lama + 1 baru)
8. Tulis `docs/handoff/day-13.md`

**Deliverable:** Branch `feat/analysis-top-product` merged

---

### 🗓 Hari 14 (Kam 2026-07-16) — Dev B
**Goal:** Briefing UI update untuk 5 analisis + customer onboarding flow.

**Tools dipakai:** Flutter

**Steps:**
1. Baca handoff Hari 13
2. Update `briefing_screen.dart` Flutter — handle 5 analisis (4 lama + 1 baru) layout grid
3. Card visual berbeda dengan icon per analisis type
4. Pull-to-refresh trigger ulang briefing
5. Welcome flow first-time customer (onboarding cards 3 layar)
6. Error states konsisten Bahasa Indonesia di semua screen customer
7. Loading skeleton + empty state polish
8. Test customer cold start performance
9. Tulis `docs/handoff/day-14.md`

**Deliverable:** Branch `feat/briefing-customer-polish` merged

---

### 🗓 Hari 15 (Jum 2026-07-17) — Dev C
**Goal:** Week 3 deploy + comprehensive E2E test.

**Tools dipakai:** SSH · Postman · Android device fisik

**Steps:**
1. Baca handoff Hari 14
2. Deploy backend ke VPS, restart systemd
3. E2E test full UMKM journey:
   - Register UMKM baru → BQ tables auto-created
   - Onboarding DPA → fill
   - Ask question respect DPA
   - Briefing 5 analisis muncul
4. E2E test full customer journey:
   - Register phone OTP → complete profile → home
   - Scan UMKM A → membership created
   - Voice transaction → checkout
   - History customer tampil
5. Catat bug di `docs/bugs-week3.md`
6. **Merge `dev` → `main`, tag `v5.0.0-week3`**
7. Tulis `docs/handoff/day-15.md`

**Deliverable:** Release `v5.0.0-week3` + bug list

---

## MINGGU 4 — Bug Fix + Submission (Hari 16–20)

---

### 🗓 Hari 16 (Sen 2026-07-20) — Dev A
**Goal:** Bug critical & high backend zero, security baseline.

**Tools dipakai:** Python · pytest · slowapi

**Steps:**
1. Baca handoff Hari 15, baca bug list
2. Fix bugs critical + high backend
3. Tambah rate limiting (`slowapi`) di endpoint sensitif:
   - `/auth/login` (5 per menit)
   - `/customer/auth/bootstrap` (3 per menit per IP)
   - `/customer/qr/session` (10 per menit per user)
4. Audit SQL injection guards di semua route baru
5. Cek JWT expiry handling
6. Final smoke test backend
7. Tulis `docs/handoff/day-16.md`

**Deliverable:** Branch `fix/be-bugs` merged

---

### 🗓 Hari 17 (Sel 2026-07-21) — Dev B
**Goal:** Bug critical & high mobile zero, final visual polish.

**Tools dipakai:** Flutter · Android device fisik

**Steps:**
1. Baca handoff Hari 16
2. Fix bugs critical + high mobile
3. Performance: lazy load list panjang, image cache
4. Final konsistensi visual (warna, font, spacing) di semua screen
5. Build release APK debug-mode untuk testing
6. Test APK install di device fisik
7. Tulis `docs/handoff/day-17.md`

**Deliverable:** Branch `fix/mob-bugs` merged

---

### 🗓 Hari 18 (Rab 2026-07-22) — Dev C
**Goal:** Documentation lengkap + demo materi siap.

**Tools dipakai:** VS Code Markdown · OBS Studio (screen recorder) · ReportLab

**Steps:**
1. Baca handoff Hari 17
2. Update `README.md` ke v5.0 — badge, fitur, screenshot
3. Update `memory.md` dengan state terbaru
4. Tulis `CUSTOMER_APP_GUIDE.md` — flow customer untuk user akhir
5. Tulis `UMKM_APP_GUIDE.md` — flow UMKM untuk user akhir
6. Update `DEPLOY.md` dengan PostgreSQL + Firebase setup
7. Update `DEMO_SCRIPT.md` — skenario 10 menit untuk grant demo
8. Record screen capture demo pakai OBS
9. Generate updated PDF overview: `python docs/generate_pdf.py`
10. Tulis `docs/handoff/day-18.md`

**Deliverable:** Branch `docs/v5-release` merged

---

### 🗓 Hari 19 (Kam 2026-07-23) — Dev A
**Goal:** Final E2E test + production hardening.

**Tools dipakai:** Postman · pytest · curl · SSH

**Steps:**
1. Baca handoff Hari 18
2. Run full E2E test di production VPS — semua skenario happy path harus lulus:
   - UMKM register → onboarding DPA → ask → briefing
   - Customer register OTP → scan UMKM → checkout → history
3. Test edge cases: token expired, network loss, double-tap, promo expired, DPA violation
4. Backup database Postgres + dump SQL
5. Verifikasi semua secret tidak ter-commit (`git secret-scan` atau manual cek)
6. Tulis `docs/handoff/day-19.md` (handoff ke Dev B + C untuk submission)

**Deliverable:** Production stable, backup taken

---

### 🗓 Hari 20 (Jum 2026-07-24) — Dev B + Dev C (kerja bareng) 🎉
**Goal:** Submission package terkirim ke MIS Grant.

**Tools dipakai:** Build APK · `pwsh package.ps1` · MIS Grant portal

**Steps Dev B (Mobile build):**
1. Build release APK production: `flutter build apk --release`
2. Build appbundle: `flutter build appbundle --release` (untuk Play Store kalau perlu)
3. Test install APK di device fisik
4. Smoke test full flow di APK release

**Steps Dev C (Backend + Package):**
1. Final smoke test production VPS
2. Tag git: `v5.0.0-mvp-submission` di `main`
3. Package zip: `pwsh ./package.ps1`
4. Verifikasi zip exclude: `.env`, `credentials/`, `.git`, `node_modules`, `.venv`, `chroma_db/`, `HANDOVER.txt`, `CLAUDE.md`
5. Sertakan: APK release, dokumentasi PDF, demo video, README

**Bersama:**
1. Submit ke MIS Grant portal
2. Sertakan link demo + APK + GitHub repo (private invite jury)
3. Celebrate 🥳 + retro singkat
4. Tulis `docs/handoff/day-20.md` sebagai laporan final

**Deliverable:** SUBMITTED ✅

---

## 🎯 Definition of Done (Per Hari)

Sebelum logout, dev hari ini WAJIB ceklis:
- [ ] Branch sudah di-push ke GitHub
- [ ] PR sudah dibuka (atau merged kalau Dev C / final day)
- [ ] Smoke test happy path lulus
- [ ] `docs/handoff/day-XX.md` ditulis lengkap
- [ ] Slack/WA grup di-notify "Day XX done, handoff ready for [nama dev besok]"

## 🚦 Plan B Kalau Hari Terlewat

Skenario: dev hari X sakit / urgent / tidak bisa kerja.

**Aturan triage:**
1. Reschedule rotasi: dev hari X+1 ambil task, hari X-nya digeser 1 hari (semua mundur)
2. Kalau tidak bisa mundur (deadline mepet): trigger Plan B scope cut
3. Plan B cuts (urutan drop):
   - Analisis `top_product` (Hari 13)
   - DPA UI mobile (Hari 12) — backend tetap, UI defer
   - Customer history endpoint detail (Hari 10) — show placeholder dulu
   - Polish hari (Hari 14) — geser ke pasca-submission

## 📋 Standup Async (Setiap Pagi 09:00–09:30)

Karena dev tidak overlap, standup = **baca + balas di Slack thread**:

```
[Day XX] Dev [nama] today.
- Read handoff: ✅
- Pulled branch: ✅
- Setup local: ✅ / ⚠️ [problem]
- Today's goal: [1 kalimat]
- Need help from previous dev? [yes/no, kalau yes: tag dia]
```

Dev kemarin standby 30 menit di Slack untuk jawab pertanyaan dev hari ini.

## 🔑 Akun & Credential Sharing

Karena 3 dev pakai infra yang sama:
- **`.env` file:** simpan di password manager (1Password / Bitwarden) team vault
- **`credentials/*.json`:** sama, di password manager
- **VPS SSH:** setiap dev punya SSH key sendiri, masukin ke `authorized_keys`
- **Firebase + GCP:** invite 3 email sebagai admin/editor
- **GitHub:** 3 collaborator
- **Domain registrar:** 1 admin (Dev A), 2 dev tahu credential via password manager

## 💰 Estimasi Biaya 4 Minggu

| Item | Biaya |
|---|---|
| VPS (sudah ada) | Rp 0 |
| Domain (opsional, DuckDNS free) | Rp 0 atau Rp 150rb |
| Firebase Auth + FCM (Free tier) | Rp 0 |
| Gemini API (Free tier 1500/hari) | Rp 0 |
| BigQuery (Free 1TB/bulan) | Rp 0 |
| GitHub Private (Free under 3 collab) | Rp 0 |
| Password Manager (1Password Family) | Rp ~50rb/bulan = Rp 200rb |
| **Total** | **Rp 200rb–350rb** |

---

## ✅ Acceptance Criteria Akhir Minggu 4

**MVP harus mencapai ini untuk lulus submission:**

- [ ] UMKM bisa register & login via Flutter mobile
- [ ] Customer bisa register phone OTP via Flutter mobile
- [ ] Customer bisa show QR identity (auto-refresh 90s)
- [ ] UMKM bisa scan QR customer untuk auto-register membership
- [ ] Checkout via voice tetap jalan + bisa attach customer
- [ ] BigQuery transaksi punya kolom `CustomerUserID` & `TenantID`
- [ ] Customer bisa lihat riwayat transaksi cross-UMKM
- [ ] UMKM bisa fill DPA (text)
- [ ] DPA jadi constraint AI di `/ask`
- [x] Briefing punya 5 analisis (4 lama + `top_product`)
- [ ] Backend HTTPS aktif dengan domain
- [ ] APK release build terinstall di device fisik
- [ ] Dokumentasi lengkap (README, guides, demo script)
- [ ] Submission package terkirim ke MIS Grant portal

**Yang TIDAK ada di MVP rotasi (defer ke v5.1 post-submission):**
- ❌ Points ledger (placeholder field saja di home)
- ❌ Promo generator + spin wheel
- ❌ FCM push notification
- ❌ Email verification untuk DPA edit
- ❌ Daily briefing scheduler per-tenant
- ❌ Dark theme
- ❌ 2 analisis tambahan (`revenue_trend`, `customer_segmentation`)
- ❌ Whisper STT fallback
- ❌ Offline sync queue
