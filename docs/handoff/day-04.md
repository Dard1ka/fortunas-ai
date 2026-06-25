# Handoff Day 4 (Customer JWT + QR identity backend)

**Dev hari ini:** Go Steven Sanjaya
**Tanggal:** 2026-06-25
**Branch:** `feat/customer-qr-identity` (dari `main` @ DPA-merge `5d28ecd`)

## ✅ Selesai — MVP fitur #4 (QR identitas) + #5 (scan → auto-member) + #3 backend skeleton

Alur penuh credential-free & testable offline: customer bootstrap (Firebase seam) → QR signed 90 detik single-use → UMKM scan → auto-membership.

- `app/core/auth.py` — `role` claim (`create_access_token` default `umkm`) + `create_customer_token`.
- `app/core/firebase_auth.py` — seam `verify_firebase_token`: real lazy-import / dev stub opt-in (`FORTUNAS_DEV_AUTH=1`, token `dev:<uid>:<phone>`) / else `FirebaseNotConfigured` (503).
- `app/customer_repo.py` — customer (`upsert` by firebase_uid, no-clobber) + membership (`ensure_membership` idempotent, `member_since`=today).
- `app/core/customer_ctx.py` — `get_current_customer` (role-gated 401).
- `app/services/qr_service.py` — PURE issue/verify (HS256, `typ:"qr"`, 90s); reason `expired`/`tampered`.
- `app/qr_nonce_repo.py` — `consume_nonce` atomik (PK `IntegrityError` = replay) + `purge_expired`.
- `app/models.py` + `app/migrations/versions/002_qr_nonces.py` — tabel `qr_nonces`.
- `app/api/routes/customer.py` — `POST /customer/auth/bootstrap` (200, idempotent), `GET/PUT /customer/me`, `POST /customer/qr/session`.
- `app/api/routes/scan.py` — `POST /umkm/customer/scan/validate` (UMKM-auth) → `{valid, reason}`/membership.
- `app/main.py` — register `customer` + `scan` router.

## ⚙️ Catatan teknis
- **Nol dep baru.** `firebase_admin` lazy-import HANYA jalur real (`# pragma: no cover`) → tak masuk CI. `requirements.txt`/`ci.yml` tak disentuh.
- **Keamanan scan (urutan):** verify signature+exp → cek customer ada → consume nonce → membership. Token palsu/kedaluwarsa/asing tak membakar nonce; replay tetap ketahuan walau sudah member.
- **Nol-regresi UMKM:** `create_access_token` additive; token UMKM lama (tanpa `role`) → diperlakukan `umkm`. `get_current_tenant` tak diubah.
- Test: 8 baru, semua offline (SQLite in-memory + monkeypatch seam). Baseline 74 + baru = hijau, ruff bersih.

## 🔴 Blocker
- TIDAK ADA. Slice merge-able default-safe. Bootstrap real butuh Firebase (seam di PENDING); dev pakai `FORTUNAS_DEV_AUTH=1`.

## 🎯 Goal berikutnya
- Checkout endpoint (#6, kontrak `CheckoutConfirm*` sudah ada) + nyambung customer via scan.
- Analisis `top_product` (#8). UI mobile customer (3 layar + render QR) = track Flutter.

## 📌 Out-of-scope (defer)
- Real Firebase wiring, mobile UI, checkout, points/promo saat scan, FCM, rate limiting, scheduling `purge_expired`.
