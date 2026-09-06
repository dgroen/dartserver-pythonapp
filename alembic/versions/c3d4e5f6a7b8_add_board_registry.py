"""add_board_registry

Adds the Board table (physical vision/electronic boards that produce throws)
and the nullable foreign keys that link players, per-player game results and
individual throws to the board they came from.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-06 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(inspector, table: str, column: str) -> bool:
    if not inspector.has_table(table):
        return False
    return column in {col["name"] for col in inspector.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("board"):
        op.create_table(
            "board",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("external_id", sa.String(length=255), nullable=False),
            sa.Column("kind", sa.String(length=20), nullable=False),
            sa.Column("display_name", sa.String(length=100), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("last_used_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("kind", "external_id", name="uq_board_kind_external_id"),
        )

    # All FKs below are nullable and purely additive - existing rows keep NULL.
    if not _has_column(inspector, "player", "last_board_id"):
        with op.batch_alter_table("player") as batch_op:
            batch_op.add_column(sa.Column("last_board_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_player_last_board_id",
                "board",
                ["last_board_id"],
                ["id"],
            )

    if not _has_column(inspector, "gameresults", "board_id"):
        with op.batch_alter_table("gameresults") as batch_op:
            batch_op.add_column(sa.Column("board_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_gameresults_board_id",
                "board",
                ["board_id"],
                ["id"],
            )

    if not _has_column(inspector, "scores", "board_id"):
        with op.batch_alter_table("scores") as batch_op:
            batch_op.add_column(sa.Column("board_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_scores_board_id",
                "board",
                ["board_id"],
                ["id"],
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_column(inspector, "scores", "board_id"):
        with op.batch_alter_table("scores") as batch_op:
            batch_op.drop_constraint("fk_scores_board_id", type_="foreignkey")
            batch_op.drop_column("board_id")

    if _has_column(inspector, "gameresults", "board_id"):
        with op.batch_alter_table("gameresults") as batch_op:
            batch_op.drop_constraint("fk_gameresults_board_id", type_="foreignkey")
            batch_op.drop_column("board_id")

    if _has_column(inspector, "player", "last_board_id"):
        with op.batch_alter_table("player") as batch_op:
            batch_op.drop_constraint("fk_player_last_board_id", type_="foreignkey")
            batch_op.drop_column("last_board_id")

    if inspector.has_table("board"):
        op.drop_table("board")
