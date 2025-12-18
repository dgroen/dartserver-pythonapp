"""add_mobile_app_tables

Revision ID: d55f29e75045
Revises: 95f33c1ce707
Create Date: 2025-10-10 14:53:05.633053

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d55f29e75045"
down_revision: str | None = "95f33c1ce707"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add username and email columns to Player table
    op.add_column("player", sa.Column("username", sa.String(length=100), nullable=True))
    op.add_column("player", sa.Column("email", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_player_username"), "player", ["username"], unique=True)
    op.create_index(op.f("ix_player_email"), "player", ["email"], unique=False)

    # Create Dartboard table
    op.create_table(
        "dartboard",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("dartboard_id", sa.String(length=100), nullable=False),
        sa.Column("wpa_key", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("is_connected", sa.Boolean(), nullable=True),
        sa.Column("last_connected_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["player_id"], ["player.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_dartboard_dartboard_id"), "dartboard", ["dartboard_id"], unique=True)

    # Create ApiKey table
    op.create_table(
        "api_key",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("key_hash", sa.String(length=255), nullable=False),
        sa.Column("key_prefix", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["player_id"], ["player.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_api_key_key_hash"), "api_key", ["key_hash"], unique=True)

    # Create HotspotConfig table
    op.create_table(
        "hotspot_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("dartboard_id", sa.String(length=100), nullable=False),
        sa.Column("wpa_key", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["player_id"], ["player.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    # Drop HotspotConfig table
    op.drop_table("hotspot_config")

    # Drop ApiKey table
    op.drop_index(op.f("ix_api_key_key_hash"), table_name="api_key")
    op.drop_table("api_key")

    # Drop Dartboard table
    op.drop_index(op.f("ix_dartboard_dartboard_id"), table_name="dartboard")
    op.drop_table("dartboard")

    # Remove columns from Player table
    op.drop_index(op.f("ix_player_email"), table_name="player")
    op.drop_index(op.f("ix_player_username"), table_name="player")
    op.drop_column("player", "email")
    op.drop_column("player", "username")
