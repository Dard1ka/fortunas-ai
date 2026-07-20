"""points ledger, balances, promo instances/events, notification log

Revision ID: 003
Revises: 002
Create Date: 2026-07-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, Sequence[str], None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "points_ledger",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_user_id", sa.Text(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("points_delta", sa.Integer(), nullable=False),
        sa.Column("invoice", sa.Text(), nullable=True),
        sa.Column("promo_id", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["customer_user_id"], ["customer_users.customer_user_id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_points_ledger_customer", "points_ledger", ["customer_user_id"])

    op.create_table(
        "points_balances",
        sa.Column("customer_user_id", sa.Text(), nullable=False),
        sa.Column("balance", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["customer_user_id"], ["customer_users.customer_user_id"]),
        sa.PrimaryKeyConstraint("customer_user_id"),
    )

    op.create_table(
        "promo_instances",
        sa.Column("promo_id", sa.Text(), nullable=False),
        sa.Column("customer_user_id", sa.Text(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("promo_code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("target_product", sa.Text(), nullable=True),
        sa.Column("discount_amount", sa.Integer(), nullable=False),
        sa.Column("points_cost", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("generated_at", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.Text(), nullable=True),
        sa.Column("redeemed_at", sa.Text(), nullable=True),
        sa.Column("redeemed_invoice", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["customer_user_id"], ["customer_users.customer_user_id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("promo_id"),
        sa.UniqueConstraint("promo_code"),
    )
    op.create_index("ix_promo_instances_customer", "promo_instances", ["customer_user_id"])

    op.create_table(
        "promo_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("promo_id", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["promo_id"], ["promo_instances.promo_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_promo_events_promo", "promo_events", ["promo_id"])

    op.create_table(
        "notification_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("recipient_type", sa.Text(), nullable=False),
        sa.Column("recipient_id", sa.Text(), nullable=False),
        sa.Column("template", sa.Text(), nullable=False),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("sent_at", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("notification_log")
    op.drop_index("ix_promo_events_promo", table_name="promo_events")
    op.drop_table("promo_events")
    op.drop_index("ix_promo_instances_customer", table_name="promo_instances")
    op.drop_table("promo_instances")
    op.drop_table("points_balances")
    op.drop_index("ix_points_ledger_customer", table_name="points_ledger")
    op.drop_table("points_ledger")
