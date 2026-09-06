"""add_score_scd2_versioning

Adds SCD2 versioning columns to `scores` so a mis-detected throw can be
corrected by invalidating the old row and inserting a new current version,
instead of deleting history.

Existing rows are backfilled to version 1 / is_current = true, which is what
they already are semantically.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-06 11:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(inspector, table: str, column: str) -> bool:
    if not inspector.has_table(table):
        return False
    return column in {col["name"] for col in inspector.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_column(inspector, "scores", "is_current"):
        return

    # Added nullable with a server default so existing rows are backfilled,
    # then tightened to NOT NULL.
    with op.batch_alter_table("scores") as batch_op:
        batch_op.add_column(
            sa.Column("is_current", sa.Boolean(), nullable=True, server_default=sa.true()),
        )
        batch_op.add_column(
            sa.Column("version", sa.Integer(), nullable=True, server_default="1"),
        )
        batch_op.add_column(sa.Column("valid_from", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("valid_to", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("replaces_score_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_scores_replaces_score_id",
            "scores",
            ["replaces_score_id"],
            ["id"],
        )

    op.execute("UPDATE scores SET is_current = true, version = 1 WHERE is_current IS NULL")
    op.execute("UPDATE scores SET valid_from = thrown_at WHERE valid_from IS NULL")

    with op.batch_alter_table("scores") as batch_op:
        batch_op.alter_column("is_current", nullable=False)
        batch_op.alter_column("version", nullable=False)

    # Reads of live throws always filter on is_current
    op.create_index("ix_scores_is_current", "scores", ["is_current"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_column(inspector, "scores", "is_current"):
        return

    # Without the versioning columns a superseded row is indistinguishable from
    # a real throw, so drop the invalidated versions rather than resurrect them.
    op.execute("DELETE FROM scores WHERE is_current = false")

    if "ix_scores_is_current" in {ix["name"] for ix in inspector.get_indexes("scores")}:
        op.drop_index("ix_scores_is_current", table_name="scores")

    with op.batch_alter_table("scores") as batch_op:
        batch_op.drop_constraint("fk_scores_replaces_score_id", type_="foreignkey")
        batch_op.drop_column("replaces_score_id")
        batch_op.drop_column("valid_to")
        batch_op.drop_column("valid_from")
        batch_op.drop_column("version")
        batch_op.drop_column("is_current")
