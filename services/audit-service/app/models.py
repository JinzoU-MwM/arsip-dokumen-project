"""
Pydantic models for the Audit Service
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Types of audit events"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    COMPANY_CREATED = "company_created"
    COMPANY_UPDATED = "company_updated"
    COMPANY_DELETED = "company_deleted"
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_DOWNLOADED = "document_downloaded"
    DOCUMENT_DELETED = "document_deleted"
    DOCUMENT_VALIDATED = "document_validated"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    API_ACCESS = "api_access"
    CONFIGURATION_CHANGED = "configuration_changed"
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_RESTORE = "system_restore"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    SECURITY_BREACH = "security_breach"
    FAILED_LOGIN = "failed_login"
    PASSWORD_RESET = "password_reset"
    ROLE_CHANGED = "role_changed"


class SecurityLevel(str, Enum):
    """Security severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventCategory(str, Enum):
    """Event categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM_OPERATION = "system_operation"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    BUSINESS = "business"


class ExportFormat(str, Enum):
    """Export formats"""
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    PDF = "pdf"


class ReportType(str, Enum):
    """Compliance report types"""
    STANDARD = "standard"
    SECURITY = "security"
    ACCESS = "access"
    DATA_PROTECTION = "data_protection"
    USER_ACTIVITY = "user_activity"
    SYSTEM_AUDIT = "system_audit"
    FULL = "full"


# Event Models
class BaseEvent(BaseModel):
    """Base event model"""
    event_id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    user_id: Optional[int] = Field(None, description="User ID who triggered the event")
    company_id: Optional[int] = Field(None, description="Company ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    source_service: str = Field(..., description="Service that generated the event")
    environment: str = Field(..., description="Environment (dev/staging/prod)")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")


class AuditEvent(BaseEvent):
    """General audit event"""
    event_type: EventType = Field(..., description="Type of audit event")
    event_category: EventCategory = Field(..., description="Event category")
    resource_type: Optional[str] = Field(None, description="Type of resource affected")
    resource_id: Optional[str] = Field(None, description="ID of resource affected")
    action: str = Field(..., description="Action performed")
    description: str = Field(..., description="Event description")
    outcome: str = Field(..., description="Event outcome (success/failure)")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional event details")
    old_values: Optional[Dict[str, Any]] = Field(None, description="Previous values for updates")
    new_values: Optional[Dict[str, Any]] = Field(None, description="New values for updates")


class SecurityEvent(BaseEvent):
    """Security-related event"""
    event_type: str = Field(..., description="Security event type")
    security_level: SecurityLevel = Field(..., description="Security severity level")
    threat_type: Optional[str] = Field(None, description="Type of security threat")
    source_ip: Optional[str] = Field(None, description="Source IP address")
    target_resource: Optional[str] = Field(None, description="Target resource")
    attack_vector: Optional[str] = Field(None, description="Attack vector used")
    blocked: bool = Field(default=False, description="Whether the threat was blocked")
    mitigation_actions: List[str] = Field(default_factory=list, description="Actions taken to mitigate")
    forensics_data: Dict[str, Any] = Field(default_factory=dict, description="Forensics information")


class BusinessEvent(BaseEvent):
    """Business-related event"""
    event_type: str = Field(..., description="Business event type")
    business_process: str = Field(..., description="Business process name")
    process_step: Optional[str] = Field(None, description="Step in the process")
    business_impact: str = Field(..., description="Business impact level")
    customer_id: Optional[int] = Field(None, description="Customer ID")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    monetary_value: Optional[float] = Field(None, description="Monetary value if applicable")
    business_rules: List[str] = Field(default_factory=list, description="Business rules applied")
    process_metrics: Dict[str, Any] = Field(default_factory=dict, description="Process metrics")


class PerformanceEvent(BaseEvent):
    """Performance-related event"""
    event_type: str = Field(..., description="Performance event type")
    metric_name: str = Field(..., description="Performance metric name")
    metric_value: float = Field(..., description="Metric value")
    metric_unit: str = Field(..., description="Unit of measurement")
    threshold_value: Optional[float] = Field(None, description="Threshold for alerting")
    service_name: str = Field(..., description="Service being measured")
    operation_name: Optional[str] = Field(None, description="Operation name")
    duration_ms: Optional[float] = Field(None, description="Duration in milliseconds")
    error_rate: Optional[float] = Field(None, description="Error rate percentage")
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")
    cpu_usage_percent: Optional[float] = Field(None, description="CPU usage percentage")


# Request/Response Models
class AuditQuery(BaseModel):
    """Audit trail query parameters"""
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    company_id: Optional[int] = Field(None, description="Filter by company ID")
    event_type: Optional[EventType] = Field(None, description="Filter by event type")
    event_category: Optional[EventCategory] = Field(None, description="Filter by event category")
    resource_type: Optional[str] = Field(None, description="Filter by resource type")
    resource_id: Optional[str] = Field(None, description="Filter by resource ID")
    start_time: Optional[datetime] = Field(None, description="Filter events after this time")
    end_time: Optional[datetime] = Field(None, description="Filter events before this time")
    ip_address: Optional[str] = Field(None, description="Filter by IP address")
    session_id: Optional[str] = Field(None, description="Filter by session ID")
    outcome: Optional[str] = Field(None, description="Filter by outcome")
    search_text: Optional[str] = Field(None, description="Search in event descriptions")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")
    sort_by: str = Field("timestamp", description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")


class LogSearchRequest(BaseModel):
    """Log search request"""
    query: str = Field(..., description="Search query")
    event_type: Optional[str] = Field(None, description="Filter by event type")
    start_time: Optional[datetime] = Field(None, description="Search from this time")
    end_time: Optional[datetime] = Field(None, description="Search until this time")
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    company_id: Optional[int] = Field(None, description="Filter by company ID")
    limit: int = Field(100, ge=1, le=1000, description="Maximum results")
    include_details: bool = Field(False, description="Include full event details")


class LogSearchResponse(BaseModel):
    """Log search response"""
    success: bool = Field(..., description="Search success status")
    query: str = Field(..., description="Search query used")
    total_count: int = Field(..., description="Total number of matching events")
    events: List[Dict[str, Any]] = Field(..., description="Matching events")
    search_time_ms: float = Field(..., description="Search duration in milliseconds")
    has_more: bool = Field(default=False, description="Whether more results are available")


class AuditResponse(BaseModel):
    """Audit trail query response"""
    success: bool = Field(..., description="Query success status")
    total_count: int = Field(..., description="Total number of matching events")
    events: List[Dict[str, Any]] = Field(..., description="Matching events")
    query_time_ms: float = Field(..., description="Query duration in milliseconds")
    has_more: bool = Field(default=False, description="Whether more results are available")


class ComplianceReport(BaseModel):
    """Compliance report model"""
    report_id: str = Field(..., description="Unique report identifier")
    report_type: ReportType = Field(..., description="Type of compliance report")
    generated_at: datetime = Field(..., description="Report generation timestamp")
    generated_by: int = Field(..., description="User ID who generated the report")
    start_date: datetime = Field(..., description="Report period start")
    end_date: datetime = Field(..., description="Report period end")
    company_id: Optional[int] = Field(None, description="Company ID for company-specific reports")
    summary: Dict[str, Any] = Field(..., description="Report summary")
    findings: List[Dict[str, Any]] = Field(default_factory=list, description="Compliance findings")
    recommendations: List[str] = Field(default_factory=list, description="Compliance recommendations")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="Statistical data")
    file_path: Optional[str] = Field(None, description="Path to generated report file")
    status: str = Field(..., description="Report status")


class ExportRequest(BaseModel):
    """Log export request"""
    query: AuditQuery = Field(..., description="Query to export logs for")
    format: ExportFormat = Field(ExportFormat.JSON, description="Export format")
    include_sensitive_data: bool = Field(False, description="Include sensitive data")
    compress_output: bool = Field(True, description="Compress the output")
    export_name: Optional[str] = Field(None, description="Custom export name")


class ExportResponse(BaseModel):
    """Log export response"""
    export_id: str = Field(..., description="Unique export identifier")
    query: AuditQuery = Field(..., description="Query that was exported")
    format: ExportFormat = Field(..., description="Export format")
    status: str = Field(..., description="Export status")
    created_at: datetime = Field(..., description="Export creation timestamp")
    expires_at: datetime = Field(..., description="Export expiration timestamp")
    download_url: Optional[str] = Field(None, description="Download URL")
    file_size_bytes: Optional[int] = Field(None, description="Export file size")
    record_count: Optional[int] = Field(None, description="Number of records exported")


class AuditStats(BaseModel):
    """Audit service statistics"""
    service: str = Field(..., description="Service name")
    uptime: str = Field(..., description="Service uptime status")
    timestamp: datetime = Field(..., description="Statistics timestamp")
    components: Dict[str, bool] = Field(..., description="Component health status")
    total_events_logged: int = Field(default=0, description="Total events logged")
    events_today: int = Field(default=0, description="Events logged today")
    events_this_hour: int = Field(default=0, description="Events logged this hour")
    storage_used_mb: float = Field(default=0, description="Storage used in MB")
    average_query_time_ms: float = Field(default=0, description="Average query time")
    active_sessions: int = Field(default=0, description="Number of active sessions")
    recent_security_events: int = Field(default=0, description="Security events in last 24h")
    top_event_types: List[Dict[str, Any]] = Field(default_factory=list, description="Most common event types")
    audit_logger_stats: Optional[Dict[str, Any]] = Field(None, description="Audit logger statistics")
    compliance_reporter_stats: Optional[Dict[str, Any]] = Field(None, description="Compliance reporter statistics")
    log_aggregator_stats: Optional[Dict[str, Any]] = Field(None, description="Log aggregator statistics")


class EventAnalytics(BaseModel):
    """Event analytics data"""
    event_type: str = Field(..., description="Event type")
    count: int = Field(..., description="Number of events")
    percentage: float = Field(..., description="Percentage of total events")
    trend: str = Field(..., description="Trend direction (up/down/stable)")
    trend_percentage: float = Field(..., description="Trend change percentage")


class SecuritySummary(BaseModel):
    """Security events summary"""
    total_events: int = Field(..., description="Total security events")
    critical_events: int = Field(..., description="Critical security events")
    high_events: int = Field(..., description="High severity events")
    medium_events: int = Field(..., description="Medium severity events")
    low_events: int = Field(..., description="Low severity events")
    blocked_threats: int = Field(..., description="Blocked threats")
    top_threat_types: List[Dict[str, Any]] = Field(default_factory=list, description="Most common threat types")
    recent_incidents: List[Dict[str, Any]] = Field(default_factory=list, description="Recent security incidents")


class PerformanceSummary(BaseModel):
    """Performance metrics summary"""
    average_response_time_ms: float = Field(..., description="Average response time")
    requests_per_minute: float = Field(..., description="Requests per minute")
    error_rate_percent: float = Field(..., description="Error rate percentage")
    cpu_usage_percent: float = Field(..., description="Average CPU usage")
    memory_usage_mb: float = Field(..., description="Average memory usage")
    slowest_endpoints: List[Dict[str, Any]] = Field(default_factory=list, description="Slowest endpoints")
    performance_alerts: List[Dict[str, Any]] = Field(default_factory=list, description="Performance alerts")


class ComplianceMetrics(BaseModel):
    """Compliance metrics"""
    compliance_score: float = Field(..., description="Overall compliance score (0-100)")
    audit_trail_coverage: float = Field(..., description="Audit trail coverage percentage")
    data_access_logs: float = Field(..., description="Data access logging coverage")
    authentication_events: int = Field(..., description="Authentication events logged")
    authorization_events: int = Field(..., description="Authorization events logged")
    data_modification_events: int = Field(..., description="Data modification events logged")
    compliance_gaps: List[Dict[str, Any]] = Field(default_factory=list, description="Identified compliance gaps")
    recommendations: List[str] = Field(default_factory=list, description="Compliance recommendations")