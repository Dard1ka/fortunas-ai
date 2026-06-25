"""qr_nonces single-use store

Revision ID: 002
Revises: 001
Create Date: 2026-06-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "qr_nonces",
        sa.Column("nonce", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("nonce"),
    )


def downgrade() -> None:
    op.drop_table("qr_nonces")
