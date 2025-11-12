"""Unit tests for RabbitMQ consumer."""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.core.rabbitmq_consumer import RabbitMQConsumer


@pytest.fixture
def config():
    """Provide RabbitMQ configuration for testing."""
    return {
        "host": "localhost",
        "port": 5672,
        "user": "guest",
        "password": "guest",
        "vhost": "/",
        "exchange": "test_exchange",
        "topic": "test.topic.#",
    }


@pytest.fixture
def callback():
    """Mock callback function."""
    return Mock()


@pytest.fixture
def consumer(config, callback):
    """Create RabbitMQ consumer instance."""
    return RabbitMQConsumer(config, callback)


class TestRabbitMQConsumer:
    """Test RabbitMQ consumer class."""

    def test_initialization(self, consumer, config, callback):
        """Test consumer initialization."""
        assert consumer.config == config
        assert consumer.callback == callback
        assert consumer.connection is None
        assert consumer.channel is None
        assert consumer.should_stop is False

    @patch("rabbitmq_consumer.pika.BlockingConnection")
    def test_connect_success(self, mock_connection, consumer):
        """Test successful connection to RabbitMQ."""
        # Setup mocks
        mock_conn_instance = MagicMock()
        mock_channel = MagicMock()
        mock_queue_result = MagicMock()
        mock_queue_result.method.queue = "test_queue"

        mock_connection.return_value = mock_conn_instance
        mock_conn_instance.channel.return_value = mock_channel
        mock_channel.queue_declare.return_value = mock_queue_result

        # Connect
        queue_name = consumer.connect()

        # Verify connection was established
        assert consumer.connection == mock_conn_instance
        assert consumer.channel == mock_channel
        assert queue_name == "test_queue"

        # Verify exchange was declared
        mock_channel.exchange_declare.assert_called_once_with(
            exchange="test_exchange",
            exchange_type="topic",
            durable=True,
        )

        # Verify queue was declared
        mock_channel.queue_declare.assert_called_once_with(queue="", exclusive=True)

        # Verify queue was bound
        mock_channel.queue_bind.assert_called_once_with(
            exchange="test_exchange",
            queue="test_queue",
            routing_key="test.topic.#",
        )

    def test_on_message_success(self, consumer, callback):
        """Test successful message processing."""
        # Setup
        mock_channel = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = "test_tag"
        mock_properties = MagicMock()

        message_data = {"score": 20, "multiplier": "TRIPLE"}
        body = json.dumps(message_data).encode("utf-8")

        # Process message
        consumer.on_message(mock_channel, mock_method, mock_properties, body)

        # Verify callback was called
        callback.assert_called_once_with(message_data)

        # Verify message was acknowledged
        mock_channel.basic_ack.assert_called_once_with(delivery_tag="test_tag")

    def test_on_message_json_decode_error(self, consumer, callback):
        """Test message processing with invalid JSON."""
        # Setup
        mock_channel = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = "test_tag"
        mock_properties = MagicMock()

        body = b"invalid json"

        # Process message
        consumer.on_message(mock_channel, mock_method, mock_properties, body)

        # Verify callback was NOT called
        callback.assert_not_called()

        # Verify message was rejected (not requeued)
        mock_channel.basic_nack.assert_called_once_with(
            delivery_tag="test_tag",
            requeue=False,
        )

    def test_on_message_callback_exception(self, consumer, callback):
        """Test message processing when callback raises exception."""
        # Setup
        mock_channel = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = "test_tag"
        mock_properties = MagicMock()

        message_data = {"score": 20, "multiplier": "TRIPLE"}
        body = json.dumps(message_data).encode("utf-8")

        # Make callback raise exception
        callback.side_effect = Exception("Processing error")

        # Process message
        consumer.on_message(mock_channel, mock_method, mock_properties, body)

        # Verify callback was called
        callback.assert_called_once_with(message_data)

        # Verify message was rejected (requeued)
        mock_channel.basic_nack.assert_called_once_with(delivery_tag="test_tag", requeue=True)

    @patch("rabbitmq_consumer.pika.BlockingConnection")
    @patch("rabbitmq_consumer.time.sleep")
    def test_start_with_connection_error(self, mock_sleep, mock_connection, consumer):
        """Test start with connection error and retry."""
        # Setup
        mock_connection.side_effect = [
            Exception("Connection failed"),
            KeyboardInterrupt(),  # Stop after first retry
        ]

        # Start consumer (should handle error and retry)
        # The consumer catches KeyboardInterrupt internally, so it won't raise
        consumer.start()

        # Verify sleep was called for retry
        mock_sleep.assert_called_with(5)

        # Verify stop flag was set
        assert consumer.should_stop is True

    @patch("rabbitmq_consumer.pika.BlockingConnection")
    def test_start_with_keyboard_interrupt(self, mock_connection, consumer):
        """Test start with keyboard interrupt."""
        # Setup
        mock_conn_instance = MagicMock()
        mock_channel = MagicMock()
        mock_queue_result = MagicMock()
        mock_queue_result.method.queue = "test_queue"

        mock_connection.return_value = mock_conn_instance
        mock_conn_instance.channel.return_value = mock_channel
        mock_channel.queue_declare.return_value = mock_queue_result
        mock_channel.start_consuming.side_effect = KeyboardInterrupt()

        # Start consumer
        consumer.start()

        # Verify stop was called
        assert consumer.should_stop is True

    @patch("rabbitmq_consumer.pika.BlockingConnection")
    @patch("rabbitmq_consumer.time.sleep")
    def test_start_with_amqp_connection_error(self, mock_sleep, mock_connection, consumer):
        """Test start with AMQP connection error."""
        import pika

        # Setup
        mock_connection.side_effect = [
            pika.exceptions.AMQPConnectionError("Connection failed"),
            KeyboardInterrupt(),  # Stop after first retry
        ]

        # Start consumer (catches KeyboardInterrupt internally)
        consumer.start()

        # Verify sleep was called for retry
        mock_sleep.assert_called_with(5)

        # Verify stop flag was set
        assert consumer.should_stop is True

    def test_stop(self, consumer):
        """Test stopping the consumer."""
        # Setup
        mock_channel = MagicMock()
        mock_channel.is_open = True
        mock_connection = MagicMock()
        mock_connection.is_open = True

        consumer.channel = mock_channel
        consumer.connection = mock_connection

        # Stop consumer
        consumer.stop()

        # Verify stop flag was set
        assert consumer.should_stop is True

        # Verify channel was stopped
        mock_channel.stop_consuming.assert_called_once()

        # Verify connection was closed
        mock_connection.close.assert_called_once()

    def test_stop_with_closed_channel(self, consumer):
        """Test stopping consumer with already closed channel."""
        # Setup
        mock_channel = MagicMock()
        mock_channel.is_open = False
        mock_connection = MagicMock()
        mock_connection.is_open = False

        consumer.channel = mock_channel
        consumer.connection = mock_connection

        # Stop consumer
        consumer.stop()

        # Verify stop flag was set
        assert consumer.should_stop is True

        # Verify stop_consuming was NOT called (channel closed)
        mock_channel.stop_consuming.assert_not_called()

        # Verify close was NOT called (connection closed)
        mock_connection.close.assert_not_called()

    def test_stop_with_no_connection(self, consumer):
        """Test stopping consumer with no connection."""
        # Stop consumer (no connection established)
        consumer.stop()

        # Verify stop flag was set
        assert consumer.should_stop is True

    def test_on_message_with_user_field(self, consumer, callback):
        """Test message processing with user field."""
        # Setup
        mock_channel = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = "test_tag"
        mock_properties = MagicMock()

        message_data = {"score": 20, "multiplier": "TRIPLE", "user": "Player 1"}
        body = json.dumps(message_data).encode("utf-8")

        # Process message
        consumer.on_message(mock_channel, mock_method, mock_properties, body)

        # Verify callback was called with user field
        callback.assert_called_once_with(message_data)

        # Verify message was acknowledged
        mock_channel.basic_ack.assert_called_once_with(delivery_tag="test_tag")

    def test_on_message_with_empty_body(self, consumer, callback):
        """Test message processing with empty body."""
        # Setup
        mock_channel = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = "test_tag"
        mock_properties = MagicMock()

        body = b""

        # Process message
        consumer.on_message(mock_channel, mock_method, mock_properties, body)

        # Verify callback was NOT called
        callback.assert_not_called()

        # Verify message was rejected
        mock_channel.basic_nack.assert_called_once_with(
            delivery_tag="test_tag",
            requeue=False,
        )

    @patch("rabbitmq_consumer.pika.BlockingConnection")
    def test_connect_with_custom_config(self, mock_connection):
        """Test connection with custom configuration."""
        # Setup custom config
        custom_config = {
            "host": "custom-host",
            "port": 5673,
            "user": "custom_user",
            "password": "custom_pass",
            "vhost": "/custom",
            "exchange": "custom_exchange",
            "topic": "custom.topic",
        }
        callback = Mock()
        consumer = RabbitMQConsumer(custom_config, callback)

        # Setup mocks
        mock_conn_instance = MagicMock()
        mock_channel = MagicMock()
        mock_queue_result = MagicMock()
        mock_queue_result.method.queue = "test_queue"

        mock_connection.return_value = mock_conn_instance
        mock_conn_instance.channel.return_value = mock_channel
        mock_channel.queue_declare.return_value = mock_queue_result

        # Connect
        consumer.connect()

        # Verify connection parameters were used
        call_args = mock_connection.call_args
        assert call_args is not None
