"""products (per-tenant catalog) + customer_product_stats (per-customer per-item)

Revision ID: 004
Revises: 003
Create Date: 2026-07-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, Sequence[str], None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("stock_code", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "stock_code", name="uq_product_tenant_code"),
    )
    op.create_index("ix_products_tenant", "products", ["tenant_id"])

    op.create_table(
        "customer_product_stats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_user_id", sa.Text(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("product_name", sa.Text(), nullable=False),
        sa.Column("purchase_count", sa.Integer(), nullable=False),
        sa.Column("total_amount", sa.Integer(), nullable=False),
        sa.Column("last_purchased_at", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["customer_user_id"], ["customer_users.customer_user_id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("customer_user_id", "tenant_id", "product_name",
                            name="uq_customer_product"),
    )
    op.create_index("ix_customer_product_stats_customer", "customer_product_stats",
                    ["customer_user_id"])


def downgrade() -> None:
    op.drop_index("ix_customer_product_stats_customer", table_name="customer_product_stats")
    op.drop_table("customer_product_stats")
    op.drop_index("ix_products_tenant", table_name="products")
    op.drop_table("products")
