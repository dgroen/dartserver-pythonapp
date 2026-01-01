"""
Add master_pins and slave_pins columns to dartboard_type table
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "f1a2b3c4d5e7"
branch_labels = None
depends_on = None


def upgrade():
    # Create dartboard_type table if it doesn't exist
    op.create_table(
        "dartboard_type",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("brand", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create dartboard_zone_mapping table if it doesn't exist
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

    # Add master_pins and slave_pins columns to dartboard_type (if intended)
    op.add_column("dartboard_type", sa.Column("master_pins", sa.Text(), nullable=True))
    op.add_column("dartboard_type", sa.Column("slave_pins", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("dartboard_type", "slave_pins")
    op.drop_column("dartboard_type", "master_pins")
    op.drop_table("dartboard_zone_mapping")
    op.drop_table("dartboard_type")
