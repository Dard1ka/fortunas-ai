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

# Status yang sudah LEWAT titik bayar — dipakai backfill di bawah.
#
# `cancelled` ikut: pesanan yang lunas lalu di-refund/chargeback gateway berakhir
# di sini (`cancel_by_gateway` menggerakkan `paid` → `cancelled`). Tanpa `paid_at`
# terisi, replay notifikasi settlement untuk baris seperti itu akan MENANG klaim
# `WHERE paid_at IS NULL` lalu memotong stok LAGI — persis lubang yang backfill
# ini ada untuk menutup.
#
# Konsekuensi yang diterima sadar: `cancelled` juga memuat pesanan yang BELUM
# pernah lunas (deny/cancel/expire dari gateway saat masih `pending_payment`).
# Baris seperti itu ikut kebagian `paid_at`, jadi `restore_stock` yang datang
# belakangan bisa menaikkan stok yang tak pernah dipotong. Status saja tak bisa
# membedakan keduanya — ini varian dari utang "paid_at cuma berarti klaim menang,
# bukan stok pernah dipotong" (day-15 §Utang, kandidat `stock_decremented_at` +
# migrasi 011). Ditukar sadar: stok terpotong DUA KALI lebih berbahaya daripada
# stok naik sekali pada pesanan yang sudah mati di gateway.
#
# `expired` sengaja TIDAK ikut: itu pesanan yang kedaluwarsa sebelum dibayar.
_PAID_ONWARDS = ("paid", "accepted", "rejected", "completed", "cancelled")


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
