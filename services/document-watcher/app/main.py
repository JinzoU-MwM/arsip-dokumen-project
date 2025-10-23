"""
Document Watcher Service
Monitors local folders for new legal documents and triggers processing pipeline
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import structlog
import uvicorn
from contextlib import asynccontextmanager

from .file_monitor import DocumentFileMonitor
from .event_handlers import DocumentEventHandler

# Configure structured logging
logger = structlog.get_logger()

# Global variables for file monitor
file_monitor: DocumentFileMonitor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global file_monitor

    logger.info("Starting Document Watcher Service")

    # Initialize file monitor
    file_monitor = DocumentFileMonitor()
    await file_monitor.start()

    yield

    logger.info("Shutting down Document Watcher Service")
    if file_monitor:
        await file_monitor.stop()


# Create FastAPI application
app = FastAPI(
    title="Document Watcher Service",
    description="Monitors local folders for new legal documents and triggers processing",
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


# Pydantic models
class DocumentEvent(BaseModel):
    """Document event model"""
    file_path: str
    event_type: str  # created, modified, deleted
    file_size: int
    timestamp: str


class MonitoringStatus(BaseModel):
    """Monitoring status model"""
    is_active: bool
    watched_folders: list[str]
    total_documents_processed: int
    last_processed_document: str | None = None


# API endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "document-watcher"}


@app.get("/status", response_model=MonitoringStatus)
async def get_monitoring_status():
    """Get current monitoring status"""
    global file_monitor

    if not file_monitor:
        raise HTTPException(status_code=503, detail="File monitor not initialized")

    status = file_monitor.get_status()
    return MonitoringStatus(**status)


@app.post("/start-monitoring")
async def start_monitoring(background_tasks: BackgroundTasks):
    """Start document monitoring"""
    global file_monitor

    if not file_monitor:
        raise HTTPException(status_code=503, detail="File monitor not initialized")

    try:
        await file_monitor.start()
        background_tasks.add_task(file_monitor.process_queued_events)
        return {"message": "Document monitoring started successfully"}
    except Exception as e:
        logger.error("Failed to start monitoring", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")


@app.post("/stop-monitoring")
async def stop_monitoring():
    """Stop document monitoring"""
    global file_monitor

    if not file_monitor:
        raise HTTPException(status_code=503, detail="File monitor not initialized")

    try:
        await file_monitor.stop()
        return {"message": "Document monitoring stopped successfully"}
    except Exception as e:
        logger.error("Failed to stop monitoring", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")


@app.post("/process-document")
async def manually_process_document(file_path: str):
    """Manually trigger processing for a specific document"""
    global file_monitor

    if not file_monitor:
        raise HTTPException(status_code=503, detail="File monitor not initialized")

    try:
        event = DocumentEvent(
            file_path=file_path,
            event_type="manual",
            file_size=0,  # Will be filled by event handler
            timestamp=""
        )

        # Trigger document processing
        result = await file_monitor.handle_manual_processing(event)
        return {"message": "Document processing triggered", "result": result}
    except Exception as e:
        logger.error("Failed to process document", file_path=file_path, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )