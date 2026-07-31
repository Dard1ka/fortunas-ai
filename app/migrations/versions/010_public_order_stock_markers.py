"""public_orders: paid_at + stock_restored_at (idempotensi stok)

Revision ID: 010
Revises: 009
Create Date: 2026-07-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "010"
down_revision: Union[str, Sequence[str], None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Status yang berarti "pesanan pernah lunas" — dipakai backfill di bawah.
_PAID_ONWARDS = ("paid", "accepted", "rejected", "completed")


def upgrade() -> None:
    op.add_column("public_orders", sa.Column("paid_at", sa.Text(), nullable=True))
    op.add_column("public_orders", sa.Column("stock_restored_at", sa.Text(), nullable=True))
    # Backfill: baris lama yang sudah lunas belum punya paid_at. Tanpa ini,
    # webhook ganda pada pesanan lama akan memotong stok dua kali karena
    # guard `paid_at is None` masih benar untuk baris tersebut.
    op.execute(
        "UPDATE public_orders SET paid_at = updated_at "
        f"WHERE status IN {_PAID_ONWARDS} AND paid_at IS NULL"
    )


def downgrade() -> None:
    op.drop_column("public_orders", "stock_restored_at")
    op.drop_column("public_orders", "paid_at")
