"""
AI Processing Service
Handles document classification, OCR, NLP processing, and multi-AI collaboration
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import structlog
import uvicorn
import asyncio
import uuid
from contextlib import asynccontextmanager

from .document_classifier import DocumentClassifier
from .ocr_processor import OCRProcessor
from .nlp_processor import NLPProcessor
from .ollama_client import OllamaClient

# Configure structured logging
logger = structlog.get_logger()

# Global variables
document_classifier: DocumentClassifier = None
ocr_processor: OCRProcessor = None
nlp_processor: NLPProcessor = None
ollama_client: OllamaClient = None

# In-memory storage for processing jobs (in production, use Redis/DB)
processing_jobs: Dict[str, Dict[str, Any]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global document_classifier, ocr_processor, nlp_processor, ollama_client

    logger.info("Starting AI Processing Service")

    # Initialize AI components
    try:
        document_classifier = DocumentClassifier()
        ocr_processor = OCRProcessor()
        nlp_processor = NLPProcessor()
        ollama_client = OllamaClient()

        await document_classifier.initialize()
        await ocr_processor.initialize()
        await nlp_processor.initialize()
        await ollama_client.initialize()

        logger.info("AI Processing Service initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize AI components", error=str(e))
        raise

    yield

    logger.info("Shutting down AI Processing Service")
    # Cleanup resources
    if ollama_client:
        await ollama_client.cleanup()


# Create FastAPI application
app = FastAPI(
    title="AI Processing Service",
    description="AI-powered document classification, OCR, and NLP processing",
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
class DocumentProcessingRequest(BaseModel):
    """Document processing request model"""
    file_path: str
    event_type: str
    priority: str = "normal"
    company_hint: Optional[str] = None


class ProcessingStatus(BaseModel):
    """Processing status model"""
    processing_id: str
    status: str  # queued, processing, completed, failed
    progress: int  # 0-100
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class ProcessingResponse(BaseModel):
    """Processing response model"""
    success: bool
    processing_id: str
    message: str
    estimated_time: Optional[int] = None  # seconds


# API endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-processor",
        "components": {
            "classifier": document_classifier is not None,
            "ocr": ocr_processor is not None,
            "nlp": nlp_processor is not None,
            "ollama": ollama_client is not None
        }
    }


@app.post("/process-document", response_model=ProcessingResponse)
async def process_document(request: DocumentProcessingRequest, background_tasks: BackgroundTasks):
    """Start document processing"""
    global document_classifier, ocr_processor, nlp_processor, ollama_client

    if not all([document_classifier, ocr_processor, nlp_processor, ollama_client]):
        raise HTTPException(status_code=503, detail="AI components not initialized")

    # Generate unique processing ID
    processing_id = str(uuid.uuid4())

    # Create processing job
    processing_job = {
        "processing_id": processing_id,
        "file_path": request.file_path,
        "event_type": request.event_type,
        "priority": request.priority,
        "company_hint": request.company_hint,
        "status": "queued",
        "progress": 0,
        "results": None,
        "error": None,
        "started_at": None,
        "completed_at": None,
        "created_at": asyncio.get_event_loop().time()
    }

    processing_jobs[processing_id] = processing_job

    # Start background processing
    background_tasks.add_task(process_document_background, processing_id, request)

    logger.info("Document processing started",
               processing_id=processing_id,
               file_path=request.file_path)

    return ProcessingResponse(
        success=True,
        processing_id=processing_id,
        message="Document processing started",
        estimated_time=30  # seconds
    )


@app.get("/processing-status/{processing_id}", response_model=ProcessingStatus)
async def get_processing_status(processing_id: str):
    """Get processing status"""
    if processing_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Processing job not found")

    job = processing_jobs[processing_id]
    return ProcessingStatus(**job)


@app.get("/active-jobs")
async def get_active_jobs():
    """Get all active processing jobs"""
    active_jobs = [
        job for job in processing_jobs.values()
        if job["status"] in ["queued", "processing"]
    ]
    return {"active_jobs": active_jobs, "count": len(active_jobs)}


@app.delete("/processing-job/{processing_id}")
async def cancel_processing_job(processing_id: str):
    """Cancel a processing job"""
    if processing_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Processing job not found")

    job = processing_jobs[processing_id]
    if job["status"] not in ["queued", "processing"]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed job")

    job["status"] = "cancelled"
    job["completed_at"] = asyncio.get_event_loop().time()

    logger.info("Processing job cancelled", processing_id=processing_id)
    return {"message": "Processing job cancelled"}


@app.post("/classify-text")
async def classify_text_endpoint(text: str):
    """Classify text content directly"""
    global document_classifier

    if not document_classifier:
        raise HTTPException(status_code=503, detail="Document classifier not available")

    try:
        result = await document_classifier.classify_text(text)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error("Text classification failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@app.post("/extract-entities")
async def extract_entities_endpoint(text: str):
    """Extract entities from text"""
    global nlp_processor

    if not nlp_processor:
        raise HTTPException(status_code=503, detail="NLP processor not available")

    try:
        result = await nlp_processor.extract_entities(text)
        return {"success": True, "entities": result}
    except Exception as e:
        logger.error("Entity extraction failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Entity extraction failed: {str(e)}")


async def process_document_background(processing_id: str, request: DocumentProcessingRequest):
    """Background task for document processing"""
    global document_classifier, ocr_processor, nlp_processor, ollama_client

    job = processing_jobs[processing_id]

    try:
        # Update job status
        job["status"] = "processing"
        job["started_at"] = asyncio.get_event_loop().time()
        job["progress"] = 10

        logger.info("Starting background processing", processing_id=processing_id)

        # Step 1: Extract text using OCR (if needed)
        job["progress"] = 20
        text_content = await ocr_processor.extract_text(request.file_path)

        if not text_content:
            raise Exception("Failed to extract text from document")

        job["progress"] = 40
        logger.info("Text extraction completed", processing_id=processing_id)

        # Step 2: Classify document
        job["progress"] = 60
        classification_result = await document_classifier.classify_document(
            text_content, request.file_path
        )

        job["progress"] = 70
        logger.info("Document classification completed",
                   processing_id=processing_id,
                   classification=classification_result["category"])

        # Step 3: Extract entities using NLP
        job["progress"] = 80
        entities = await nlp_processor.extract_entities(text_content)

        # Step 4: Advanced AI analysis using Ollama
        job["progress"] = 90
        ai_analysis = await ollama_client.analyze_document(
            text_content, classification_result, entities, request.company_hint
        )

        # Compile results
        results = {
            "text_content": text_content[:1000] + "..." if len(text_content) > 1000 else text_content,
            "classification": classification_result,
            "entities": entities,
            "ai_analysis": ai_analysis,
            "processing_time": asyncio.get_event_loop().time() - job["started_at"],
            "file_path": request.file_path
        }

        # Update job with results
        job["status"] = "completed"
        job["progress"] = 100
        job["results"] = results
        job["completed_at"] = asyncio.get_event_loop().time()

        logger.info("Document processing completed successfully",
                   processing_id=processing_id,
                   category=classification_result["category"],
                   confidence=classification_result.get("confidence", 0))

    except Exception as e:
        logger.error("Document processing failed",
                    processing_id=processing_id,
                    error=str(e))

        job["status"] = "failed"
        job["error"] = str(e)
        job["completed_at"] = asyncio.get_event_loop().time()

    # Cleanup old jobs (keep last 100)
    if len(processing_jobs) > 100:
        oldest_jobs = sorted(
            [(pid, job) for pid, job in processing_jobs.items()],
            key=lambda x: x[1]["created_at"]
        )[:50]

        for pid, _ in oldest_jobs:
            del processing_jobs[pid]


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )