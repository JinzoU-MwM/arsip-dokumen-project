"""
Audit Logger
Core audit logging functionality with database storage
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    AuditEvent,
    SecurityEvent,
    BusinessEvent,
    PerformanceEvent,
    AuditQuery,
    AuditResponse,
    EventType,
    EventCategory
)


class AuditLogger:
    """Service for managing audit logs"""

    def __init__(self):
        self.logger = structlog.get_logger().bind(component="AuditLogger")
        self.db_session = None
        self.stats = {
            "total_events": 0,
            "events_today": 0,
            "events_this_hour": 0,
            "event_types": {}
        }

    async def initialize(self):
        """Initialize the audit logger"""
        self.logger.info("Initializing Audit Logger")

        try:
            # Initialize database connection (would be imported from shared module)
            from shared.database import get_db

            # Test database connection
            async for session in get_db():
                self.db_session = session
                break

            # Initialize statistics
            await self._update_stats()

            self.logger.info("Audit Logger initialized successfully")

        except Exception as e:
            self.logger.error("Failed to initialize Audit Logger", error=str(e))
            raise

    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up Audit Logger")
        if self.db_session:
            await self.db_session.close()

    async def log_audit_event(self, event: AuditEvent):
        """Log an audit event"""
        try:
            # Generate event ID if not provided
            if not event.event_id:
                event.event_id = str(uuid.uuid4())

            # Log to database
            await self._store_audit_event(event)

            # Update statistics
            self.stats["total_events"] += 1
            self.stats["event_types"][event.event_type.value] = self.stats["event_types"].get(event.event_type.value, 0) + 1

            self.logger.info("Audit event logged",
                           event_id=event.event_id,
                           event_type=event.event_type.value,
                           user_id=event.user_id,
                           company_id=event.company_id)

        except Exception as e:
            self.logger.error("Failed to log audit event", error=str(e))
            raise

    async def log_security_event(self, event: SecurityEvent):
        """Log a security event"""
        try:
            # Generate event ID if not provided
            if not event.event_id:
                event.event_id = str(uuid.uuid4())

            # Store security event with higher priority
            await self._store_security_event(event)

            # Trigger immediate security alerts for critical events
            if event.security_level in ["high", "critical"]:
                await self._trigger_security_alert(event)

            self.logger.warning("Security event logged",
                              event_id=event.event_id,
                              security_level=event.security_level.value,
                              threat_type=event.threat_type,
                              user_id=event.user_id)

        except Exception as e:
            self.logger.error("Failed to log security event", error=str(e))
            raise

    async def log_business_event(self, event: BusinessEvent):
        """Log a business event"""
        try:
            # Generate event ID if not provided
            if not event.event_id:
                event.event_id = str(uuid.uuid4())

            await self._store_business_event(event)

            self.logger.info("Business event logged",
                           event_id=event.event_id,
                           business_process=event.business_process,
                           user_id=event.user_id)

        except Exception as e:
            self.logger.error("Failed to log business event", error=str(e))
            raise

    async def log_performance_event(self, event: PerformanceEvent):
        """Log a performance event"""
        try:
            # Generate event ID if not provided
            if not event.event_id:
                event.event_id = str(uuid.uuid4())

            await self._store_performance_event(event)

            # Check for performance alerts
            await self._check_performance_alerts(event)

            self.logger.info("Performance event logged",
                           event_id=event.event_id,
                           metric_name=event.metric_name,
                           metric_value=event.metric_value)

        except Exception as e:
            self.logger.error("Failed to log performance event", error=str(e))
            raise

    async def query_audit_trail(self, query: AuditQuery) -> AuditResponse:
        """Query audit trail with filters"""
        try:
            start_time = asyncio.get_event_loop().time()

            # Build query filters
            filters = []

            if query.user_id:
                filters.append(self.db_session.query(AuditEvent).filter(AuditEvent.user_id == query.user_id))

            if query.company_id:
                filters.append(AuditEvent.company_id == query.company_id)

            if query.event_type:
                filters.append(AuditEvent.event_type == query.event_type)

            if query.event_category:
                filters.append(AuditEvent.event_category == query.event_category)

            if query.start_time:
                filters.append(AuditEvent.timestamp >= query.start_time)

            if query.end_time:
                filters.append(AuditEvent.timestamp <= query.end_time)

            if query.ip_address:
                filters.append(AuditEvent.ip_address == query.ip_address)

            if query.session_id:
                filters.append(AuditEvent.session_id == query.session_id)

            if query.outcome:
                filters.append(AuditEvent.outcome == query.outcome)

            if query.search_text:
                filters.append(AuditEvent.description.ilike(f"%{query.search_text}%"))

            # Execute query
            base_query = self.db_session.query(AuditEvent)
            if filters:
                base_query = base_query.filter(and_(*filters))

            # Get total count
            total_count = await base_query.count()

            # Apply sorting and pagination
            if query.sort_by == "timestamp":
                order_field = AuditEvent.timestamp
            else:
                order_field = getattr(AuditEvent, query.sort_by, AuditEvent.timestamp)

            if query.sort_order == "desc":
                order_field = desc(order_field)

            events = await base_query.order_by(order_field).offset(query.offset).limit(query.limit).all()

            # Convert to dict format
            event_dicts = [event.to_dict() for event in events]

            query_time = (asyncio.get_event_loop().time() - start_time) * 1000
            has_more = (query.offset + len(events)) < total_count

            return AuditResponse(
                success=True,
                total_count=total_count,
                events=event_dicts,
                query_time_ms=query_time,
                has_more=has_more
            )

        except Exception as e:
            self.logger.error("Audit trail query failed", error=str(e))
            raise

    async def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get specific event by ID"""
        try:
            # Try to get from audit events first
            event = await self.db_session.query(AuditEvent).filter(AuditEvent.event_id == event_id).first()
            if event:
                return event.to_dict()

            # Try security events
            event = await self.db_session.query(SecurityEvent).filter(SecurityEvent.event_id == event_id).first()
            if event:
                return event.to_dict()

            # Try business events
            event = await self.db_session.query(BusinessEvent).filter(BusinessEvent.event_id == event_id).first()
            if event:
                return event.to_dict()

            # Try performance events
            event = await self.db_session.query(PerformanceEvent).filter(PerformanceEvent.event_id == event_id).first()
            if event:
                return event.to_dict()

            return None

        except Exception as e:
            self.logger.error("Failed to get event", event_id=event_id, error=str(e))
            return None

    async def count_logs_before(self, cutoff_date: datetime) -> int:
        """Count logs before cutoff date"""
        try:
            count = await self.db_session.query(AuditEvent).filter(
                AuditEvent.timestamp < cutoff_date
            ).count()

            return count

        except Exception as e:
            self.logger.error("Failed to count logs before date", error=str(e))
            return 0

    async def delete_logs_before(self, cutoff_date: datetime) -> int:
        """Delete logs before cutoff date"""
        try:
            # Delete in batches to avoid blocking
            batch_size = 1000
            total_deleted = 0

            while True:
                # Get batch of events to delete
                events = await self.db_session.query(AuditEvent).filter(
                    AuditEvent.timestamp < cutoff_date
                ).limit(batch_size).all()

                if not events:
                    break

                # Delete events
                for event in events:
                    await self.db_session.delete(event)

                await self.db_session.commit()
                total_deleted += len(events)

                self.logger.info("Deleted log batch", batch_size=len(events), total_deleted=total_deleted)

            return total_deleted

        except Exception as e:
            self.logger.error("Failed to delete logs before date", error=str(e))
            await self.db_session.rollback()
            raise

    async def get_recent_activity_summary(self) -> Dict[str, Any]:
        """Get recent activity summary"""
        try:
            now = datetime.utcnow()
            last_24h = now - timedelta(hours=24)
            last_hour = now - timedelta(hours=1)

            # Get activity counts
            total_24h = await self.db_session.query(AuditEvent).filter(
                AuditEvent.timestamp >= last_24h
            ).count()

            total_hour = await self.db_session.query(AuditEvent).filter(
                AuditEvent.timestamp >= last_hour
            ).count()

            # Get top event types in last 24h
            top_events = await self.db_session.query(
                AuditEvent.event_type,
                func.count(AuditEvent.event_id).label('count')
            ).filter(
                AuditEvent.timestamp >= last_24h
            ).group_by(AuditEvent.event_type).order_by(desc('count')).limit(5).all()

            # Get recent user activity
            active_users = await self.db_session.query(
                AuditEvent.user_id,
                func.count(AuditEvent.event_id).label('count')
            ).filter(
                AuditEvent.timestamp >= last_24h,
                AuditEvent.user_id.isnot(None)
            ).group_by(AuditEvent.user_id).order_by(desc('count')).limit(10).all()

            return {
                "events_last_24h": total_24h,
                "events_last_hour": total_hour,
                "top_event_types": [{"type": et[0], "count": et[1]} for et in top_events],
                "active_users": [{"user_id": et[0], "events": et[1]} for et in active_users],
                "timestamp": now
            }

        except Exception as e:
            self.logger.error("Failed to get recent activity summary", error=str(e))
            return {}

    async def get_security_events_summary(self) -> Dict[str, Any]:
        """Get security events summary"""
        try:
            last_24h = datetime.utcnow() - timedelta(hours=24)

            # Get security event counts by severity
            security_counts = await self.db_session.query(
                SecurityEvent.security_level,
                func.count(SecurityEvent.event_id).label('count')
            ).filter(
                SecurityEvent.timestamp >= last_24h
            ).group_by(SecurityEvent.security_level).all()

            # Get recent security incidents
            recent_incidents = await self.db_session.query(SecurityEvent).filter(
                SecurityEvent.timestamp >= last_24h,
                SecurityEvent.security_level.in_(["high", "critical"])
            ).order_by(desc(SecurityEvent.timestamp)).limit(5).all()

            summary = {
                "total_events": sum(count[1] for count in security_counts),
                "by_severity": {count[0].value: count[1] for count in security_counts},
                "recent_incidents": [incident.to_dict() for incident in recent_incidents]
            }

            return summary

        except Exception as e:
            self.logger.error("Failed to get security events summary", error=str(e))
            return {}

    async def _store_audit_event(self, event: AuditEvent):
        """Store audit event in database"""
        try:
            # Would use actual database models here
            # This is a placeholder implementation
            self.logger.debug("Storing audit event", event_id=event.event_id)

        except Exception as e:
            self.logger.error("Failed to store audit event", error=str(e))
            raise

    async def _store_security_event(self, event: SecurityEvent):
        """Store security event in database"""
        try:
            # Would use actual database models here
            self.logger.debug("Storing security event", event_id=event.event_id)

        except Exception as e:
            self.logger.error("Failed to store security event", error=str(e))
            raise

    async def _store_business_event(self, event: BusinessEvent):
        """Store business event in database"""
        try:
            # Would use actual database models here
            self.logger.debug("Storing business event", event_id=event.event_id)

        except Exception as e:
            self.logger.error("Failed to store business event", error=str(e))
            raise

    async def _store_performance_event(self, event: PerformanceEvent):
        """Store performance event in database"""
        try:
            # Would use actual database models here
            self.logger.debug("Storing performance event", event_id=event.event_id)

        except Exception as e:
            self.logger.error("Failed to store performance event", error=str(e))
            raise

    async def _trigger_security_alert(self, event: SecurityEvent):
        """Trigger security alert for critical events"""
        try:
            # Would integrate with notification service here
            self.logger.warning("Security alert triggered",
                              event_id=event.event_id,
                              security_level=event.security_level.value,
                              threat_type=event.threat_type)

        except Exception as e:
            self.logger.error("Failed to trigger security alert", error=str(e))

    async def _check_performance_alerts(self, event: PerformanceEvent):
        """Check for performance alerts"""
        try:
            # Would check thresholds and trigger alerts
            if event.threshold_value and event.metric_value > event.threshold_value:
                self.logger.warning("Performance threshold exceeded",
                                  event_id=event.event_id,
                                  metric=event.metric_name,
                                  value=event.metric_value,
                                  threshold=event.threshold_value)

        except Exception as e:
            self.logger.error("Failed to check performance alerts", error=str(e))

    async def _update_stats(self):
        """Update internal statistics"""
        try:
            # Get today's events
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_count = await self.db_session.query(AuditEvent).filter(
                AuditEvent.timestamp >= today
            ).count()

            # Get this hour's events
            this_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            hour_count = await self.db_session.query(AuditEvent).filter(
                AuditEvent.timestamp >= this_hour
            ).count()

            self.stats["events_today"] = today_count
            self.stats["events_this_hour"] = hour_count

        except Exception as e:
            self.logger.error("Failed to update stats", error=str(e))

    async def get_stats(self) -> Dict[str, Any]:
        """Get audit logger statistics"""
        return {
            "service": "audit_logger",
            "status": "active",
            **self.stats
        }