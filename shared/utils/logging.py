"""
Structured logging configuration and utilities for the AI Legal Document Automation System
"""

import os
import sys
import json
import logging
import logging.handlers
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum
import structlog
from pythonjsonlogger import jsonlogger

logger = structlog.get_logger()


class LogLevel(Enum):
    """Log levels for the application"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogCategory(Enum):
    """Log categories for better organization"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DOCUMENT_PROCESSING = "document_processing"
    AI_PROCESSING = "ai_processing"
    NOTIFICATION = "notification"
    DATABASE = "database"
    API = "api"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    SYSTEM = "system"
    BUSINESS = "business"


class CustomJSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""

    def add_fields(self, log_record: Dict[str, Any]) -> Dict[str, Any]:
        """Add custom fields to log record"""
        # Add timestamp in ISO format
        if "asctime" in log_record:
            log_record["timestamp"] = datetime.fromisoformat(log_record["asctime"]).isoformat()
            del log_record["asctime"]

        # Add service information
        log_record["service"] = os.getenv("SERVICE_NAME", "legal-automation")
        log_record["environment"] = os.getenv("NODE_ENV", "development")
        log_record["version"] = os.getenv("APP_VERSION", "1.0.0")

        # Add process and thread info
        log_record["process_id"] = os.getpid()
        log_record["thread_id"] = log_record.get("thread", "")

        # Add file and line number
        if "pathname" in log_record:
            log_record["file"] = os.path.basename(log_record["pathname"])
            del log_record["pathname"]

        return log_record


class LogMaskingProcessor:
    """Processor for masking sensitive information in logs"""

    def __init__(self):
        self.sensitive_fields = [
            "password", "token", "secret", "key", "credential",
            "authorization", "auth", "bearer", "api_key",
            "ssn", "social_security", "tax_id", "credit_card",
            "bank_account", "email", "phone", "address"
        ]

    def __call__(self, logger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Process log event and mask sensitive information"""
        try:
            masked_event = event_dict.copy()

            # Mask sensitive fields in the event
            for key, value in masked_event.items():
                if isinstance(value, str):
                    masked_event[key] = self._mask_sensitive_value(key, value)
                elif isinstance(value, dict):
                    masked_event[key] = self._mask_dict_values(value)

            return masked_event
        except Exception as e:
            # If masking fails, log the error and return original event
            logger.error("Log masking failed", error=str(e))
            return event_dict

    def _mask_sensitive_value(self, key: str, value: str) -> str:
        """Mask a sensitive value"""
        if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
            if len(value) <= 4:
                return "*" * len(value)
            return value[:2] + "*" * (len(value) - 4) + value[-2:]
        return value

    def _mask_dict_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask values in a dictionary"""
        masked_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                masked_data[key] = self._mask_sensitive_value(key, value)
            elif isinstance(value, dict):
                masked_data[key] = self._mask_dict_values(value)
            else:
                masked_data[key] = value
        return masked_data


class SecurityLogProcessor:
    """Processor for security-related logging"""

    def __call__(self, logger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Process security-related log events"""
        try:
            # Add security-specific fields
            event_dict["security_event"] = True
            event_dict["risk_level"] = self._determine_risk_level(event_dict)

            # Add timestamp for security events
            event_dict["security_timestamp"] = datetime.now(timezone.utc).isoformat()

            return event_dict
        except Exception as e:
            logger.error("Security log processing failed", error=str(e))
            return event_dict

    def _determine_risk_level(self, event_dict: Dict[str, Any]) -> str:
        """Determine risk level for security events"""
        high_risk_events = ["login_failed", "unauthorized_access", "permission_denied", "security_violation"]
        medium_risk_events = ["login_success", "password_changed", "permission_changed"]

        event_type = event_dict.get("event_type", "")
        if event_type in high_risk_events:
            return "HIGH"
        elif event_type in medium_risk_events:
            return "MEDIUM"
        else:
            return "LOW"


class BusinessLogProcessor:
    """Processor for business-related logging"""

    def __call__(self, logger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Process business-related log events"""
        try:
            # Add business-specific fields
            event_dict["business_event"] = True
            event_dict["business_category"] = self._categorize_business_event(event_dict)

            # Add user context if available
            if "user_id" not in event_dict and "user" in event_dict:
                if isinstance(event_dict["user"], dict):
                    event_dict["user_id"] = event_dict["user"].get("id")

            return event_dict
        except Exception as e:
            logger.error("Business log processing failed", error=str(e))
            return event_dict

    def _categorize_business_event(self, event_dict: Dict[str, Any]) -> str:
        """Categorize business events"""
        event_type = event_dict.get("event_type", "")

        if "document" in event_type:
            return "DOCUMENT_MANAGEMENT"
        elif "user" in event_type:
            return "USER_MANAGEMENT"
        elif "company" in event_type:
            return "COMPANY_MANAGEMENT"
        elif "processing" in event_type:
            return "DOCUMENT_PROCESSING"
        elif "notification" in event_type:
            return "NOTIFICATION"
        else:
            return "GENERAL"


def configure_logging(
    service_name: str = None,
    log_level: str = None,
    log_file: str = None,
    enable_json: bool = None
) -> None:
    """Configure structured logging for the application"""
    try:
        # Get configuration from environment
        service_name = service_name or os.getenv("SERVICE_NAME", "legal-automation")
        log_level = log_level or os.getenv("LOG_LEVEL", "info").lower()
        log_file = log_file or os.getenv("LOG_FILE", None)
        enable_json = enable_json if enable_json is not None else os.getenv("LOG_JSON", "true").lower() == "true"

        # Configure standard logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(message)s",
            handlers=[]
        )

        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))

        if enable_json:
            console_formatter = CustomJSONFormatter(
                "%(asctime)s %(name)s %(levelname)s %(message)s"
            )
        else:
            console_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        console_handler.setFormatter(console_formatter)
        logging.getLogger().addHandler(console_handler)

        # Add file handler if log file is specified
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=100 * 1024 * 1024,  # 100MB
                backupCount=5
            )
            file_handler.setLevel(getattr(logging, log_level.upper()))

            if enable_json:
                file_formatter = CustomJSONFormatter(
                    "%(asctime)s %(name)s %(levelname)s %(message)s"
                )
            else:
                file_formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )

            file_handler.setFormatter(file_formatter)
            logging.getLogger().addHandler(file_handler)

        # Configure structlog
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
        ]

        # Add masking processor for sensitive data
        processors.append(LogMaskingProcessor())

        # Add security processor for security events
        processors.append(structlog.processors.filter_by_level(lambda level, event: level >= logging.WARNING))

        # Add business processor for business events
        processors.append(BusinessLogProcessor())

        # Add JSON renderer for production
        if enable_json:
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer(colors=True))

        # Configure structlog
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        logger.info("Logging configured successfully",
                   service=service_name,
                   level=log_level,
                   json_format=enable_json,
                   file=log_file)

    except Exception as e:
        print(f"Failed to configure logging: {e}")
        # Configure basic logging as fallback
        logging.basicConfig(level=logging.INFO)


