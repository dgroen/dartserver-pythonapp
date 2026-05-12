"""add_dartboard_zone_mapping_table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-02 20:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("dartboard_zone_mapping"):
        op.create_table(
            "dartboard_zone_mapping",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("dartboard_type_id", sa.Integer(), nullable=False),
            sa.Column("master_pin", sa.Integer(), nullable=False),
            sa.Column("slave_pin", sa.Integer(), nullable=False),
            sa.Column("zone_number", sa.Integer(), nullable=False),
            sa.Column("multiplier_type", sa.String(length=20), nullable=False),
            sa.Column("base_value", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["dartboard_type_id"], ["dartboard_type.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    indexes = {index["name"] for index in inspector.get_indexes("dartboard_zone_mapping")}
    if "ix_dartboard_zone_mapping_dartboard_type_id" not in indexes:
        op.create_index(
            "ix_dartboard_zone_mapping_dartboard_type_id",
            "dartboard_zone_mapping",
            ["dartboard_type_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("dartboard_zone_mapping"):
        indexes = {index["name"] for index in inspector.get_indexes("dartboard_zone_mapping")}
        if "ix_dartboard_zone_mapping_dartboard_type_id" in indexes:
            op.drop_index(
                "ix_dartboard_zone_mapping_dartboard_type_id",
                table_name="dartboard_zone_mapping",
            )
        op.drop_table("dartboard_zone_mapping")
