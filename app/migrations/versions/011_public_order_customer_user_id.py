"""public_orders: customer_user_id (tautan akun pelanggan untuk BigQuery/loyalty)

Revision ID: 011
Revises: 010
Create Date: 2026-08-03

Kolom opsional: jalur pesan-online tanpa auth, jadi hanya terisi bila pelanggan
kebetulan login saat memesan. Dipakai saat pesanan `completed` untuk menaut
penjualan online ke akun (checkout_service.persist_completed_order). Baris lama
dibiarkan NULL (tamu) — tak ada backfill yang bisa menebak akun secara retroaktif.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "011"
down_revision: Union[str, Sequence[str], None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "public_orders", sa.Column("customer_user_id", sa.Text(), nullable=True))
    op.create_index(
        "ix_public_orders_customer_user_id", "public_orders", ["customer_user_id"])


def downgrade() -> None:
    op.drop_index("ix_public_orders_customer_user_id", table_name="public_orders")
    op.drop_column("public_orders", "customer_user_id")
