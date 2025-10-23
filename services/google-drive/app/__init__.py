"""
Google Drive Service
Handles document storage, retrieval, and organization in Google Drive
"""

from .main import app
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
    DriveStats,
    DocumentType,
    ShareRole,
    ProcessingStatus,
    BatchUploadRequest,
    BatchUploadResponse,
    UpdateMetadataRequest,
    CompanyFolderStructure,
    FileProcessingResult,
    DriveActivity,
    QuotaUsage
)

__version__ = "1.0.0"
__service_name__ = "google-drive"

__all__ = [
    "app",
    "DriveManager",
    "FileProcessor",
    "UploadRequest",
    "UploadResponse",
    "FileMetadata",
    "FolderRequest",
    "FolderResponse",
    "SearchRequest",
    "SearchResponse",
    "ShareRequest",
    "ShareResponse",
    "DriveStats",
    "DocumentType",
    "ShareRole",
    "ProcessingStatus",
    "BatchUploadRequest",
    "BatchUploadResponse",
    "UpdateMetadataRequest",
    "CompanyFolderStructure",
    "FileProcessingResult",
    "DriveActivity",
    "QuotaUsage"
]