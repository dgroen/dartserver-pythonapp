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
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("dartboard_type"):
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
            sa.Column("master_pins", sa.Text(), nullable=True),
            sa.Column("slave_pins", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )
        return

    columns = {column["name"] for column in inspector.get_columns("dartboard_type")}

    if "master_pins" not in columns:
        op.add_column("dartboard_type", sa.Column("master_pins", sa.Text(), nullable=True))
    if "slave_pins" not in columns:
        op.add_column("dartboard_type", sa.Column("slave_pins", sa.Text(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("dartboard_type"):
        return

    columns = {column["name"] for column in inspector.get_columns("dartboard_type")}

    if "slave_pins" in columns:
        op.drop_column("dartboard_type", "slave_pins")
    if "master_pins" in columns:
        op.drop_column("dartboard_type", "master_pins")
