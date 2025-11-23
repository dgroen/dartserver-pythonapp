"""Add reset_on_miss field to GameResult for hard mode

Revision ID: f1a2b3c4d5e7
Revises: ad03fe01b8c6
Create Date: 2025-11-15 12:00:00.000000

This migration adds the reset_on_miss column to the gameresults table
to store whether the hard mode (reset on 3 consecutive misses) was enabled
for Round the Clock games.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "f1a2b3c4d5e7"
down_revision: str | None = "ad03fe01b8c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'gameresults' AND column_name = 'reset_on_miss'
            ) THEN
                ALTER TABLE gameresults ADD COLUMN reset_on_miss BOOLEAN NOT
                NULL DEFAULT false;
            END IF;
        END $$;
    """,
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'gameresults' AND column_name = 'reset_on_miss'
            ) THEN
                ALTER TABLE gameresults DROP COLUMN reset_on_miss;
            END IF;
        END $$;
    """,
    )
