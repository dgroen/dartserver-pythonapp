"""Compatibility shim for RabbitMQConsumer tests.

Provides access to RabbitMQConsumer and any patched dependencies like `pika`
and `time` when tests reference the legacy `rabbitmq_consumer` module path.
"""

import time

try:
    import pika  # type: ignore
except ImportError:  # pragma: no cover - optional dependency in test env
    pika = None  # type: ignore

from dartserver_services.rabbitmq import RabbitMQConsumer

__all__ = ["RabbitMQConsumer", "pika", "time"]
