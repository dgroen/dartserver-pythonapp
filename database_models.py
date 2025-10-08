"""
Database models for storing game data in PostgreSQL
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class Player(Base):
    """Player table - stores player information"""

    __tablename__ = "player"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    game_results = relationship("GameResult", back_populates="player")
    scores = relationship("Score", back_populates="player")

    def __repr__(self):
        return f"<Player(id={self.id}, name='{self.name}')>"


class GameType(Base):
    """GameType table - stores different game types"""

    __tablename__ = "gametype"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)  # '301', '401', '501', 'cricket'
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    game_results = relationship("GameResult", back_populates="game_type")

    def __repr__(self):
        return f"<GameType(id={self.id}, name='{self.name}')>"


class GameResult(Base):
    """GameResult table - stores information about each game played"""

    __tablename__ = "gameresults"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_type_id = Column(Integer, ForeignKey("gametype.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("player.id"), nullable=False)
    player_order = Column(Integer, nullable=False)  # Order of player in the game (0, 1, 2, etc.)
    start_score = Column(Integer)  # Starting score for 301/401/501 games
    final_score = Column(Integer)  # Final score
    is_winner = Column(Boolean, default=False)
    double_out_enabled = Column(Boolean, default=False)  # For 301/401/501 games
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    game_session_id = Column(String(100), nullable=False)  # UUID to group players in same game

    # Relationships
    game_type = relationship("GameType", back_populates="game_results")
    player = relationship("Player", back_populates="game_results")
    scores = relationship("Score", back_populates="game_result", cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f"<GameResult(id={self.id}, game_session={self.game_session_id}, "
            f"player_id={self.player_id}, is_winner={self.is_winner})>"
        )


class Score(Base):
    """
    Score table - stores each throw in detail for game replay capability
    """

    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_result_id = Column(Integer, ForeignKey("gameresults.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("player.id"), nullable=False)

    # Throw details
    throw_sequence = Column(
        Integer,
        nullable=False,
    )  # Overall throw sequence in game for this player
    turn_number = Column(Integer, nullable=False)  # Which turn (1, 2, 3, ...)
    throw_in_turn = Column(Integer, nullable=False)  # Position in turn (1, 2, or 3)

    # Score details
    base_score = Column(Integer, nullable=False)  # Base score (0-20 or 25 for bull)
    multiplier = Column(String(20), nullable=False)  # SINGLE, DOUBLE, TRIPLE, BULL, DBLBULL
    multiplier_value = Column(Integer, nullable=False)  # 1, 2, or 3
    actual_score = Column(Integer, nullable=False)  # base_score * multiplier_value
    score_before = Column(Integer, nullable=False)  # Score before this throw
    score_after = Column(Integer, nullable=False)  # Score after this throw

    # Configuration and state
    dartboard_sends_actual_score = Column(Boolean, nullable=False)  # Config at time of throw
    is_bust = Column(Boolean, default=False)
    is_finish = Column(Boolean, default=False)  # Winning throw

    # Timestamp
    thrown_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    game_result = relationship("GameResult", back_populates="scores")
    player = relationship("Player", back_populates="scores")

    def __repr__(self):
        return (
            f"<Score(id={self.id}, player_id={self.player_id}, "
            f"throw_seq={self.throw_sequence}, score={self.actual_score})>"
        )


class DatabaseManager:
    """Manager class for database operations"""

    def __init__(self, database_url):
        """
        Initialize database manager

        Args:
            database_url: PostgreSQL connection URL
        """
        self.engine = create_engine(database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        """Create all tables in the database"""
        Base.metadata.create_all(self.engine)

    def drop_tables(self):
        """Drop all tables in the database"""
        Base.metadata.drop_all(self.engine)

    def get_session(self):
        """Get a new database session"""
        return self.Session()
