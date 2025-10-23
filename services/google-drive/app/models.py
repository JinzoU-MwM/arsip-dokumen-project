"""
Pydantic models for the Google Drive Service
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Document types for organization"""
    KTP = "ktp"
    KK = "kk"
    AKTA_KELAHIRAN = "akta_kelahiran"
    AKTA_KEMATIAN = "akta_kematian"
    AKTA_PERNIKAHAN = "akta_pernikahan"
    AKTA_PERCERAIAN = "akta_perceraian"
    IZIN_LOKASI = "izin_lokasi"
    SURAT_KEPEMILIKAN_TANAH = "surat_kepemilikan_tanah"
    NPWP = "npwp"
    SIUP = "siup"
    TDP = "tdp"
    LAINNYA = "lainnya"


class ShareRole(str, Enum):
    """Share roles for Google Drive"""
    OWNER = "owner"
    ORGANIZER = "organizer"
    FILE_ORGANIZER = "fileOrganizer"
    WRITER = "writer"
    COMMENTER = "commenter"
    READER = "reader"


class ProcessingStatus(str, Enum):
    """File processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Request Models
class UploadRequest(BaseModel):
    """Request model for file upload"""
    company_id: int = Field(..., description="Company ID")
    document_type: DocumentType = Field(..., description="Document type")
    folder_id: Optional[str] = Field(None, description="Specific folder ID")
    folder_name: Optional[str] = Field(None, description="Create new folder with this name")
    user_id: Optional[int] = Field(None, description="User ID uploading the file")
    description: Optional[str] = Field(None, description="File description")
    tags: Optional[List[str]] = Field(default_factory=list, description="File tags")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class FolderRequest(BaseModel):
    """Request model for folder creation"""
    company_id: int = Field(..., description="Company ID")
    folder_name: str = Field(..., description="Folder name")
    parent_folder_id: Optional[str] = Field(None, description="Parent folder ID")
    description: Optional[str] = Field(None, description="Folder description")
    create_structure: bool = Field(False, description="Create standard subfolders")


class SearchRequest(BaseModel):
    """Request model for file search"""
    query: str = Field(..., description="Search query")
    company_id: Optional[int] = Field(None, description="Filter by company ID")
    document_type: Optional[DocumentType] = Field(None, description="Filter by document type")
    folder_id: Optional[str] = Field(None, description="Search within specific folder")
    created_after: Optional[datetime] = Field(None, description="Filter files created after this date")
    created_before: Optional[datetime] = Field(None, description="Filter files created before this date")
    file_types: Optional[List[str]] = Field(None, description="Filter by MIME types")
    max_results: int = Field(100, description="Maximum number of results")
    page_token: Optional[str] = Field(None, description="Pagination token")


class ShareRequest(BaseModel):
    """Request model for file sharing"""
    email: str = Field(..., description="Email address to share with")
    role: ShareRole = Field(ShareRole.READER, description="Share role")
    send_notification_email: bool = Field(True, description="Send notification email")
    message: Optional[str] = Field(None, description="Custom message for the recipient")


class UpdateMetadataRequest(BaseModel):
    """Request model for updating file metadata"""
    name: Optional[str] = Field(None, description="New file name")
    description: Optional[str] = Field(None, description="File description")
    tags: Optional[List[str]] = Field(None, description="File tags")
    properties: Optional[Dict[str, str]] = Field(None, description="Custom properties")
    folder_id: Optional[str] = Field(None, description="Move to different folder")


# Response Models
class FileMetadata(BaseModel):
    """File metadata from Google Drive"""
    id: str = Field(..., description="File ID")
    name: str = Field(..., description="File name")
    mime_type: str = Field(..., description="MIME type")
    size: Optional[int] = Field(None, description="File size in bytes")
    created_time: datetime = Field(..., description="Creation time")
    modified_time: datetime = Field(..., description="Last modified time")
    parents: List[str] = Field(default_factory=list, description="Parent folder IDs")
    drive_url: str = Field(..., description="Google Drive URL")
    thumbnail_link: Optional[str] = Field(None, description="Thumbnail URL")
    web_view_link: str = Field(..., description="Web view link")
    web_content_link: Optional[str] = Field(None, description="Direct download link")
    description: Optional[str] = Field(None, description="File description")
    tags: List[str] = Field(default_factory=list, description="File tags")
    properties: Dict[str, str] = Field(default_factory=dict, description="Custom properties")
    company_id: Optional[int] = Field(None, description="Associated company ID")
    document_type: Optional[DocumentType] = Field(None, description="Document type")
    user_id: Optional[int] = Field(None, description="Uploaded by user ID")
    processing_status: ProcessingStatus = Field(ProcessingStatus.COMPLETED, description="Processing status")


class UploadResponse(BaseModel):
    """Response model for file upload"""
    success: bool = Field(..., description="Upload success status")
    file_id: Optional[str] = Field(None, description="Uploaded file ID")
    filename: str = Field(..., description="Original filename")
    drive_url: Optional[str] = Field(None, description="Google Drive URL")
    file_metadata: Optional[FileMetadata] = Field(None, description="Complete file metadata")
    folder_id: Optional[str] = Field(None, description="Folder ID where file was uploaded")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if upload failed")
    warnings: List[str] = Field(default_factory=list, description="Upload warnings")


class FolderResponse(BaseModel):
    """Response model for folder creation"""
    success: bool = Field(..., description="Creation success status")
    folder_id: str = Field(..., description="Created folder ID")
    folder_name: str = Field(..., description="Folder name")
    drive_url: str = Field(..., description="Google Drive URL")
    parent_folder_id: Optional[str] = Field(None, description="Parent folder ID")
    created_subfolders: List[str] = Field(default_factory=list, description="Created subfolder IDs")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if creation failed")


class SearchResponse(BaseModel):
    """Response model for file search"""
    success: bool = Field(..., description="Search success status")
    files: List[FileMetadata] = Field(..., description="Found files")
    total_count: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Search query used")
    next_page_token: Optional[str] = Field(None, description="Token for next page")
    processing_time_ms: Optional[float] = Field(None, description="Search processing time")
    search_applied_filters: Dict[str, Any] = Field(default_factory=dict, description="Filters applied")


class ShareResponse(BaseModel):
    """Response model for file sharing"""
    success: bool = Field(..., description="Share success status")
    file_id: str = Field(..., description="Shared file ID")
    email: str = Field(..., description="Email shared with")
    role: ShareRole = Field(..., description="Share role granted")
    share_id: Optional[str] = Field(None, description="Share ID")
    share_url: Optional[str] = Field(None, description="Shareable URL")
    expiration_date: Optional[datetime] = Field(None, description="Share expiration date")
    processing_time_ms: Optional[float] = Field(None, description="Share processing time")
    error_message: Optional[str] = Field(None, description="Error message if sharing failed")


class DriveStats(BaseModel):
    """Drive service statistics"""
    service: str = Field(..., description="Service name")
    uptime: str = Field(..., description="Service uptime status")
    timestamp: datetime = Field(..., description="Statistics timestamp")
    components: Dict[str, bool] = Field(..., description="Component health status")
    total_files_processed: int = Field(default=0, description="Total files processed")
    successful_uploads: int = Field(default=0, description="Successful uploads")
    failed_uploads: int = Field(default=0, description="Failed uploads")
    total_storage_used_mb: float = Field(default=0, description="Storage used in MB")
    total_folders_created: int = Field(default=0, description="Total folders created")
    active_companies: int = Field(default=0, description="Active companies using the service")
    most_common_document_types: List[Dict[str, Any]] = Field(default_factory=list, description="Most common document types")
    average_file_size_kb: float = Field(default=0, description="Average file size in KB")
    drive_manager_stats: Optional[Dict[str, Any]] = Field(None, description="Drive manager statistics")
    file_processor_stats: Optional[Dict[str, Any]] = Field(None, description="File processor statistics")


class CompanyFolderStructure(BaseModel):
    """Company folder structure model"""
    company_id: int = Field(..., description="Company ID")
    root_folder_id: str = Field(..., description="Root folder ID")
    root_folder_name: str = Field(..., description="Root folder name")
    document_folders: Dict[str, str] = Field(default_factory=dict, description="Document type folder IDs")
    archive_folder_id: Optional[str] = Field(None, description="Archive folder ID")
    temp_folder_id: Optional[str] = Field(None, description="Temporary folder ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    drive_url: str = Field(..., description="Root folder Drive URL")


class FileProcessingResult(BaseModel):
    """File processing result"""
    success: bool = Field(..., description="Processing success")
    original_filename: str = Field(..., description="Original filename")
    processed_filename: Optional[str] = Field(None, description="Processed filename")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="Detected MIME type")
    virus_scan_result: Optional[str] = Field(None, description="Virus scan result")
    thumbnail_generated: bool = Field(default=False, description="Whether thumbnail was generated")
    metadata_extracted: bool = Field(default=False, description="Whether metadata was extracted")
    processing_time_ms: float = Field(..., description="Processing time")
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")


class BatchOperationResult(BaseModel):
    """Result of batch operations"""
    total_operations: int = Field(..., description="Total operations attempted")
    successful_operations: int = Field(..., description="Successful operations")
    failed_operations: int = Field(..., description="Failed operations")
    success_rate: float = Field(..., description="Success rate percentage")
    operation_type: str = Field(..., description="Type of operation")
    results: List[Dict[str, Any]] = Field(..., description="Individual operation results")
    processing_time_ms: float = Field(..., description="Total processing time")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Operation timestamp")


class DriveActivity(BaseModel):
    """Drive activity log"""
    activity_id: str = Field(..., description="Activity ID")
    user_id: Optional[int] = Field(None, description="User ID who performed action")
    company_id: Optional[int] = Field(None, description="Company ID")
    action: str = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Type of resource (file/folder)")
    resource_id: str = Field(..., description="Resource ID")
    resource_name: str = Field(..., description="Resource name")
    timestamp: datetime = Field(..., description="Activity timestamp")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")
    ip_address: Optional[str] = Field(None, description="User IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")


class QuotaUsage(BaseModel):
    """Drive quota usage information"""
    used_bytes: int = Field(..., description="Used storage in bytes")
    total_bytes: int = Field(..., description="Total available storage in bytes")
    used_percentage: float = Field(..., description="Percentage of storage used")
    files_count: int = Field(..., description="Number of files")
    folders_count: int = Field(..., description="Number of folders")
    last_updated: datetime = Field(..., description="Last update timestamp")