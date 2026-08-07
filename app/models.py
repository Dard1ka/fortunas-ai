"""ORM models untuk metadata-store (auth, settings, customer, dpa, device).

Konvensi: timestamp/tanggal = Text ISO-8601; JSON = tipe generik (JSONB di PG,
TEXT-JSON di SQLite). PK surrogate = Integer (SERIAL di PG).
"""
from __future__ import annotations

from sqlalchemy import (
    JSON,
    Column,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)

from app.db_pg import Base


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    table_prefix = Column(Text, nullable=False, unique=True)
    business_profile = Column(JSON, nullable=False, default=dict)
    created_at = Column(Text, nullable=False)


class TenantUser(Base):
    __tablename__ = "tenant_users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    role = Column(Text, nullable=False, default="admin")
    created_at = Column(Text, nullable=False)


class TenantSettings(Base):
    __tablename__ = "tenant_settings"
    tenant_id = Column(Integer, ForeignKey("tenants.id"), primary_key=True)
    loyalty = Column(JSON, nullable=False, default=dict)
    created_at = Column(Text, nullable=True)
    updated_at = Column(Text, nullable=True)


class CustomerUser(Base):
    __tablename__ = "customer_users"
    customer_user_id = Column(Text, primary_key=True)
    firebase_uid = Column(Text, unique=True, index=True, nullable=True)
    username = Column(Text, nullable=False)
    phone_number = Column(Text, nullable=False, default="", index=True)
    birth_date = Column(Text, nullable=False, default="")
    created_at = Column(Text, nullable=True)


class CustomerTenantMembership(Base):
    __tablename__ = "customer_tenant_memberships"
    __table_args__ = (
        UniqueConstraint("customer_user_id", "tenant_id", name="uq_customer_tenant"),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_user_id = Column(
        Text, ForeignKey("customer_users.customer_user_id"), nullable=False
    )
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    member_since = Column(Text, nullable=True)
    created_at = Column(Text, nullable=True)


class TenantDPAPolicy(Base):
    __tablename__ = "tenant_dpa_policies"
    tenant_id = Column(Integer, ForeignKey("tenants.id"), primary_key=True)
    raw_text = Column(Text, nullable=False, default="")
    allowed_rules = Column(JSON, nullable=False, default=list)
    forbidden_rules = Column(JSON, nullable=False, default=list)
    policy_summary = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=0)
    verified_at = Column(Text, nullable=True)
    updated_at = Column(Text, nullable=True)


class DeviceToken(Base):
    __tablename__ = "device_tokens"
    id = Column(Integer, primary_key=True, autoincrement=True)
    fcm_token = Column(Text, nullable=False, unique=True)
    platform = Column(Text, nullable=False)
    user_type = Column(Text, nullable=True)
    owner_ref = Column(Text, nullable=True)
    created_at = Column(Text, nullable=True)


class QRNonce(Base):
    __tablename__ = "qr_nonces"
    nonce = Column(Text, primary_key=True)
    expires_at = Column(Text, nullable=False)
    created_at = Column(Text, nullable=True)


class PointsLedger(Base):
    __tablename__ = "points_ledger"
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_user_id = Column(
        Text, ForeignKey("customer_users.customer_user_id"), nullable=False, index=True
    )
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    event_type = Column(Text, nullable=False)  # earn | redeem | expire | adjust
    points_delta = Column(Integer, nullable=False)
    invoice = Column(Text, nullable=True)
    promo_id = Column(Text, nullable=True)
    created_at = Column(Text, nullable=True)


class PointsBalance(Base):
    __tablename__ = "points_balances"
    customer_user_id = Column(
        Text, ForeignKey("customer_users.customer_user_id"), primary_key=True
    )
    balance = Column(Integer, nullable=False, default=0)
    updated_at = Column(Text, nullable=True)


class PromoInstanceRow(Base):
    __tablename__ = "promo_instances"
    promo_id = Column(Text, primary_key=True)
    customer_user_id = Column(
        Text, ForeignKey("customer_users.customer_user_id"), nullable=False, index=True
    )
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    promo_code = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=False, default="")
    description = Column(Text, nullable=False, default="")
    target_product = Column(Text, nullable=True)
    discount_amount = Column(Integer, nullable=False, default=0)
    points_cost = Column(Integer, nullable=False, default=0)
    status = Column(Text, nullable=False, default="generated")  # generated | redeemed | expired
    generated_at = Column(Text, nullable=True)
    expires_at = Column(Text, nullable=True)
    redeemed_at = Column(Text, nullable=True)
    redeemed_invoice = Column(Text, nullable=True)


