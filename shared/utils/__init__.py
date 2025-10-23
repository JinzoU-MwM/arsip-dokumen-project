"""
Shared utilities for the AI Legal Document Automation System
"""

from .logging import (
    LogLevel,
    LogCategory,
    configure_logging,
    get_logger,
    log_security_event,
    log_business_event,
    log_performance_event,
    log_api_request,
)
from .config import (
    Environment,
    AppConfig,
    DatabaseConfig,
    RedisConfig,
    OllamaConfig,
    WAHAConfig,
    GoogleDriveConfig,
    SecurityConfig,
    LoggingConfig,
    MonitoringConfig,
    FileProcessingConfig,
    NotificationConfig,
    ConfigManager,
    config_manager,
)

__all__ = [
    "LogLevel",
    "LogCategory",
    "configure_logging",
    "get_logger",
    "log_security_event",
    "log_business_event",
    "log_performance_event",
    "log_api_request",
    "Environment",
    "AppConfig",
    "DatabaseConfig",
    "RedisConfig",
    "OllamaConfig",
    "WAHAConfig",
    "GoogleDriveConfig",
    "SecurityConfig",
    "LoggingConfig",
    "MonitoringConfig",
    "FileProcessingConfig",
    "NotificationConfig",
    "ConfigManager",
    "config_manager",
]