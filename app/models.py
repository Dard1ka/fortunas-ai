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
