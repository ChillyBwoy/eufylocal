"""Create measurements table.

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "measurements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("measured_at", sa.Text(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("impedance_ohm", sa.Float(), nullable=True),
        sa.Column("device_id", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("raw_payload_hex", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sqlite_autoincrement=True,
    )
    op.create_index(
        "idx_measurements_measured_at",
        "measurements",
        [sa.text("measured_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_measurements_measured_at", table_name="measurements")
    op.drop_table("measurements")
