"""
Dartserver Services - Background services for Darts application

Provides RabbitMQ message consumer, TTS service, Dartboard mapping service,
and Mobile app service management.
"""

from dartserver_services.dartboard_service import DartboardMappingError, DartboardService
from dartserver_services.mobile_service import MobileService
from dartserver_services.rabbitmq import RabbitMQConsumer
from dartserver_services.tts_service import TTSService

__version__ = "1.0.0"
__all__ = [
    "RabbitMQConsumer",
    "TTSService",
    "DartboardService",
    "DartboardMappingError",
    "MobileService",
]
