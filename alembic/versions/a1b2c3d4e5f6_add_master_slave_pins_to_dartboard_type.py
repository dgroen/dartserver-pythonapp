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
    op.add_column("dartboard_type", sa.Column("master_pins", sa.Text(), nullable=True))
    op.add_column("dartboard_type", sa.Column("slave_pins", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("dartboard_type", "slave_pins")
    op.drop_column("dartboard_type", "master_pins")
