"""add_training_mode_tables

Revision ID: ad03fe01b8c6
Revises: e1a2b3c4d5e6
Create Date: 2025-11-09 11:11:07.781925

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad03fe01b8c6'
down_revision: Union[str, None] = 'e1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create training_session table
    op.create_table(
        'training_session',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('game_type_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('start_score', sa.Integer(), nullable=True),
        sa.Column('final_score', sa.Integer(), nullable=True),
        sa.Column('double_out_enabled', sa.Boolean(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['game_type_id'], ['gametype.id'], ),
        sa.ForeignKeyConstraint(['player_id'], ['player.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )

    # Create training_score table
    op.create_table(
        'training_score',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('training_session_id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('throw_sequence', sa.Integer(), nullable=False),
        sa.Column('turn_number', sa.Integer(), nullable=False),
        sa.Column('throw_in_turn', sa.Integer(), nullable=False),
        sa.Column('base_score', sa.Integer(), nullable=False),
        sa.Column('multiplier', sa.String(length=20), nullable=False),
        sa.Column('multiplier_value', sa.Integer(), nullable=False),
        sa.Column('actual_score', sa.Integer(), nullable=False),
        sa.Column('score_before', sa.Integer(), nullable=False),
        sa.Column('score_after', sa.Integer(), nullable=False),
        sa.Column('dartboard_sends_actual_score', sa.Boolean(), nullable=False),
        sa.Column('is_bust', sa.Boolean(), nullable=True),
        sa.Column('is_finish', sa.Boolean(), nullable=True),
        sa.Column('thrown_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['player_id'], ['player.id'], ),
        sa.ForeignKeyConstraint(['training_session_id'], ['training_session.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('training_score')
    op.drop_table('training_session')
