# Handoff Day 1 → Day 2

**Dev hari ini:** Go Steven Sanjaya (mengisi peran **Dev A** — pemetaan A/B/C belum final, lihat ROADMAP)
**Dev besok:** **Dev B** — PostgreSQL foundation (plan Hari 2)
**Tanggal:** 2026-06-24 *(dikerjakan lebih awal dari window resmi 29 Jun)*

## ✅ Selesai hari ini

Kontrak API v5.0 MVP (langkah 4–6 plan Hari 1). Branch `feat/foundation-contracts`, **7 commit, BELUM di-push**.

- **25 schema Pydantic** di `app/schemas.py` — additive, class lama tidak diubah. 6 domain: customer auth & profile, QR identity + validate, multi-item checkout, DPA policy, device token, loyalty/points/promo.
- **25 DTO Dart** mirror di `mobile/lib/api/models.dart` — `flutter analyze` clean.
- **29 unit test TDD** di `tests/test_schemas.py` — semua hijau.
- `docs/API_CONTRACTS.md` — endpoint + sample curl + status tag (🟢 now / 🟡 thin / 🔵 v5.1).
- `requirements-dev.txt` — pytest sebagai dev dependency.

Commit terakhir: `5c89ffa`. Verifikasi: tidak ada perubahan di `app/api/routes/*` atau voice/pipeline (alur lama utuh).

> Spec & plan brainstorming **tidak** di repo — ada di folder induk `Fortunas/brainstorming/{specs,plans}/`.

## ⏳ Belum selesai (sisa Hari 1, opsional dilengkapi nanti)

- Langkah 1: branch `dev` + branch protection `main` (butuh GitHub Settings)
- Langkah 2: PR template `.github/pull_request_template.md`
- Langkah 3: CI `.github/workflows/ci.yml` (ruff + `flutter analyze` + pytest smoke)

## 🔴 Blocker / Bug ditemukan

- Tidak ada blocker. Pemetaan Dev A/B/C masih **TBD**.

## 📦 State branch

- Current: `feat/foundation-contracts`
- Push terakhir: **BELUM di-push** (aturan: jangan push/PR tanpa konfirmasi Steven; docs digabung ke satu PR MVP nanti)
- PR open: belum

## 🎯 Goal besok (Dev B — PostgreSQL, plan Hari 2)

Migrasi SQLite → Postgres + skema auth. **Kontrak hari ini menentukan kolom yang harus tersedia** — selaraskan tabel Postgres dengan field schema agar repository layer bisa langsung memetakan ke DTO:

- `customer_users` → harus bisa menghasilkan `CustomerProfile` (`customer_user_id`, `username`, `phone_number`, `birth_date`, `created_at`) + `firebase_uid`.
- `tenant_dpa_policies` → cocokkan `DPAPayload` (`raw_text`, `allowed_rules`, `forbidden_rules`, `policy_summary`, `version`, `verified_at`, `updated_at`).
- `tenant_settings` (loyalty) → cocokkan `LoyaltySettings` (`min_points_to_generate_promo`, `spin_wheel`, `promo_valid_days`, `points_earning_rule`).
- `device_tokens` → cocokkan `DeviceTokenRequest` (`fcm_token`, `platform`, `user_type`) — v5.1, tabel boleh disiapkan.

## 📌 Catatan tambahan (keputusan + dependency untuk hari berikut)

- **Customer JWT (perlu di Hari 5):** `app/core/auth.py::create_access_token` saat ini hanya menanam `tenant_id`. Customer bootstrap perlu klaim `role="customer"` + `customer_user_id` (tanpa `tenant_id`). Perlu ekstensi.
- **Checkout baru:** `/checkout/confirm` (multi-item) = endpoint **BARU**, coexist dgn `/voice/transaction` lama. **Jangan ganggu** alur voice. `customer_qr_token` opt-in (REKOMENDASI A7).
- **QR:** TTL 90 detik, single-use + nonce (REKOMENDASI A5).
- **DPA:** edit pakai konfirmasi password (MVP simplified); email-OTP ditunda v5.1.
- **Konvensi kontrak:** tanggal/waktu = string ISO-8601; uang = integer Rupiah; enum tertutup = `Literal`.
- **Spin wheel default:** total `probability` = 1.0 (divalidasi backend); EV Rp22.250 — jangan ubah tanpa kalibrasi ambang poin (REKOMENDASI "Catatan Ekonomi").
- **Cara jalankan test:** `pip install -r requirements-dev.txt` lalu `python -m pytest tests/test_schemas.py -v` dari root repo.
