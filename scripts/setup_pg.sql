-- Buat role + database untuk Fortunas metadata-store.
-- Jalankan sebagai superuser:
--   psql -U postgres -h localhost -f scripts/setup_pg.sql
-- Ganti 'CHANGE_ME_app_pwd' dengan password pilihanmu, lalu pakai di .env DATABASE_URL.

DO
$$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'fortunas_app') THEN
      CREATE ROLE fortunas_app LOGIN PASSWORD 'CHANGE_ME_app_pwd';
   END IF;
END
$$;

-- CREATE DATABASE tak bisa di dalam blok transaksi/DO → pakai \gexec idempotent.
SELECT 'CREATE DATABASE fortunas_app_dev OWNER fortunas_app'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'fortunas_app_dev')\gexec

-- Catatan: di PostgreSQL 15+/18, role HARUS jadi OWNER database (di atas) agar
-- 'alembic upgrade head' bisa CREATE tabel di schema public. GRANT di bawah cuma pelengkap.
GRANT ALL PRIVILEGES ON DATABASE fortunas_app_dev TO fortunas_app;