class PromoEvent(Base):
    __tablename__ = "promo_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    promo_id = Column(Text, ForeignKey("promo_instances.promo_id"), nullable=False, index=True)
    event_type = Column(Text, nullable=False)  # generated | redeemed | expired | reminder_sent
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(Text, nullable=True)


class NotificationLog(Base):
    __tablename__ = "notification_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient_type = Column(Text, nullable=False)  # customer | umkm
    recipient_id = Column(Text, nullable=False)
    template = Column(Text, nullable=False)  # daily_briefing | dpa_reminder | promo_unused
    channel = Column(Text, nullable=False, default="push")
    status = Column(Text, nullable=False, default="queued")  # queued | sent | skipped | failed
    sent_at = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)


class Product(Base):
    """Katalog produk milik satu UMKM (tenant-scoped via tenant_id).

    stock_code otomatis: 2 huruf awal nama + nomor urut per-prefix per-tenant
    (mis. "kopi susu" -> ko-001, "kopi latte" -> ko-002). Unik per tenant.
    """
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("tenant_id", "stock_code", name="uq_product_tenant_code"),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=False, default="")
    stock_code = Column(Text, nullable=False)
    image_url = Column(Text, nullable=False, default="")  # path served via /media/products
    stock = Column(Integer, nullable=True)  # NULL = tak-dilacak; >=0 = jumlah dilacak
    price = Column(Integer, nullable=True)  # harga jual (Rupiah, bulat); NULL = belum diset
    category_id = Column(
        Integer, ForeignKey("product_categories.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(Text, nullable=True)


class ProductCategory(Base):
    """Kategori produk custom milik satu UMKM (tenant-scoped)."""
    __tablename__ = "product_categories"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_category_tenant_name"),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(Text, nullable=False)
    created_at = Column(Text, nullable=True)


class CustomerProductStat(Base):
    """Riwayat belanja per-barang di akun pelanggan (gaya Indomaret Point).

    Global lintas UMKM (milik customer), tapi menyimpan tenant_id agar bisa
    dipisah per-UMKM saat ditampilkan. Di-upsert saat checkout customer.
    """
    __tablename__ = "customer_product_stats"
    __table_args__ = (
        UniqueConstraint("customer_user_id", "tenant_id", "product_name",
                         name="uq_customer_product"),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_user_id = Column(
        Text, ForeignKey("customer_users.customer_user_id"), nullable=False, index=True
    )
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    product_name = Column(Text, nullable=False)
    purchase_count = Column(Integer, nullable=False, default=0)
    total_amount = Column(Integer, nullable=False, default=0)
    last_purchased_at = Column(Text, nullable=True)


class PublicOrder(Base):
    """Pesanan pelanggan lewat alur publik (kode UMKM, tanpa akun/scan QR).

    Menyimpan state pesanan sebelum jadi transaksi final. Alur status:
      pending_payment → paid → accepted/rejected → completed
                              ↘ expired / cancelled
    Stok dipotong saat status menjadi `paid` (lihat order_repo.mark_paid).
    """
    __tablename__ = "public_orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    code = Column(Text, nullable=False, default="")  # snapshot kode UMKM
    customer_name = Column(Text, nullable=False, default="")
    customer_phone = Column(Text, nullable=False, default="")
    # Akun pelanggan yang kebetulan login saat memesan (loyalty). None = tamu.
    # Jalur publik tanpa auth, jadi ini best-effort: diisi hanya bila klien
    # menyertakan bearer pelanggan yang sah (lihat routes/public.create_public_order).
    # Dipakai saat pesanan `completed` untuk menaut penjualan online ke akun
    # (checkout_service.persist_completed_order).
    customer_user_id = Column(Text, nullable=True, index=True)
    # items: list[{product_id, name, qty, unit_price, subtotal}]
    items = Column(JSON, nullable=False, default=list)
    total = Column(Integer, nullable=False, default=0)  # Rupiah bulat
    status = Column(Text, nullable=False, default="pending_payment", index=True)
    payment_provider = Column(Text, nullable=True)      # "midtrans" | "simulated"
    payment_order_id = Column(Text, nullable=True, unique=True, index=True)  # id ke gateway
    payment_token = Column(Text, nullable=True)         # Snap token
    payment_redirect_url = Column(Text, nullable=True)  # Snap redirect URL
    payment_status = Column(Text, nullable=True)        # status mentah dari gateway
    # Penanda idempotensi stok (Slice 1). paid_at = pernah lunas → stok SUDAH
    # dipotong; jangan potong ulang & jangan mundurkan status saat webhook
    # gateway terkirim ganda. stock_restored_at = stok sudah dikembalikan.
    paid_at = Column(Text, nullable=True)
    stock_restored_at = Column(Text, nullable=True)
    created_at = Column(Text, nullable=True)
    updated_at = Column(Text, nullable=True)
