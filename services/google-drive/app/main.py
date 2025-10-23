"""
Google Drive Service
Handles document storage, retrieval, and organization in Google Drive
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import structlog
import uvicorn
import asyncio
import os
import tempfile
from contextlib import asynccontextmanager
from datetime import datetime

from .drive_manager import DriveManager
from .file_processor import FileProcessor
from .models import (
    UploadRequest,
    UploadResponse,
    FileMetadata,
    FolderRequest,
    FolderResponse,
    SearchRequest,
    SearchResponse,
    ShareRequest,
    ShareResponse,
    DriveStats
)

# Configure structured logging
logger = structlog.get_logger()

# Global variables
drive_manager: DriveManager = None
file_processor: FileProcessor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global drive_manager, file_processor

    logger.info("Starting Google Drive Service")

    # Initialize components
    try:
        drive_manager = DriveManager()
        file_processor = FileProcessor()

        await drive_manager.initialize()
        await file_processor.initialize()

        logger.info("Google Drive Service initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize Google Drive Service", error=str(e))
        raise

    yield

    logger.info("Shutting down Google Drive Service")
    # Cleanup resources
    if drive_manager:
        await drive_manager.cleanup()
    if file_processor:
        await file_processor.cleanup()


# Create FastAPI application
app = FastAPI(
    title="Google Drive Service",
    description="Document storage and organization in Google Drive",
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
class BatchUploadRequest(BaseModel):
    """Request model for batch upload"""
    company_id: int
    files: List[UploadRequest]
    create_folders: bool = True


class BatchUploadResponse(BaseModel):
    """Response model for batch upload"""
    success: bool
    total_files: int
    successful_uploads: int
    failed_uploads: int
    results: List[UploadResponse]
    folder_id: Optional[str] = None


# API endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "google-drive",
        "components": {
            "drive_manager": drive_manager is not None,
            "file_processor": file_processor is not None
        }
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    request: UploadRequest = Depends()
):
    """Upload a file to Google Drive"""
    try:
        logger.info("File upload requested",
                   filename=file.filename,
                   company_id=request.company_id,
                   document_type=request.document_type)

        # Validate file
        if not await file_processor.validate_file(file):
            raise HTTPException(status_code=400, detail="Invalid file format or size")

        # Process file
        processed_file = await file_processor.process_file(file, request)

        # Upload to Drive
        drive_result = await drive_manager.upload_file(processed_file, request)

        logger.info("File upload completed",
                   filename=file.filename,
                   file_id=drive_result.file_id,
                   drive_url=drive_result.drive_url)

        return drive_result

    except Exception as e:
        logger.error("File upload failed",
                     filename=file.filename,
                     error=str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/batch-upload", response_model=BatchUploadResponse)
async def batch_upload_files(
    files: List[UploadFile] = File(...),
    request: BatchUploadRequest = Depends()
):
    """Upload multiple files to Google Drive"""
    try:
        logger.info("Batch upload requested",
                   total_files=len(files),
                   company_id=request.company_id)

        results = []
        successful_uploads = 0
        failed_uploads = 0
        folder_id = None

        # Create folder if requested
        if request.create_folders:
            folder_request = FolderRequest(
                company_id=request.company_id,
                folder_name=f"Uploads_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            folder_response = await create_folder(folder_request)
            folder_id = folder_response.folder_id

        # Process each file
        for i, file in enumerate(files):
            try:
                # Update file request with folder
                file_request = request.files[i] if i < len(request.files) else UploadRequest(
                    company_id=request.company_id,
                    document_type="lainnya"
                )
                if folder_id:
                    file_request.folder_id = folder_id

                # Upload file
                result = await upload_file(file, file_request)
                results.append(result)
                successful_uploads += 1

            except Exception as e:
                logger.error("Batch upload item failed",
                           filename=file.filename,
                           error=str(e))
                failed_uploads += 1
                results.append(UploadResponse(
                    success=False,
                    filename=file.filename,
                    error_message=str(e)
                ))

        return BatchUploadResponse(
            success=failed_uploads == 0,
            total_files=len(files),
            successful_uploads=successful_uploads,
            failed_uploads=failed_uploads,
            results=results,
            folder_id=folder_id
        )

    except Exception as e:
        logger.error("Batch upload failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")


@app.post("/folders", response_model=FolderResponse)
async def create_folder(request: FolderRequest):
    """Create a folder in Google Drive"""
    try:
        logger.info("Folder creation requested",
                   folder_name=request.folder_name,
                   company_id=request.company_id)

        result = await drive_manager.create_folder(request)

        logger.info("Folder created successfully",
                   folder_name=request.folder_name,
                   folder_id=result.folder_id)

        return result

    except Exception as e:
        logger.error("Folder creation failed",
                     folder_name=request.folder_name,
                     error=str(e))
        raise HTTPException(status_code=500, detail=f"Folder creation failed: {str(e)}")


@app.get("/folders/{folder_id}/files", response_model=List[FileMetadata])
async def list_folder_files(folder_id: str):
    """List files in a folder"""
    try:
        logger.info("Listing folder files", folder_id=folder_id)

        files = await drive_manager.list_folder_files(folder_id)

        logger.info("Folder files listed",
                   folder_id=folder_id,
                   file_count=len(files))

        return files

    except Exception as e:
        logger.error("Failed to list folder files",
                     folder_id=folder_id,
                     error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@app.post("/search", response_model=SearchResponse)
async def search_files(request: SearchRequest):
    """Search for files in Google Drive"""
    try:
        logger.info("File search requested",
                   query=request.query,
                   company_id=request.company_id)

        results = await drive_manager.search_files(request)

        logger.info("File search completed",
                   query=request.query,
                   results_count=len(results.files))

        return results

    except Exception as e:
        logger.error("File search failed",
                     query=request.query,
                     error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/files/{file_id}", response_model=FileMetadata)
async def get_file_metadata(file_id: str):
    """Get file metadata"""
    try:
        logger.info("Getting file metadata", file_id=file_id)

        metadata = await drive_manager.get_file_metadata(file_id)

        logger.info("File metadata retrieved", file_id=file_id)

        return metadata

    except Exception as e:
        logger.error("Failed to get file metadata",
                     file_id=file_id,
                     error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get metadata: {str(e)}")


@app.get("/files/{file_id}/download")
async def download_file(file_id: str):
    """Download a file from Google Drive"""
    try:
        logger.info("File download requested", file_id=file_id)

        # Get file metadata
        metadata = await drive_manager.get_file_metadata(file_id)

        # Download file content
        file_content = await drive_manager.download_file(file_id)

        # Return as streaming response
        return StreamingResponse(
            file_content,
            media_type=metadata.mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={metadata.name}"
            }
        )

    except Exception as e:
        logger.error("File download failed",
                     file_id=file_id,
                     error=str(e))
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Delete a file from Google Drive"""
    try:
        logger.info("File deletion requested", file_id=file_id)

        success = await drive_manager.delete_file(file_id)

        if not success:
            raise HTTPException(status_code=404, detail="File not found")

        logger.info("File deleted successfully", file_id=file_id)

        return {"success": True, "message": "File deleted successfully"}

    except Exception as e:
        logger.error("File deletion failed",
                     file_id=file_id,
                     error=str(e))
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@app.post("/files/{file_id}/share", response_model=ShareResponse)
async def share_file(file_id: str, request: ShareRequest):
    """Share a file with specified users"""
    try:
        logger.info("File sharing requested",
                   file_id=file_id,
                   email=request.email)

        result = await drive_manager.share_file(file_id, request)

        logger.info("File shared successfully",
                   file_id=file_id,
                   email=request.email)

        return result

    except Exception as e:
        logger.error("File sharing failed",
                     file_id=file_id,
                     email=request.email,
                     error=str(e))
        raise HTTPException(status_code=500, detail=f"Sharing failed: {str(e)}")


