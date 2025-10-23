"""
Audit Service
Centralized logging, audit trails, and compliance reporting
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import structlog
import uvicorn
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

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
    ComplianceReport,
    LogSearchRequest,
    LogSearchResponse,
    AuditStats,
    ExportRequest,
    ExportResponse
)

# Configure structured logging
logger = structlog.get_logger()

# Global variables
audit_logger: AuditLogger = None
compliance_reporter: ComplianceReporter = None
log_aggregator: LogAggregator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global audit_logger, compliance_reporter, log_aggregator

    logger.info("Starting Audit Service")

    # Initialize components
    try:
        audit_logger = AuditLogger()
        compliance_reporter = ComplianceReporter()
        log_aggregator = LogAggregator()

        await audit_logger.initialize()
        await compliance_reporter.initialize()
        await log_aggregator.initialize()

        logger.info("Audit Service initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize Audit Service", error=str(e))
        raise

    yield

    logger.info("Shutting down Audit Service")
    # Cleanup resources
    if audit_logger:
        await audit_logger.cleanup()
    if compliance_reporter:
        await compliance_reporter.cleanup()
    if log_aggregator:
        await log_aggregator.cleanup()


# Create FastAPI application
app = FastAPI(
    title="Audit Service",
    description="Centralized logging, audit trails, and compliance reporting",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "audit-service",
        "components": {
            "audit_logger": audit_logger is not None,
            "compliance_reporter": compliance_reporter is not None,
            "log_aggregator": log_aggregator is not None
        }
    }


@app.post("/events/audit")
async def log_audit_event(event: AuditEvent):
    """Log an audit event"""
    try:
        await audit_logger.log_audit_event(event)
        return {"success": True, "message": "Audit event logged successfully"}

    except Exception as e:
        logger.error("Failed to log audit event", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to log event: {str(e)}")


@app.post("/events/security")
async def log_security_event(event: SecurityEvent):
    """Log a security event"""
    try:
        await audit_logger.log_security_event(event)
        return {"success": True, "message": "Security event logged successfully"}

    except Exception as e:
        logger.error("Failed to log security event", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to log event: {str(e)}")


@app.post("/events/business")
async def log_business_event(event: BusinessEvent):
    """Log a business event"""
    try:
        await audit_logger.log_business_event(event)
        return {"success": True, "message": "Business event logged successfully"}

    except Exception as e:
        logger.error("Failed to log business event", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to log event: {str(e)}")


@app.post("/events/performance")
async def log_performance_event(event: PerformanceEvent):
    """Log a performance event"""
    try:
        await audit_logger.log_performance_event(event)
        return {"success": True, "message": "Performance event logged successfully"}

    except Exception as e:
        logger.error("Failed to log performance event", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to log event: {str(e)}")


@app.post("/search", response_model=LogSearchResponse)
async def search_logs(request: LogSearchRequest):
    """Search audit logs"""
    try:
        logger.info("Log search requested", query=request.query, event_type=request.event_type)

        results = await log_aggregator.search_logs(request)

        logger.info("Log search completed", result_count=len(results.events))

        return results

    except Exception as e:
        logger.error("Log search failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/query", response_model=AuditResponse)
async def query_audit_trail(request: AuditQuery):
    """Query audit trail with filters"""
    try:
        logger.info("Audit trail query requested", user_id=request.user_id, company_id=request.company_id)

        results = await audit_logger.query_audit_trail(request)

        logger.info("Audit trail query completed", result_count=len(results.events))

        return results

    except Exception as e:
        logger.error("Audit trail query failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/events/{event_id}")
async def get_event(event_id: str):
    """Get specific event by ID"""
    try:
        event = await audit_logger.get_event(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        return event

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get event", event_id=event_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get event: {str(e)}")


@app.get("/users/{user_id}/activity")
async def get_user_activity(
    user_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get user activity log"""
    try:
        query = AuditQuery(
            user_id=user_id,
            start_time=start_date,
            end_time=end_date,
            limit=limit
        )

        results = await audit_logger.query_audit_trail(query)
        return results

    except Exception as e:
        logger.error("Failed to get user activity", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get user activity: {str(e)}")


@app.get("/companies/{company_id}/activity")
async def get_company_activity(
    company_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get company activity log"""
    try:
        query = AuditQuery(
            company_id=company_id,
            start_time=start_date,
            end_time=end_date,
            limit=limit
        )

        results = await audit_logger.query_audit_trail(query)
        return results

    except Exception as e:
        logger.error("Failed to get company activity", company_id=company_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get company activity: {str(e)}")


@app.post("/reports/compliance", response_model=ComplianceReport)
async def generate_compliance_report(
    start_date: datetime,
    end_date: datetime,
    company_id: Optional[int] = None,
    report_type: str = "standard"
):
    """Generate compliance report"""
    try:
        logger.info("Compliance report generation requested",
                   start_date=start_date,
                   end_date=end_date,
                   company_id=company_id,
                   report_type=report_type)

        report = await compliance_reporter.generate_report(
            start_date=start_date,
            end_date=end_date,
            company_id=company_id,
            report_type=report_type
        )

        logger.info("Compliance report generated", report_id=report.report_id)

        return report

    except Exception as e:
        logger.error("Compliance report generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@app.get("/reports/compliance/{report_id}")
async def get_compliance_report(report_id: str):
    """Get compliance report by ID"""
    try:
        report = await compliance_reporter.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get compliance report", report_id=report_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")


@app.post("/export", response_model=ExportResponse)
async def export_logs(request: ExportRequest):
    """Export logs in specified format"""
    try:
        logger.info("Log export requested", format=request.format, query=request.query)

        export_result = await log_aggregator.export_logs(request)

        logger.info("Log export completed", export_id=export_result.export_id)

        return export_result

    except Exception as e:
        logger.error("Log export failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.get("/export/{export_id}/download")
async def download_export(export_id: str):
    """Download exported logs"""
    try:
        export_data = await log_aggregator.get_export_file(export_id)
        if not export_data:
            raise HTTPException(status_code=404, detail="Export not found")

        from fastapi.responses import StreamingResponse
        import io

        return StreamingResponse(
            io.BytesIO(export_data['content']),
            media_type=export_data['media_type'],
            headers={
                "Content-Disposition": f"attachment; filename={export_data['filename']}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to download export", export_id=export_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@app.get("/stats", response_model=AuditStats)
async def get_audit_stats():
    """Get audit service statistics"""
    try:
        stats = {
            "service": "audit-service",
            "uptime": "running",
            "timestamp": datetime.utcnow(),
            "components": {
                "audit_logger": audit_logger is not None,
                "compliance_reporter": compliance_reporter is not None,
                "log_aggregator": log_aggregator is not None
            }
        }

        # Add statistics from components
        if audit_logger:
            stats["audit_logger_stats"] = await audit_logger.get_stats()

        if compliance_reporter:
            stats["compliance_reporter_stats"] = await compliance_reporter.get_stats()

        if log_aggregator:
            stats["log_aggregator_stats"] = await log_aggregator.get_stats()

        return AuditStats(**stats)

    except Exception as e:
        logger.error("Failed to get audit stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.post("/cleanup")
async def cleanup_old_logs(
    days_to_keep: int = Query(90, ge=1, le=365),
    dry_run: bool = Query(True)
):
    """Clean up old audit logs"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        if dry_run:
            # Just count what would be deleted
            count = await audit_logger.count_logs_before(cutoff_date)
            return {
                "dry_run": True,
                "logs_to_delete": count,
                "cutoff_date": cutoff_date,
                "message": f"Would delete {count} logs older than {cutoff_date}"
            }
        else:
            # Actually delete the logs
            deleted_count = await audit_logger.delete_logs_before(cutoff_date)
            return {
                "dry_run": False,
                "logs_deleted": deleted_count,
                "cutoff_date": cutoff_date,
                "message": f"Deleted {deleted_count} logs older than {cutoff_date}"
            }

    except Exception as e:
        logger.error("Log cleanup failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@app.get("/dashboard/summary")
async def get_dashboard_summary():
    """Get summary data for dashboard"""
    try:
        # Get recent activity summary
        recent_activity = await audit_logger.get_recent_activity_summary()

        # Get security events summary
        security_summary = await audit_logger.get_security_events_summary()

        # Get performance metrics
        performance_summary = await log_aggregator.get_performance_summary()

        return {
            "recent_activity": recent_activity,
            "security_summary": security_summary,
            "performance_summary": performance_summary,
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error("Failed to get dashboard summary", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info"
    )