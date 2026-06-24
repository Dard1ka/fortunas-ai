# Fortunas AI — API Contracts (v5.0 MVP)

> **Status:** kontrak (Hari 1). Endpoint belum semua diimplementasi — lihat tag.
> **Sumber Pydantic:** [`app/schemas.py`](../app/schemas.py) · **Mirror Dart:** [`mobile/lib/api/models.dart`](../mobile/lib/api/models.dart)
> **Auth:** header `Authorization: Bearer <jwt>` (kecuali bootstrap). Base URL dev: `http://127.0.0.1:8000`.

**Legend:** 🟢 MVP-now · 🟡 MVP-thin (spin-wheel demo) · 🔵 v5.1 (kontrak saja, endpoint nanti).
Tanggal/waktu = ISO-8601 string · uang = integer Rupiah.

## Konvensi Error

| Kode | Arti |
|---|---|
| 401 | Token tidak ada / invalid / kedaluwarsa |
| 403 | Akses lintas-tenant / lintas-customer ditolak |
| 409 | Konflik (email/username sudah dipakai) |
| 422 | Validasi payload gagal (otomatis Pydantic) |

QR invalid TIDAK melempar exception — `POST /umkm/customer/scan/validate` balas `200` dgn `{valid:false, reason:"expired|tampered|replayed"}`.

---

## 🟢 Customer Auth & Profile

### POST /customer/auth/bootstrap
Verifikasi Firebase ID token → upsert `customer_users` → balas internal JWT.

Request `CustomerBootstrapRequest`:
```json
{ "firebase_id_token": "<firebase-jwt>", "username": "Budi", "birth_date": "1995-08-17" }
```
Response `CustomerBootstrapResponse`:
```json
{
  "access_token": "<internal-jwt>", "token_type": "bearer",
  "role": "customer", "is_new_user": true,
  "profile": { "customer_user_id": "cu_123", "username": "Budi",
    "phone_number": "+628123456789", "birth_date": "1995-08-17",
    "created_at": "2026-06-24T10:00:00+07:00" }
}
```
```bash
curl -X POST http://127.0.0.1:8000/customer/auth/bootstrap \
  -H "Content-Type: application/json" \
  -d '{"firebase_id_token":"<token>","username":"Budi","birth_date":"1995-08-17"}'
```

### GET /customer/me → `CustomerProfile`
### PUT /customer/me ← `CustomerProfileUpdate`
```json
{ "username": "Budi Santoso", "birth_date": "1995-08-17" }
```

---

## 🟢 QR Identity + Scan Validate

### POST /customer/qr/session → `QRSessionResponse`
QR identitas customer, signed JWT 90 detik single-use + nonce (REKOMENDASI A5).
```json
{ "qr_token": "<jwt>", "nonce": "ab12cd", "issued_at": "2026-06-24T10:00:00+07:00",
  "expires_at": "2026-06-24T10:01:30+07:00", "ttl_seconds": 90 }
```

### POST /umkm/customer/scan/validate
Request `QRValidateRequest`: `{ "customer_qr_token": "<jwt>" }`
Response `QRValidateResponse` (valid):
```json
{ "valid": true, "customer_user_id": "cu_123", "username": "Budi",
  "is_new_member": false, "member_since": "2026-07-01", "reason": null }
```
Response invalid: `{ "valid": false, "reason": "expired" }`

---

## 🟢 Checkout (multi-item, baru)

### POST /checkout/confirm
Endpoint **baru**, coexist dgn `/voice/transaction` lama (tidak diganggu). `customer_qr_token` opt-in.

Request `CheckoutConfirmRequest`:
```json
{
  "items": [
    { "product": "Kopi Susu", "qty": 2, "unit_price": 15000 },
    { "product": "Roti", "qty": 1, "unit_price": 12000 }
  ],
  "customer": "Budi", "country": "Indonesia",
  "customer_qr_token": null, "promo_code": null
}
```
Response `CheckoutConfirmResponse`:
```json
{ "ok": true, "status": "ok", "reply": "Tercatat 2 item, total Rp42.000.",
  "invoice": "10001", "item_count": 2, "grand_total": 42000,
  "customer_user_id": null, "is_new_member": false, "member_since": null,
  "points_earned": null, "promo_redeemed": null }
```
```bash
curl -X POST http://127.0.0.1:8000/checkout/confirm \
  -H "Authorization: Bearer <jwt>" -H "Content-Type: application/json" \
  -d '{"items":[{"product":"Kopi","qty":2,"unit_price":15000}],"customer":"Budi"}'
```

---

## 🟢 DPA Policy

### GET /umkm/dpa → `DPAPayload`
### PUT /umkm/dpa ← `DPAUpdateRequest`
Edit pakai konfirmasi password (MVP; email-OTP → v5.1).
```json
{ "raw_text": "Tidak menjual produk tembakau.",
  "allowed_rules": ["diskon makanan"], "forbidden_rules": ["rokok", "tembakau"],
  "password": "<password-umkm>" }
```

---

## 🔵 Device Token (FCM) — v5.1 (kontrak saja)

### POST /customer/device-token · POST /umkm/device-token ← `DeviceTokenRequest`
```json
{ "fcm_token": "<fcm-token>", "platform": "android", "user_type": "customer" }
```

---

## 🟡 Loyalty Settings + Points + Promo (MVP-thin)

### GET /umkm/settings/loyalty · PUT /umkm/settings/loyalty ← `LoyaltySettings`
```json
{ "min_points_to_generate_promo": 30,
  "spin_wheel": [
    { "discount_amount": 100000, "probability": 0.05 },
    { "discount_amount": 50000, "probability": 0.10 },
    { "discount_amount": 25000, "probability": 0.25 },
    { "discount_amount": 10000, "probability": 0.60 } ],
  "promo_valid_days": 7,
  "points_earning_rule": { "type": "per_amount", "points_per_amount": 10000, "points_per_invoice": 1 } }
```
> Catatan: total `probability` wajib = 1.0 (divalidasi backend).

### GET /customer/points → `PointsBalanceResponse`
```json
{ "customer_user_id": "cu_123", "balance": 120,
  "recent": [ { "event_type": "earn", "points_delta": 45, "invoice": "10001",
    "promo_id": null, "tenant_id": 1, "created_at": "2026-07-01T12:00:00+07:00" } ] }
```

### POST /customer/promos/generate ← `PromoGenerateRequest` → `PromoGenerateResponse`
```json
{ "tenant_id": 1 }
```
```json
{ "promo": { "promo_id": "pr_9", "tenant_id": 1, "name": "Diskon Kopi X",
    "code": "KOPI25", "description": "Potongan Rp25.000 untuk Kopi X.",
    "discount_amount": 25000, "target_product": "Kopi X", "status": "generated",
    "points_cost": 30, "generated_at": "2026-07-01T12:00:00+07:00",
    "expires_at": "2026-07-08T12:00:00+07:00", "redeemed_at": null,
    "qr_payload": "<signed-token>" },
  "spin_result": { "discount_amount": 25000, "probability": 0.25 } }
```

### GET /customer/promos → `PromoListResponse`
```json
{ "promos": [ /* PromoInstance[] */ ] }
```
