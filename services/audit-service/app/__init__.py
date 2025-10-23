"""
Audit Service
Centralized logging, audit trails, and compliance reporting
"""

from .main import app
from .audit_logger import AuditLogger
from .compliance_reporter import ComplianceReporter
from .log_aggregator import LogAggregator
from .models import (
    AuditEvent,
    SecurityEvent,
    BusinessEvent,
    PerformanceEvent,
    AuditQuery,
    AuditResponse,
    LogSearchRequest,
    LogSearchResponse,
    ComplianceReport,
    ExportRequest,
    ExportResponse,
    AuditStats,
    EventType,
    SecurityLevel,
    EventCategory,
    ExportFormat,
    ReportType,
    EventAnalytics,
    SecuritySummary,
    PerformanceSummary,
    ComplianceMetrics
)

__version__ = "1.0.0"
__service_name__ = "audit-service"

__all__ = [
    "app",
    "AuditLogger",
    "ComplianceReporter",
    "LogAggregator",
    "AuditEvent",
    "SecurityEvent",
    "BusinessEvent",
    "PerformanceEvent",
    "AuditQuery",
    "AuditResponse",
    "LogSearchRequest",
    "LogSearchResponse",
    "ComplianceReport",
    "ExportRequest",
    "ExportResponse",
    "AuditStats",
    "EventType",
    "SecurityLevel",
    "EventCategory",
    "ExportFormat",
    "ReportType",
    "EventAnalytics",
    "SecuritySummary",
    "PerformanceSummary",
    "ComplianceMetrics"
]