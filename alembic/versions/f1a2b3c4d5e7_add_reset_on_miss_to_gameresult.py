"""Add reset_on_miss field to GameResult for hard mode

Revision ID: f1a2b3c4d5e7
Revises: e1a2b3c4d5e6
Create Date: 2025-11-15 12:00:00.000000

This migration adds the reset_on_miss column to the gameresults table
to store whether the hard mode (reset on 3 consecutive misses) was enabled
for Round the Clock games.
"""

from collections.abc import Sequence
from contextlib import suppress

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e7"
down_revision: str | None = "e1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add reset_on_miss column to gameresults table"""
    with suppress(Exception):
        op.add_column(
            "gameresults",
            sa.Column("reset_on_miss", sa.Boolean(), nullable=False, server_default="0"),
        )


def downgrade() -> None:
    """Remove reset_on_miss column from gameresults table"""
    with suppress(Exception):
        op.drop_column("gameresults", "reset_on_miss")
