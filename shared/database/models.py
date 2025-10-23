"""
Shared database models for the AI Legal Document Automation System
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime
from typing import Optional, Dict, Any

Base = declarative_base()


class UserStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class UserRole(enum.Enum):
    ADMIN = "admin"
    LEGAL_ADMIN = "legal_admin"
    COMPANY_USER = "company_user"
    VIEWER = "viewer"


class DocumentStatus(enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    VALIDATED = "validated"
    REJECTED = "rejected"


class ProcessingStatus(enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationStatus(enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class ComplianceStatus(enum.Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    REQUIRES_REVIEW = "requires_review"


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), unique=True, index=True)

    # Authentication
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(255), nullable=False)

    # User information
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.COMPANY_USER)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.ACTIVE)

    # Company association
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)

    # Permissions and settings
    permissions = Column(JSON, default=list)
    notification_preferences = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    company = relationship("Company", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role.value})>"


class Company(Base):
    """Company model for multi-tenant architecture"""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)

    # Company identification
    npwp = Column(String(20), unique=True, index=True)
    nib = Column(String(15), unique=True, index=True)
    company_type = Column(String(50))  # PT, CV, etc.

    # Contact information
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(255))

    # Industry and business info
    industry = Column(String(100))
    business_description = Column(Text)

    # Compliance and settings
    compliance_requirements = Column(JSON, default=dict)
    notification_settings = Column(JSON, default=dict)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="company")
    documents = relationship("Document", back_populates="company")
    processing_jobs = relationship("ProcessingJob", back_populates="company")
    notifications = relationship("Notification", back_populates="company")

    def __repr__(self):
        return f"<Company(id={self.id}, name={self.name}, npwp={self.npwp})>"


class Document(Base):
    """Document model for storing document metadata"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    # File information
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), index=True)  # SHA-256 hash

    # Classification
    document_type = Column(String(50), nullable=False, index=True)  # Akta, NPWP, etc.
    subcategory = Column(String(100))
    confidence_score = Column(Float)

    # Status
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADED)

    # Processing information
    processing_id = Column(String(100), unique=True, index=True)
    processing_time = Column(Float)  # seconds

    # Content and metadata
    text_content = Column(Text)  # Extracted text (truncated)
    extracted_entities = Column(JSON)
    ai_analysis = Column(JSON)

    # Compliance
    compliance_status = Column(SQLEnum(ComplianceStatus))
    compliance_score = Column(Float)
    missing_documents = Column(JSON, default=list)

    # Storage
    drive_file_id = Column(String(255))
    drive_folder_id = Column(String(255))
    drive_url = Column(String(500))

    # Associations
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True))

    # Relationships
    company = relationship("Company", back_populates="documents")
    uploader = relationship("User")
    processing_jobs = relationship("ProcessingJob", back_populates="document")

    def __repr__(self):
        return f"<Document(id={self.id}, type={self.document_type}, status={self.status.value})>"


class ProcessingJob(Base):
    """Processing job model for tracking document processing"""
    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    processing_id = Column(String(100), unique=True, index=True, nullable=False)

    # Job information
    job_type = Column(String(50), nullable=False)  # document_processing, classification, etc.
    status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.QUEUED)
    priority = Column(String(20), default="normal")  # low, normal, high, urgent

    # Progress tracking
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String(100))
    total_steps = Column(Integer, default=1)

    # Input and output
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)

    # Performance metrics
    processing_time = Column(Float)  # total time in seconds
    cpu_usage = Column(Float)
    memory_usage = Column(Float)

    # Associations
    document_id = Column(Integer, ForeignKey("documents.id"))
    company_id = Column(Integer, ForeignKey("companies.id"))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    document = relationship("Document", back_populates="processing_jobs")
    company = relationship("Company", back_populates="processing_jobs")

    def __repr__(self):
        return f"<ProcessingJob(id={self.id}, processing_id={self.processing_id}, status={self.status.value})>"


class Notification(Base):
    """Notification model for tracking sent notifications"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    # Notification details
    notification_type = Column(String(50), nullable=False, index=True)
    channel = Column(String(20), nullable=False)  # whatsapp, email, sms
    recipient = Column(String(255), nullable=False)

    # Content
    subject = Column(String(255))
    message = Column(Text, nullable=False)
    template_name = Column(String(100))
    template_data = Column(JSON)

    # Status tracking
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
    sent_at = Column(DateTime(timezone=True))
    delivery_confirmed_at = Column(DateTime(timezone=True))

    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Associations
    company_id = Column(Integer, ForeignKey("companies.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    document_id = Column(Integer, ForeignKey("documents.id"))
    processing_job_id = Column(Integer, ForeignKey("processing_jobs.id"))

    # External service tracking
    external_id = Column(String(255))  # WhatsApp message ID, email ID, etc.
    external_status = Column(String(100))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    scheduled_at = Column(DateTime(timezone=True))

    # Relationships
    company = relationship("Company", back_populates="notifications")
    user = relationship("User")
    document = relationship("Document")
    processing_job = relationship("ProcessingJob")

    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.notification_type}, status={self.status.value})>"


class AuditLog(Base):
    """Audit log model for compliance and security tracking"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Event information
    event_type = Column(String(100), nullable=False, index=True)
    event_category = Column(String(50), nullable=False, index=True)  # auth, document, system
    action = Column(String(100), nullable=False)

    # User and session
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(String(255))
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(500))

    # Resource information
    resource_type = Column(String(50))  # document, user, company, etc.
    resource_id = Column(String(100))
    resource_details = Column(JSON)

    # Event details
    description = Column(Text)
    old_values = Column(JSON)
    new_values = Column(JSON)

    # Result
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    # Sensitivity and compliance
    sensitivity_level = Column(String(20), default="normal")  # low, normal, high, critical
    compliance_tags = Column(JSON, default=list)

    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, user_id={self.user_id})>"


class SystemConfiguration(Base):
    """System configuration model for dynamic settings"""
    __tablename__ = "system_configurations"

    id = Column(Integer, primary_key=True, index=True)

    # Configuration key and value
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(JSON)
    description = Column(Text)

    # Configuration metadata
    category = Column(String(50), nullable=False, index=True)
    is_sensitive = Column(Boolean, default=False)
    is_encrypted = Column(Boolean, default=False)

    # Validation
    validation_schema = Column(JSON)  # JSON schema for validation
    allowed_values = Column(JSON, default=list)

    # Versioning
    version = Column(Integer, default=1)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"))

    def __repr__(self):
        return f"<SystemConfiguration(key={self.config_key}, category={self.category})>"


class APIKey(Base):
    """API key model for external service authentication"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)

    # Key information
    key_name = Column(String(100), nullable=False)
    api_key = Column(String(255), unique=True, nullable=False, index=True)
    key_hash = Column(String(64), unique=True, nullable=False)  # SHA-256 hash

    # Permissions and restrictions
    permissions = Column(JSON, default=list)
    allowed_endpoints = Column(JSON, default=list)
    rate_limit = Column(Integer, default=1000)  # requests per hour

    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))

    # Usage tracking
    last_used = Column(DateTime(timezone=True))
    usage_count = Column(Integer, default=0)

    # Associations
    company_id = Column(Integer, ForeignKey("companies.id"))
    created_by = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<APIKey(id={self.id}, name={self.key_name}, active={self.is_active})>"