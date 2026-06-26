# Handoff Day 5 (Checkout nyambung customer — MVP #6)

> _Ditulis retroaktif (backfill) 2026-06-26 dari git history + catatan dev; fakta diverifikasi terhadap squash `d9d331d` (PR #8)._

**Dev hari ini:** Go Steven Sanjaya
**Tanggal:** 2026-06-25
**Branch:** `feat/checkout-confirm` (dari `main` @ `bf535f0` = Day 4 merge) → PR #8, squash `d9d331d`

## ✅ Selesai — MVP fitur #6 (checkout multi-item nyambung customer)

`POST /checkout/confirm` (UMKM-auth): multi-item sale → BigQuery + opt-in `customer_qr_token` loyalty link. Berdampingan dengan `/voice/transaction` lama (tidak disentuh).

- `app/services/checkout_service.py` (baru) — `confirm_checkout` orchestrator + `resolve_bq_customer_name` (pure) + **satu seam BQ lazy** `persist_basket` + 5 wrapper `_bq_*` (`# pragma: no cover`); reuse helper voice (`to_wa_payload`/`validate_payload`/`resolve_customer_id`/`next_invoice_number`/`_insert_in_batches`).
- `app/api/routes/checkout.py` (baru) + register router di `app/main.py`.
- Docs: `API_CONTRACTS.md` tandai implemented, `.env.example`, ROADMAP/PLAN cite PR #8.

## ⚙️ Catatan teknis & keputusan kunci (jangan dibongkar tanpa diskusi)

- **Unify, QR menang:** QR valid → username QR jadi nama pelanggan BQ (mengalahkan free-text `customer`).
- **Sale-first, loyalty-after:** `verify_qr`+`get_customer` (pure) sebelum sale; `consume_nonce`+`ensure_membership` HANYA setelah `persist_basket` "ok" → BQ gagal **tidak** membakar QR (terkunci di `test_bq_error_does_not_burn_qr`).
- **Loyalty tak pernah blokir sale:** QR invalid/expired/tampered/replay → sale tetap jalan, `customer_user_id=null` + note.
- **CI-clean import dibuktikan:** route+service import walau `google.cloud` diblokir (pola lazy = firebase seam Day 4). **Nol dep CI baru.**
- **Idempotency:** lewat `invoice` eksplisit (digit-normalized; non-digit di-strip biar `int()` tak crash); `invoice=null` → auto-allocate.
- Suite: 106 → **127 hijau** (test baru: `test_checkout_routes.py`, `test_checkout_service.py`), ruff bersih, CI backend+mobile hijau.

## 🔴 Blocker
- TIDAK ADA. Slice merge-able default-safe.

## 🎯 Goal berikutnya
- Analisis ke-5 `top_product` (#8) — track backend terakhir yang credential-free.
- UI mobile (checkout, customer/QR, DPA) = track Flutter terpisah.

## 📌 Out-of-scope (defer → v5.1)
- `points_earned`/`promo_redeemed` selalu `null`, `promo_code` diabaikan, identity-resolution deterministik `cu_`→numeric BQ key, UI mobile checkout.
- **PENDING (luar repo):** verifikasi insert BQ asli butuh GCP service account (di master checklist `PENDING_EXTERNAL_SETUP.md`, bukan seam baru).
