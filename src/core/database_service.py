"""
Database service for persisting game data
"""

import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv

from src.core.database_models import DatabaseManager, GameResult, GameType, Player, Score

load_dotenv()


class DatabaseService:
    """Service for handling all database operations"""

    def __init__(self, database_url=None):
        """
        Initialize database service

        Args:
            database_url: PostgreSQL connection URL (optional, reads from env if not provided)
        """
        if database_url is None:
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://postgres:postgres@localhost:5432/dartsdb",
            )

        self.db_manager = DatabaseManager(database_url)
        self.current_game_session_id = None
        self.current_game_results = {}  # Map player_id to GameResult.id
        self.throw_counters = {}  # Track throw sequence per player

    def initialize_database(self):
        """Initialize database tables"""
        self.db_manager.create_tables()
        self._ensure_game_types_exist()

    def _ensure_game_types_exist(self):
        """Ensure all game types exist in the database"""
        session = self.db_manager.get_session()
        try:
            game_types = [
                {"name": "301", "description": "301 darts game"},
                {"name": "401", "description": "401 darts game"},
                {"name": "501", "description": "501 darts game"},
                {"name": "cricket", "description": "Cricket darts game"},
            ]

            for gt_data in game_types:
                existing = session.query(GameType).filter_by(name=gt_data["name"]).first()
                if not existing:
                    game_type = GameType(**gt_data)
                    session.add(game_type)

            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error ensuring game types exist: {e}")
        finally:
            session.close()

    def start_new_game(self, game_type_name, player_names, start_score=None, double_out=False):
        """
        Start a new game and create database records

        Args:
            game_type_name: Name of the game type ('301', '401', '501', 'cricket')
            player_names: List of player names
            start_score: Starting score for 301/401/501 games
            double_out: Whether double-out is enabled

        Returns:
            game_session_id: UUID for this game session
        """
        session = self.db_manager.get_session()
        try:
            # Generate new game session ID
            self.current_game_session_id = str(uuid.uuid4())
            self.current_game_results = {}
            self.throw_counters = {}

            # Get or create game type
            game_type = session.query(GameType).filter_by(name=game_type_name).first()
            if not game_type:
                game_type = GameType(
                    name=game_type_name,
                    description=f"{game_type_name} darts game",
                )
                session.add(game_type)
                session.flush()

            # Create or get players and game results
            for player_order, player_name in enumerate(player_names):
                # Get or create player
                player = session.query(Player).filter_by(name=player_name).first()
                if not player:
                    player = Player(name=player_name)
                    session.add(player)
                    session.flush()

                # Create game result for this player
                game_result = GameResult(
                    game_type_id=game_type.id,
                    player_id=player.id,
                    player_order=player_order,
                    start_score=start_score,
                    final_score=start_score if start_score else 0,
                    double_out_enabled=double_out,
                    game_session_id=self.current_game_session_id,
                    started_at=datetime.now(tz=timezone.utc),
                )
                session.add(game_result)
                session.flush()

                # Store mapping
                self.current_game_results[player_order] = game_result.id
                self.throw_counters[player_order] = 0

            session.commit()
            print(f"New game started: session_id={self.current_game_session_id}")
            return self.current_game_session_id

        except Exception as e:
            session.rollback()
            print(f"Error starting new game: {e}")
            raise
        finally:
            session.close()

    def record_throw(
        self,
        player_id,
        base_score,
        multiplier,
        multiplier_value,
        actual_score,
        score_before,
        score_after,
        turn_number,
        throw_in_turn,
        dartboard_sends_actual_score,
        is_bust=False,
        is_finish=False,
    ):
        """
        Record a single throw in the database

        Args:
            player_id: Player ID (0-based index in game)
            base_score: Base score value
            multiplier: Multiplier type string
            multiplier_value: Numeric multiplier value
            actual_score: Calculated actual score
            score_before: Score before this throw
            score_after: Score after this throw
            turn_number: Turn number
            throw_in_turn: Position in turn (1, 2, or 3)
            dartboard_sends_actual_score: Config setting
            is_bust: Whether this throw resulted in a bust
            is_finish: Whether this throw won the game
        """
        if self.current_game_session_id is None:
            print("No active game session")
            return

        if player_id not in self.current_game_results:
            print(f"Player {player_id} not in current game")
            return

        session = self.db_manager.get_session()
        try:
            game_result_id = self.current_game_results[player_id]

            # Increment throw counter
            self.throw_counters[player_id] += 1
            throw_sequence = self.throw_counters[player_id]

            # Get the actual player database ID
            game_result = session.query(GameResult).filter_by(id=game_result_id).first()
            if not game_result:
                print(f"Game result not found: {game_result_id}")
                return

            # Create score record
            score = Score(
                game_result_id=game_result_id,
                player_id=game_result.player_id,
                throw_sequence=throw_sequence,
                turn_number=turn_number,
                throw_in_turn=throw_in_turn,
                base_score=base_score,
                multiplier=multiplier,
                multiplier_value=multiplier_value,
                actual_score=actual_score,
                score_before=score_before,
                score_after=score_after,
                dartboard_sends_actual_score=dartboard_sends_actual_score,
                is_bust=is_bust,
                is_finish=is_finish,
                thrown_at=datetime.now(tz=timezone.utc),
            )

            session.add(score)
            session.commit()

            print(
                f"Throw recorded: player={player_id}, seq={throw_sequence}, "
                f"score={actual_score}, bust={is_bust}, finish={is_finish}",
            )

        except Exception as e:
            session.rollback()
            print(f"Error recording throw: {e}")
        finally:
            session.close()

    def update_player_score(self, player_id, final_score):
        """
        Update player's final score in game result

        Args:
            player_id: Player ID (0-based index in game)
            final_score: Current/final score
        """
        if self.current_game_session_id is None or player_id not in self.current_game_results:
            return

        session = self.db_manager.get_session()
        try:
            game_result_id = self.current_game_results[player_id]
            game_result = session.query(GameResult).filter_by(id=game_result_id).first()

            if game_result:
                game_result.final_score = final_score
                session.commit()

        except Exception as e:
            session.rollback()
            print(f"Error updating player score: {e}")
        finally:
            session.close()

    def mark_winner(self, player_id):
        """
        Mark a player as winner and finish the game

        Args:
            player_id: Player ID (0-based index in game)
        """
        if self.current_game_session_id is None or player_id not in self.current_game_results:
            return

        session = self.db_manager.get_session()
        try:
            # Mark winner
            game_result_id = self.current_game_results[player_id]
            game_result = session.query(GameResult).filter_by(id=game_result_id).first()

            if game_result:
                game_result.is_winner = True
                game_result.finished_at = datetime.now(tz=timezone.utc)

            # Update finished_at for all players in this game session
            all_results = (
                session.query(GameResult)
                .filter_by(game_session_id=self.current_game_session_id)
                .all()
            )

            for result in all_results:
                if result.finished_at is None:
                    result.finished_at = datetime.now(tz=timezone.utc)

            session.commit()
            print(f"Winner marked: player={player_id}, session={self.current_game_session_id}")

        except Exception as e:
            session.rollback()
            print(f"Error marking winner: {e}")
        finally:
            session.close()

    def undo_throws_for_bust(self, player_id, throw_count):
        """
        Remove the last N throws for a player (for bust handling)

        Args:
            player_id: Player ID (0-based index in game)
            throw_count: Number of throws to remove
        """
        if self.current_game_session_id is None or player_id not in self.current_game_results:
            return

        session = self.db_manager.get_session()
        try:
            game_result_id = self.current_game_results[player_id]

            # Get the last N throws for this player
            throws = (
                session.query(Score)
                .filter_by(game_result_id=game_result_id)
                .order_by(Score.throw_sequence.desc())
                .limit(throw_count)
                .all()
            )

            # Delete them
            for throw in throws:
                session.delete(throw)

            # Update throw counter
            self.throw_counters[player_id] -= throw_count

            session.commit()
            print(f"Undid {throw_count} throw(s) for player {player_id}")

        except Exception as e:
            session.rollback()
            print(f"Error undoing throws: {e}")
        finally:
            session.close()

    def get_game_replay_data(self, game_session_id):
        """
        Get all data needed to replay a game

        Args:
            game_session_id: UUID of the game session

        Returns:
            Dictionary with game data and all throws in sequence
        """
        session = self.db_manager.get_session()
        try:
            # Get all game results for this session
            game_results = (
                session.query(GameResult).filter_by(game_session_id=game_session_id).all()
            )

            if not game_results:
                return None

            # Get game type
            game_type = session.query(GameType).filter_by(id=game_results[0].game_type_id).first()

            # Build player info
            players = []
            for gr in sorted(game_results, key=lambda x: x.player_order):
                player = session.query(Player).filter_by(id=gr.player_id).first()
                players.append(
                    {
                        "player_order": gr.player_order,
                        "player_id": gr.player_id,
                        "player_name": player.name,
                        "start_score": gr.start_score,
                        "final_score": gr.final_score,
                        "is_winner": gr.is_winner,
                    },
                )

            # Get all throws for this game, ordered by timestamp
            all_throws = []
            for gr in game_results:
                throws = (
                    session.query(Score)
                    .filter_by(game_result_id=gr.id)
                    .order_by(Score.thrown_at)
                    .all()
                )

                for throw in throws:
                    all_throws.append(
                        {
                            "player_order": gr.player_order,
                            "player_name": session.query(Player)
                            .filter_by(id=throw.player_id)
                            .first()
                            .name,
                            "throw_sequence": throw.throw_sequence,
                            "turn_number": throw.turn_number,
                            "throw_in_turn": throw.throw_in_turn,
                            "base_score": throw.base_score,
                            "multiplier": throw.multiplier,
                            "multiplier_value": throw.multiplier_value,
                            "actual_score": throw.actual_score,
                            "score_before": throw.score_before,
                            "score_after": throw.score_after,
                            "dartboard_sends_actual_score": throw.dartboard_sends_actual_score,
                            "is_bust": throw.is_bust,
                            "is_finish": throw.is_finish,
                            "thrown_at": throw.thrown_at.isoformat(),
                        },
                    )

            # Sort all throws by timestamp
            all_throws.sort(key=lambda x: x["thrown_at"])

            return {
                "game_session_id": game_session_id,
                "game_type": game_type.name,
                "double_out_enabled": game_results[0].double_out_enabled,
                "started_at": game_results[0].started_at.isoformat(),
                "finished_at": (
                    game_results[0].finished_at.isoformat() if game_results[0].finished_at else None
                ),
                "players": players,
                "throws": all_throws,
            }

        except Exception as e:
            print(f"Error getting game replay data: {e}")
            return None
        finally:
            session.close()

    def get_recent_games(self, limit=10):
        """
        Get recent game sessions

        Args:
            limit: Maximum number of games to return

        Returns:
            List of game session summaries
        """
        session = self.db_manager.get_session()
        try:
            # Get unique game sessions with their start times
            # Use a subquery to get the max started_at for each game_session_id
            from sqlalchemy import func

            subquery = (
                session.query(
                    GameResult.game_session_id,
                    func.max(GameResult.started_at).label("max_started_at"),
                )
                .group_by(GameResult.game_session_id)
                .order_by(func.max(GameResult.started_at).desc())
                .limit(limit)
                .subquery()
            )

            game_sessions = session.query(
                subquery.c.game_session_id,
                subquery.c.max_started_at,
            ).all()

            results = []
            for game_session_id, _ in game_sessions:
                game_results = (
                    session.query(GameResult).filter_by(game_session_id=game_session_id).all()
                )

                if game_results:
                    game_type = (
                        session.query(GameType).filter_by(id=game_results[0].game_type_id).first()
                    )
                    winner = next((gr for gr in game_results if gr.is_winner), None)
                    winner_name = None
                    if winner:
                        winner_player = session.query(Player).filter_by(id=winner.player_id).first()
                        winner_name = winner_player.name if winner_player else None

                    results.append(
                        {
                            "game_session_id": game_session_id,
                            "game_type": game_type.name,
                            "player_count": len(game_results),
                            "winner": winner_name,
                            "started_at": game_results[0].started_at.isoformat(),
                            "finished_at": (
                                game_results[0].finished_at.isoformat()
                                if game_results[0].finished_at
                                else None
                            ),
                        },
                    )

            return results

        except Exception as e:
            print(f"Error getting recent games: {e}")
            return []
        finally:
            session.close()

    def get_or_create_player(self, username, email=None, name=None):
        """
        Get or create a player from username

        Args:
            username: Username from authentication
            email: Email address (optional)
            name: Display name (optional, defaults to username)

        Returns:
            Player object
        """
        session = self.db_manager.get_session()
        try:
            # Try to find by username first
            player = session.query(Player).filter_by(username=username).first()

            if not player:
                # Create new player
                player = Player(
                    name=name or username,
                    username=username,
                    email=email,
                    created_at=datetime.now(tz=timezone.utc),
                )
                session.add(player)
                session.commit()
                print(f"New player created: {username} (name: {player.name})")
            else:
                print(f"Player found: {username}")

            return player

        except Exception as e:
            session.rollback()
            print(f"Error getting or creating player: {e}")
            return None
        finally:
            session.close()

    def get_player_game_history(self, player_id, game_type=None, limit=50):
        """
        Get a player's game history with statistics

        Args:
            player_id: Player ID
            game_type: Optional game type filter ('301', '401', '501', 'cricket')
            limit: Maximum number of games to return

        Returns:
            List of game results with player statistics
        """
        session = self.db_manager.get_session()
        try:
            query = session.query(GameResult).filter_by(player_id=player_id)

            if game_type:
                game_type_obj = session.query(GameType).filter_by(name=game_type).first()
                if game_type_obj:
                    query = query.filter_by(game_type_id=game_type_obj.id)

            game_results = query.order_by(GameResult.finished_at.desc()).limit(limit).all()

            results = []
            for gr in game_results:
                game_type_obj = session.query(GameType).filter_by(id=gr.game_type_id).first()
                game_session_results = (
                    session.query(GameResult).filter_by(game_session_id=gr.game_session_id).all()
                )

                # Get all players in this game
                players_in_game = []
                for game_result in game_session_results:
                    player = session.query(Player).filter_by(id=game_result.player_id).first()
                    players_in_game.append(
                        {
                            "name": player.name if player else "Unknown",
                            "final_score": game_result.final_score,
                            "is_winner": game_result.is_winner,
                        },
                    )

                results.append(
                    {
                        "game_session_id": gr.game_session_id,
                        "game_type": game_type_obj.name if game_type_obj else "Unknown",
                        "started_at": gr.started_at.isoformat(),
                        "finished_at": gr.finished_at.isoformat() if gr.finished_at else None,
                        "is_winner": gr.is_winner,
                        "final_score": gr.final_score,
                        "start_score": gr.start_score,
                        "player_count": len(players_in_game),
                        "players": players_in_game,
                        "double_out_enabled": gr.double_out_enabled,
                    },
                )

            return results

        except Exception as e:
            print(f"Error getting player game history: {e}")
            return []
        finally:
            session.close()

    def get_player_statistics(self, player_id):
        """
        Get overall statistics for a player

        Args:
            player_id: Player ID

        Returns:
            Dictionary with player statistics
        """
        session = self.db_manager.get_session()
        try:
            player = session.query(Player).filter_by(id=player_id).first()
            if not player:
                return None

            all_game_results = session.query(GameResult).filter_by(player_id=player_id).all()

            if not all_game_results:
                return {
                    "player_id": player_id,
                    "player_name": player.name,
                    "total_games": 0,
                    "wins": 0,
                    "losses": 0,
                    "win_rate": 0,
                    "average_score": 0,
                    "by_game_type": {},
                }

            total_games = len(all_game_results)
            wins = sum(1 for gr in all_game_results if gr.is_winner)
            losses = total_games - wins
            average_score = sum(gr.final_score or 0 for gr in all_game_results) / total_games

            # Stats by game type
            by_game_type = {}
            for gr in all_game_results:
                game_type = session.query(GameType).filter_by(id=gr.game_type_id).first()
                game_type_name = game_type.name if game_type else "Unknown"

                if game_type_name not in by_game_type:
                    by_game_type[game_type_name] = {
                        "games": 0,
                        "wins": 0,
                        "losses": 0,
                        "average_score": 0,
                        "scores": [],
                    }

                by_game_type[game_type_name]["games"] += 1
                by_game_type[game_type_name]["wins"] += 1 if gr.is_winner else 0
                by_game_type[game_type_name]["losses"] += 0 if gr.is_winner else 1
                by_game_type[game_type_name]["scores"].append(gr.final_score or 0)

            # Calculate averages per game type
            for _game_type_name, stats in by_game_type.items():
                if stats["scores"]:
                    stats["average_score"] = sum(stats["scores"]) / len(stats["scores"])
                del stats["scores"]  # Remove scores list from final output

            return {
                "player_id": player_id,
                "player_name": player.name,
                "total_games": total_games,
                "wins": wins,
                "losses": losses,
                "win_rate": round((wins / total_games * 100), 1) if total_games > 0 else 0,
                "average_score": round(average_score, 1),
                "by_game_type": by_game_type,
            }

        except Exception as e:
            print(f"Error getting player statistics: {e}")
            return None
        finally:
            session.close()

    def get_active_games(self):
        """
        Get currently active games with their current state

        Returns:
            List of active games with current scores and player info
        """
        session = self.db_manager.get_session()
        try:
            # Get game sessions that have started but not finished
            from sqlalchemy import and_

            active_games_query = (
                session.query(GameResult.game_session_id)
                .filter(
                    and_(
                        GameResult.started_at.isnot(None),
                        GameResult.finished_at.isnull(),
                    ),
                )
                .group_by(GameResult.game_session_id)
                .all()
            )

            results = []
            for (game_session_id,) in active_games_query:
                game_results = (
                    session.query(GameResult).filter_by(game_session_id=game_session_id).all()
                )

                if game_results:
                    game_type = (
                        session.query(GameType).filter_by(id=game_results[0].game_type_id).first()
                    )

                    players = []
                    for gr in sorted(game_results, key=lambda x: x.player_order):
                        player = session.query(Player).filter_by(id=gr.player_id).first()
                        players.append(
                            {
                                "player_id": gr.player_id,
                                "player_name": player.name if player else "Unknown",
                                "current_score": gr.final_score,
                                "start_score": gr.start_score,
                                "is_winner": gr.is_winner,
                            },
                        )

                    results.append(
                        {
                            "game_session_id": game_session_id,
                            "game_type": game_type.name if game_type else "Unknown",
                            "started_at": game_results[0].started_at.isoformat(),
                            "player_count": len(players),
                            "players": players,
                            "double_out_enabled": game_results[0].double_out_enabled,
                        },
                    )

            return results

        except Exception as e:
            print(f"Error getting active games: {e}")
            return []
        finally:
            session.close()
