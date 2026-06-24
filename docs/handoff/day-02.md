# Handoff Day 2 → Day 3

**Dev hari ini:** Go Steven Sanjaya (peran Dev B — PostgreSQL foundation)
**Dev besok:** Dev C — HTTPS VPS + endpoint customer/dpa (plan Hari 3)
**Tanggal:** 2026-06-24 (dikerjakan lebih awal dari window resmi)

## ✅ Selesai hari ini

Migrasi metadata-store SQLite → PostgreSQL (SQLAlchemy 2.0 + Alembic). Branch `feat/pg-foundation`.

- `app/db_pg.py` — engine/SessionLocal/Base; `DATABASE_URL` (default SQLite, cutover ke `postgresql+psycopg2://`).
- `app/models.py` — **7 ORM model** (tenants, tenant_users, tenant_settings, customer_users, customer_tenant_memberships, tenant_dpa_policies, device_tokens).
- `app/db.py` — di-refactor jadi wrapper SQLAlchemy; public API & return shape **tidak berubah** → auth.py/tenancy.py/main.py utuh.
- `app/migrations/` + `001_foundation_schema` — bikin 7 tabel + 2 index (`ix_customer_users_firebase_uid` unique, `ix_customer_users_phone_number`).
- `scripts/migrate_sqlite_to_pg.py` (defensif/idempotent) + `scripts/setup_pg.sql`.
- Test: `test_db_pg`, `test_models`, `test_db_repository`, `test_migrate_script` — semua di SQLite in-memory; **total suite hijau: 48 passed** (29 lama + 19 baru) → baseline regresi untuk Dev C.
- CI: +`SQLAlchemy`, ruff exclude `app/migrations`.

## ⚠️ PENTING — scope Day 3 ditarik maju

Atas keputusan Steven, **skema 7 tabel (termasuk yang seharusnya Day 3) sudah dibuat di Hari 2**. Maka Dev C **TIDAK perlu bikin migration 002/003 lagi** — tabel `customer_users`, `customer_tenant_memberships`, `tenant_dpa_policies`, `device_tokens` SUDAH ADA. Fokus Dev C Hari 3 = **endpoint logic + HTTPS**, bukan skema:
- Endpoint customer bootstrap/QR/DPA pakai tabel yang sudah ada.
- Repository per-domain (`customer_repo.py`, `dpa_repo.py`) boleh dibangun di atas model `app/models.py`.

## 🔴 Blocker

- Smoke test Postgres asli (register/login lawan PG) **belum dijalankan** — nunggu password superuser `postgres` dari Steven. Semua test otomatis sudah lulus di SQLite (lapisan DB terbukti benar lintas dialek). Lihat "Cara cutover ke Postgres".

## 📦 State branch

- Current: `feat/pg-foundation`
- Push terakhir: BELUM (nunggu konfirmasi Steven; jangan push tanpa izin)
- PR open: belum

## 🎯 Goal besok (Dev C, plan Hari 3)

HTTPS aktif di VPS + endpoint customer/dpa. Skema DB sudah siap (lihat di atas).

## 📌 Cara cutover ke Postgres (lokal)

1. `psql -U postgres -h localhost -f scripts/setup_pg.sql` (ganti password app dulu).
2. Set `.env`: `DATABASE_URL=postgresql+psycopg2://fortunas_app:<pwd>@localhost:5432/fortunas_app_dev`.
3. `alembic upgrade head` (bikin 7 tabel di Postgres).
4. (Opsional) `python scripts/migrate_sqlite_to_pg.py` — copy data SQLite lama kalau ada (di lokal Steven kosong → no-op).
5. Jalankan app → register UMKM → login → `/auth/me`. Verifikasi row di DBeaver.

## 📌 Catatan teknis

- Timestamp/tanggal = TEXT ISO-8601 (portable SQLite↔PG, cocok kontrak). `tenant_settings.loyalty` = blob JSON `LoyaltySettings`. `create_tenant` auto-seed settings default.
- `init_db()` (create_all) tetap dipanggil di startup (idempotent) — untuk prod jalankan `alembic upgrade head` dulu, create_all lalu no-op. **Catatan:** setelah migration 002 ditambah, startup `create_all` di prod HARUS di-gate ke dev-only atau dihapus agar tidak menyembunyikan "forgot to run migration" error.
- PostgreSQL lokal Steven = versi **18** (plan tulis 15; kompatibel).
