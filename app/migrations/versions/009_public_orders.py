"""public orders (customer self-order via UMKM code)

Revision ID: 009
Revises: 008
Create Date: 2026-07-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "009"
down_revision: Union[str, Sequence[str], None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "public_orders",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("code", sa.Text(), nullable=False, server_default=""),
        sa.Column("customer_name", sa.Text(), nullable=False, server_default=""),
        sa.Column("customer_phone", sa.Text(), nullable=False, server_default=""),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending_payment"),
        sa.Column("payment_provider", sa.Text(), nullable=True),
        sa.Column("payment_order_id", sa.Text(), nullable=True),
        sa.Column("payment_token", sa.Text(), nullable=True),
        sa.Column("payment_redirect_url", sa.Text(), nullable=True),
        sa.Column("payment_status", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.Text(), nullable=True),
    )
    op.create_index("ix_public_orders_tenant_id", "public_orders", ["tenant_id"])
    op.create_index("ix_public_orders_status", "public_orders", ["status"])
    op.create_index(
        "ix_public_orders_payment_order_id", "public_orders", ["payment_order_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_public_orders_payment_order_id", table_name="public_orders")
    op.drop_index("ix_public_orders_status", table_name="public_orders")
    op.drop_index("ix_public_orders_tenant_id", table_name="public_orders")
    op.drop_table("public_orders")
