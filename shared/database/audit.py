"""
Audit logging system for compliance and security tracking
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import structlog
from cryptography.fernet import Fernet

from .models import AuditLog, User
from ..security.encryption import encryption_service
from ..utils.logging import get_logger

logger = get_logger("audit")


class AuditEvent:
    """Audit event types and categories"""

    class Category:
        AUTHENTICATION = "authentication"
        AUTHORIZATION = "authorization"
        DOCUMENT = "document"
        USER = "user"
        COMPANY = "company"
        SYSTEM = "system"
        SECURITY = "security"
        COMPLIANCE = "compliance"
        API = "api"
        DATA = "data"
        NOTIFICATION = "notification"

    class Action:
        # Authentication events
        LOGIN = "login"
        LOGOUT = "logout"
        LOGIN_FAILED = "login_failed"
        PASSWORD_CHANGE = "password_change"
        PASSWORD_RESET = "password_reset"

        # Authorization events
        PERMISSION_GRANTED = "permission_granted"
        PERMISSION_DENIED = "permission_denied"
        ROLE_CHANGE = "role_change"

        # User management events
        USER_CREATED = "user_created"
        USER_UPDATED = "user_updated"
        USER_DELETED = "user_deleted"
        USER_SUSPENDED = "user_suspended"
        USER_ACTIVATED = "user_activated"

        # Company management events
        COMPANY_CREATED = "company_created"
        COMPANY_UPDATED = "company_updated"
        COMPANY_DELETED = "company_deleted"
        COMPANY_SUSPENDED = "company_suspended"

        # Document events
        DOCUMENT_UPLOADED = "document_uploaded"
        DOCUMENT_PROCESSED = "document_processed"
        DOCUMENT_DELETED = "document_deleted"
        DOCUMENT_DOWNLOADED = "document_downloaded"
        DOCUMENT_SHARED = "document_shared"

        # System events
        SYSTEM_STARTED = "system_started"
        SYSTEM_STOPPED = "system_stopped"
        CONFIGURATION_CHANGED = "configuration_changed"

        # Security events
        SECURITY_VIOLATION = "security_violation"
        UNAUTHORIZED_ACCESS = "unauthorized_access"
        DATA_BREACH = "data_breach"
        SUSPICIOUS_ACTIVITY = "suspicious_activity"

        # Compliance events
        COMPLIANCE_CHECK = "compliance_check"
        COMPLIANCE_VIOLATION = "compliance_violation"
        AUDIT_CONDUCTED = "audit_conducted"

        # API events
        API_REQUEST = "api_request"
        API_ERROR = "api_error"
        RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

        # Data events
        DATA_EXPORT = "data_export"
        DATA_IMPORT = "data_import"
        DATA_BACKUP = "data_backup"
        DATA_RESTORE = "data_restore"

        # Notification events
        NOTIFICATION_SENT = "notification_sent"
        NOTIFICATION_FAILED = "notification_failed"


class AuditLogger:
    """Audit logging service for compliance and security tracking"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logger

    def log_event(
        self,
        event_type: str,
        event_category: str,
        action: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_details: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        sensitivity_level: str = "normal",
        compliance_tags: Optional[List[str]] = None
    ) -> AuditLog:
        """Log an audit event"""
        try:
            # Create audit log entry
            audit_log = AuditLog(
                event_type=event_type,
                event_category=event_category,
                action=action,
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_details=resource_details or {},
                description=description,
                old_values=old_values or {},
                new_values=new_values or {},
                success=success,
                error_message=error_message,
                sensitivity_level=sensitivity_level,
                compliance_tags=compliance_tags or [],
                timestamp=datetime.now(timezone.utc)
            )

            # Save to database
            self.db.add(audit_log)
            self.db.commit()

            self.logger.info("Audit event logged",
                           event_type=event_type,
                           action=action,
                           user_id=user_id,
                           success=success)

            return audit_log

        except Exception as e:
            self.logger.error("Failed to log audit event",
                            event_type=event_type,
                            error=str(e))
            self.db.rollback()
            raise

    def log_authentication_event(
        self,
        action: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> AuditLog:
        """Log authentication event"""
        return self.log_event(
            event_type=f"auth_{action}",
            event_category=AuditEvent.Category.AUTHENTICATION,
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type="user_session",
            success=success,
            error_message=error_message,
            session_id=session_id,
            sensitivity_level="high",
            compliance_tags=["authentication", "security"]
        )

    def log_authorization_event(
        self,
        action: str,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        permission: Optional[str] = None,
        success: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log authorization event"""
        resource_details = {}
        if permission:
            resource_details["permission"] = permission

        return self.log_event(
            event_type=f"authz_{action}",
            event_category=AuditEvent.Category.AUTHORIZATION,
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_details=resource_details,
            success=success,
            sensitivity_level="high",
            compliance_tags=["authorization", "security"]
        )

    def log_user_management_event(
        self,
        action: str,
        user_id: int,
        target_user_id: int,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log user management event"""
        return self.log_event(
            event_type=f"user_{action}",
            event_category=AuditEvent.Category.USER,
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type="user",
            resource_id=str(target_user_id),
            old_values=old_values,
            new_values=new_values,
            sensitivity_level="high",
            compliance_tags=["user_management", "privacy"]
        )

    def log_document_event(
        self,
        action: str,
        document_id: int,
        user_id: Optional[int] = None,
        company_id: Optional[int] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log document-related event"""
        resource_details = {}
        if company_id:
            resource_details["company_id"] = company_id

        return self.log_event(
            event_type=f"document_{action}",
            event_category=AuditEvent.Category.DOCUMENT,
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type="document",
            resource_id=str(document_id),
            resource_details=resource_details,
            old_values=old_values,
            new_values=new_values,
            sensitivity_level="medium",
            compliance_tags=["document_management", "data_protection"]
        )

    def log_system_event(
        self,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ) -> AuditLog:
        """Log system-level event"""
        return self.log_event(
            event_type=f"system_{action}",
            event_category=AuditEvent.Category.SYSTEM,
            action=action,
            user_id=user_id,
            resource_details=details or {},
            sensitivity_level="low",
            compliance_tags=["system", "administration"]
        )

    def log_security_event(
        self,
        action: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True
    ) -> AuditLog:
        """Log security-related event"""
        return self.log_event(
            event_type=f"security_{action}",
            event_category=AuditEvent.Category.SECURITY,
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_details=details or {},
            success=success,
            sensitivity_level="critical",
            compliance_tags=["security", "critical_incident"]
        )

    def log_compliance_event(
        self,
        action: str,
        compliance_type: str,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        violations: Optional[List[str]] = None
    ) -> AuditLog:
        """Log compliance-related event"""
        resource_details = {
            "compliance_type": compliance_type,
            "violations": violations or []
        }
        if details:
            resource_details.update(details)

        compliance_tags = ["compliance", compliance_type]
        if violations:
            compliance_tags.append("violation")

        return self.log_event(
            event_type=f"compliance_{action}",
            event_category=AuditEvent.Category.COMPLIANCE,
            action=action,
            user_id=user_id,
            resource_details=resource_details,
            success=success,
            sensitivity_level="high",
            compliance_tags=compliance_tags
        )

    def log_data_event(
        self,
        action: str,
        data_type: str,
        record_count: int,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        success: bool = True
    ) -> AuditLog:
        """Log data-related event"""
        resource_details = {
            "data_type": data_type,
            "record_count": record_count
        }

        return self.log_event(
            event_type=f"data_{action}",
            event_category=AuditEvent.Category.DATA,
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            resource_type="data",
            resource_details=resource_details,
            success=success,
            sensitivity_level="medium",
            compliance_tags=["data_management", "privacy"]
        )

    def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        event_type: Optional[str] = None,
        event_category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Query audit logs with filters"""
        try:
            query = self.db.query(AuditLog)

            # Apply filters
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)

            if event_type:
                query = query.filter(AuditLog.event_type == event_type)

            if event_category:
                query = query.filter(AuditLog.event_category == event_category)

            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)

            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)

            # Order and paginate
            logs = query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()

            return logs

        except Exception as e:
            self.logger.error("Failed to query audit logs", error=str(e))
            return []

    def get_user_activity_summary(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get activity summary for a user"""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)

            # Query user activities
            activities = self.db.query(AuditLog).filter(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.timestamp >= start_date
                )
            ).all()

            # Analyze activities
            summary = {
                "user_id": user_id,
                "period_days": days,
                "total_activities": len(activities),
                "successful_activities": len([a for a in activities if a.success]),
                "failed_activities": len([a for a in activities if not a.success]),
                "categories": {},
                "actions": {},
                "last_activity": None
            }

            # Categorize activities
            for activity in activities:
                # Category summary
                category = activity.event_category
                if category not in summary["categories"]:
                    summary["categories"][category] = 0
                summary["categories"][category] += 1

                # Action summary
                action = activity.action
                if action not in summary["actions"]:
                    summary["actions"][action] = 0
                summary["actions"][action] += 1

                # Last activity
                if (summary["last_activity"] is None or
                    activity.timestamp > summary["last_activity"]):
                    summary["last_activity"] = activity.timestamp

            return summary

        except Exception as e:
            self.logger.error("Failed to get user activity summary", error=str(e))
            return {}

    def export_audit_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        event_categories: Optional[List[str]] = None,
        format: str = "json"
    ) -> str:
        """Export audit logs for compliance reporting"""
        try:
            query = self.db.query(AuditLog).filter(
                and_(
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date
                )
            )

            if event_categories:
                query = query.filter(AuditLog.event_category.in_(event_categories))

            logs = query.order_by(AuditLog.timestamp).all()

            if format.lower() == "json":
                # Convert to JSON format
                export_data = []
                for log in logs:
                    export_data.append({
                        "id": log.id,
                        "timestamp": log.timestamp.isoformat(),
                        "event_type": log.event_type,
                        "event_category": log.event_category,
                        "action": log.action,
                        "user_id": log.user_id,
                        "ip_address": log.ip_address,
                        "resource_type": log.resource_type,
                        "resource_id": log.resource_id,
                        "description": log.description,
                        "success": log.success,
                        "sensitivity_level": log.sensitivity_level,
                        "compliance_tags": log.compliance_tags
                    })

                return json.dumps(export_data, indent=2, default=str)

            else:
                # CSV format (simplified)
                import csv
                import io

                output = io.StringIO()
                writer = csv.writer(output)

                # Header
                writer.writerow([
                    "timestamp", "event_type", "event_category", "action",
                    "user_id", "ip_address", "resource_type", "resource_id",
                    "description", "success", "sensitivity_level"
                ])

                # Data rows
                for log in logs:
                    writer.writerow([
                        log.timestamp.isoformat(),
                        log.event_type,
                        log.event_category,
                        log.action,
                        log.user_id,
                        log.ip_address,
                        log.resource_type,
                        log.resource_id,
                        log.description,
                        log.success,
                        log.sensitivity_level
                    ])

                return output.getvalue()

        except Exception as e:
            self.logger.error("Failed to export audit logs", error=str(e))
            raise


def get_audit_logger(db_session: Session) -> AuditLogger:
    """Get audit logger instance"""
    return AuditLogger(db_session)