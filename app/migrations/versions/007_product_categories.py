"""product_categories + products.category_id

Revision ID: 007
Revises: 006
Create Date: 2026-07-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, Sequence[str], None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_category_tenant_name"),
    )
    op.create_index("ix_product_categories_tenant", "product_categories", ["tenant_id"])
    with op.batch_alter_table("products") as b:
        b.add_column(sa.Column("category_id", sa.Integer(), nullable=True))
        b.create_foreign_key("fk_products_category", "product_categories",
                             ["category_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    with op.batch_alter_table("products") as b:
        b.drop_column("category_id")
    op.drop_index("ix_product_categories_tenant", table_name="product_categories")
    op.drop_table("product_categories")