def get_logger(name: str = None, **kwargs) -> structlog.BoundLogger:
    """Get a structured logger with additional context"""
    if name:
        return structlog.get_logger(name, **kwargs)
    else:
        return structlog.get_logger(**kwargs)


def log_security_event(
    event_type: str,
    user_id: int = None,
    ip_address: str = None,
    user_agent: str = None,
    resource: str = None,
    success: bool = True,
    details: Dict[str, Any] = None
) -> None:
    """Log a security event"""
    try:
        security_logger = get_logger("security")

        event_data = {
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "resource": resource,
            "success": success,
            "details": details or {}
        }

        if success:
            security_logger.info("Security event", **event_data)
        else:
            security_logger.warning("Security event (failed)", **event_data)

    except Exception as e:
        logger.error("Failed to log security event", error=str(e))


def log_business_event(
    event_type: str,
    user_id: int = None,
    company_id: int = None,
    resource_id: str = None,
    metadata: Dict[str, Any] = None
) -> None:
    """Log a business event"""
    try:
        business_logger = get_logger("business")

        event_data = {
            "event_type": event_type,
            "user_id": user_id,
            "company_id": company_id,
            "resource_id": resource_id,
            "metadata": metadata or {}
        }

        business_logger.info("Business event", **event_data)

    except Exception as e:
        logger.error("Failed to log business event", error=str(e))


def log_performance_event(
    operation: str,
    duration: float,
    status: str = "success",
    metadata: Dict[str, Any] = None
) -> None:
    """Log a performance event"""
    try:
        perf_logger = get_logger("performance")

        event_data = {
            "operation": operation,
            "duration_ms": duration * 1000,
            "status": status,
            "metadata": metadata or {}
        }

        if duration > 5.0:  # Log slow operations as warnings
            perf_logger.warning("Slow operation detected", **event_data)
        else:
            perf_logger.info("Performance event", **event_data)

    except Exception as e:
        logger.error("Failed to log performance event", error=str(e))


def log_api_request(
    method: str,
    endpoint: str,
    user_id: int = None,
    status_code: int = 200,
    duration: float = None,
    request_size: int = None,
    response_size: int = None
) -> None:
    """Log an API request"""
    try:
        api_logger = get_logger("api")

        event_data = {
            "method": method,
            "endpoint": endpoint,
            "user_id": user_id,
            "status_code": status_code,
            "duration_ms": int(duration * 1000) if duration else None,
            "request_size_bytes": request_size,
            "response_size_bytes": response_size
        }

        if status_code >= 400:
            api_logger.warning("API request (error)", **event_data)
        else:
            api_logger.info("API request", **event_data)

    except Exception as e:
        logger.error("Failed to log API request", error=str(e))


# Configure logging on module import
configure_logging()