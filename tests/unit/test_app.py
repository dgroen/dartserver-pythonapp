"""Unit tests for app.py module."""

import os
from unittest.mock import MagicMock, patch

from src.app.app import on_score_received


class TestAppModule:
    """Test app module functions."""

    def test_on_score_received(self):
        """Test on_score_received callback function."""
        # Setup
        with patch("src.app.app.game_manager") as mock_game_manager:
            score_data = {"score": 20, "multiplier": "TRIPLE"}

            # Call callback
            on_score_received(score_data)

            # Verify game_manager.process_score was called
            mock_game_manager.process_score.assert_called_once_with(score_data)

    @patch("src.app.app.RabbitMQConsumer")
    @patch("src.app.app.threading.Thread")
    def test_start_rabbitmq_consumer_success(self, mock_thread, mock_consumer_class):
        """Test successful RabbitMQ consumer start."""
        from src.app.app import start_rabbitmq_consumer

        # Setup mocks
        mock_consumer_instance = MagicMock()
        mock_consumer_class.return_value = mock_consumer_instance
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        # Start consumer
        start_rabbitmq_consumer()

        # Verify consumer was created
        assert mock_consumer_class.called

        # Verify thread was created and started
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

    @patch("src.app.app.RabbitMQConsumer")
    def test_start_rabbitmq_consumer_failure(self, mock_consumer_class):
        """Test RabbitMQ consumer start with failure."""
        from src.app.app import start_rabbitmq_consumer

        # Setup mock to raise exception
        mock_consumer_class.side_effect = Exception("Connection failed")

        # Start consumer (should handle exception gracefully)
        start_rabbitmq_consumer()

        # Should not raise exception

    @patch.dict(os.environ, {}, clear=True)
    @patch("src.app.app.RabbitMQConsumer")
    @patch("src.app.app.threading.Thread")
    def test_start_rabbitmq_consumer_default_config(self, mock_thread, mock_consumer_class):
        """Test RabbitMQ consumer with default configuration."""
        from src.app.app import start_rabbitmq_consumer

        # Setup mocks
        mock_consumer_instance = MagicMock()
        mock_consumer_class.return_value = mock_consumer_instance
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        # Start consumer
        start_rabbitmq_consumer()

        # Verify consumer was created with default config
        call_args = mock_consumer_class.call_args
        config = call_args[0][0]

        assert config["host"] == "localhost"
        assert config["port"] == 5672
        assert config["user"] == "guest"
        assert config["password"] == "guest"
        assert config["vhost"] == "/"
        assert config["exchange"] == "darts_exchange"
        assert config["topic"] == "darts.scores.#"

    @patch.dict(
        os.environ,
        {
            "RABBITMQ_HOST": "custom-host",
            "RABBITMQ_PORT": "5673",
            "RABBITMQ_USER": "custom_user",
            "RABBITMQ_PASSWORD": "custom_pass",
            "RABBITMQ_VHOST": "/custom",
            "RABBITMQ_EXCHANGE": "custom_exchange",
            "RABBITMQ_TOPIC": "custom.topic",
        },
    )
    @patch("src.app.app.RabbitMQConsumer")
    @patch("src.app.app.threading.Thread")
    def test_start_rabbitmq_consumer_custom_config(self, mock_thread, mock_consumer_class):
        """Test RabbitMQ consumer with custom configuration."""
        from src.app.app import start_rabbitmq_consumer

        # Setup mocks
        mock_consumer_instance = MagicMock()
        mock_consumer_class.return_value = mock_consumer_instance
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        # Start consumer
        start_rabbitmq_consumer()

        # Verify consumer was created with custom config
        call_args = mock_consumer_class.call_args
        config = call_args[0][0]

        assert config["host"] == "custom-host"
        assert config["port"] == 5673
        assert config["user"] == "custom_user"
        assert config["password"] == "custom_pass"
        assert config["vhost"] == "/custom"
        assert config["exchange"] == "custom_exchange"
        assert config["topic"] == "custom.topic"
