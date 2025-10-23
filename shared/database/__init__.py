"""
Shared database module for the AI Legal Document Automation System
"""

from .models import (
    Base,
    User,
    Company,
    Document,
    ProcessingJob,
    Notification,
    AuditLog,
    SystemConfiguration,
    APIKey,
    UserStatus,
    UserRole,
    DocumentStatus,
    ProcessingStatus,
    NotificationStatus,
    ComplianceStatus,
)

__all__ = [
    "Base",
    "User",
    "Company",
    "Document",
    "ProcessingJob",
    "Notification",
    "AuditLog",
    "SystemConfiguration",
    "APIKey",
    "UserStatus",
    "UserRole",
    "DocumentStatus",
    "ProcessingStatus",
    "NotificationStatus",
    "ComplianceStatus",
]