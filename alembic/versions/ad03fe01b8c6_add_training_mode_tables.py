"""add_training_mode_tables

Revision ID: ad03fe01b8c6
Revises: e1a2b3c4d5e6
Create Date: 2025-11-09 11:11:07.781925

"""

from collections.abc import Sequence

from alembic import op

revision: str = "ad03fe01b8c6"
down_revision: str | None = "e1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS training_session (
            id SERIAL NOT NULL,
            player_id INTEGER NOT NULL,
            game_type_id INTEGER NOT NULL,
            session_id VARCHAR(100) NOT NULL,
            start_score INTEGER,
            final_score INTEGER,
            double_out_enabled BOOLEAN,
            completed BOOLEAN,
            started_at TIMESTAMP WITHOUT TIME ZONE,
            finished_at TIMESTAMP WITHOUT TIME ZONE,
            PRIMARY KEY (id),
            FOREIGN KEY(game_type_id) REFERENCES gametype (id),
            FOREIGN KEY(player_id) REFERENCES player (id),
            UNIQUE (session_id)
        )
    """,
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS training_score (
            id SERIAL NOT NULL,
            training_session_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            throw_sequence INTEGER NOT NULL,
            turn_number INTEGER NOT NULL,
            throw_in_turn INTEGER NOT NULL,
            base_score INTEGER NOT NULL,
            multiplier VARCHAR(20) NOT NULL,
            multiplier_value INTEGER NOT NULL,
            actual_score INTEGER NOT NULL,
            score_before INTEGER NOT NULL,
            score_after INTEGER NOT NULL,
            dartboard_sends_actual_score BOOLEAN NOT NULL,
            is_bust BOOLEAN,
            is_finish BOOLEAN,
            thrown_at TIMESTAMP WITHOUT TIME ZONE,
            PRIMARY KEY (id),
            FOREIGN KEY(player_id) REFERENCES player (id),
            FOREIGN KEY(training_session_id) REFERENCES training_session (id)
        )
    """,
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS training_score")
    op.execute("DROP TABLE IF EXISTS training_session")