@app.get("/stats", response_model=DriveStats)
async def get_drive_stats():
    """Get Drive service statistics"""
    try:
        stats = {
            "service": "google-drive",
            "uptime": "running",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "drive_manager": drive_manager is not None,
                "file_processor": file_processor is not None
            }
        }

        # Add statistics from components if available
        if drive_manager:
            stats["drive_manager_stats"] = await drive_manager.get_stats()

        if file_processor:
            stats["file_processor_stats"] = await file_processor.get_stats()

        return DriveStats(**stats)

    except Exception as e:
        logger.error("Failed to get drive stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.post("/folders/company/{company_id}")
async def create_company_folder_structure(company_id: int):
    """Create standardized folder structure for a company"""
    try:
        logger.info("Creating company folder structure", company_id=company_id)

        result = await drive_manager.create_company_folder_structure(company_id)

        logger.info("Company folder structure created",
                   company_id=company_id,
                   root_folder_id=result.get("root_folder_id"))

        return result

    except Exception as e:
        logger.error("Failed to create company folder structure",
                     company_id=company_id,
                     error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create folder structure: {str(e)}")


@app.get("/folders/company/{company_id}")
async def get_company_folders(company_id: int):
    """Get folder structure for a company"""
    try:
        logger.info("Getting company folders", company_id=company_id)

        folders = await drive_manager.get_company_folders(company_id)

        logger.info("Company folders retrieved",
                   company_id=company_id,
                   folder_count=len(folders))

        return folders

    except Exception as e:
        logger.error("Failed to get company folders",
                     company_id=company_id,
                     error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get folders: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,
        reload=True,
        log_level="info"
    )