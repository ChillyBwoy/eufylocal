"""add users

Revision ID: 78af5e21947c
Revises: 43da97b30f1d
Create Date: 2026-09-14 00:01:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "78af5e21947c"
down_revision: str | None = "43da97b30f1d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("color", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.add_column("measurements", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_measurements_user_id_users",
        "measurements",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_measurements_user_id_measured_at_id",
        "measurements",
        [
            "user_id",
            sa.literal_column("measured_at DESC"),
            sa.literal_column("id DESC"),
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_measurements_user_id_measured_at_id", table_name="measurements")
    op.drop_constraint(
        "fk_measurements_user_id_users",
        "measurements",
        type_="foreignkey",
    )
    op.drop_column("measurements", "user_id")
    op.drop_table("users")
