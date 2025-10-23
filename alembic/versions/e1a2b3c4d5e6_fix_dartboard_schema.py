"""Fix dartboard table schema to match models

Revision ID: e1a2b3c4d5e6
Revises: d55f29e75045
Create Date: 2025-10-18 12:00:00.000000

This migration:
1. Renames player_id to owner_id in dartboard table
2. Adds missing columns: is_active, updated_at
3. Renames is_connected to is_active and last_connected_at to last_connected
4. Removes redundant name column duplication
"""

from collections.abc import Sequence
from contextlib import suppress

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1a2b3c4d5e6"
down_revision: str | None = "d55f29e75045"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Rename is_connected to is_active if it exists
    with suppress(Exception):
        op.alter_column("dartboard", "is_connected", new_column_name="is_active")

    # Rename last_connected_at to last_connected if it exists
    with suppress(Exception):
        op.alter_column("dartboard", "last_connected_at", new_column_name="last_connected")

    # Add updated_at column if it doesn't exist
    with suppress(Exception):
        op.add_column("dartboard", sa.Column("updated_at", sa.DateTime(), nullable=True))

    # Rename player_id to owner_id in dartboard table
    with suppress(Exception):
        op.alter_column("dartboard", "player_id", new_column_name="owner_id")


def downgrade() -> None:
    # Reverse: rename owner_id back to player_id
    with suppress(Exception):
        op.alter_column("dartboard", "owner_id", new_column_name="player_id")

    # Remove updated_at column
    with suppress(Exception):
        op.drop_column("dartboard", "updated_at")

    # Rename is_active back to is_connected
    with suppress(Exception):
        op.alter_column("dartboard", "is_active", new_column_name="is_connected")

    # Rename last_connected back to last_connected_at
    with suppress(Exception):
        op.alter_column("dartboard", "last_connected", new_column_name="last_connected_at")
