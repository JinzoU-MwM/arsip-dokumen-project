"""
pytest configuration and fixtures for AI-Driven Legal Document Automation System

This file contains shared test fixtures, configuration, and utilities for all tests.
"""

import pytest
import asyncio
import tempfile
import os
import json
import time
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timedelta
import uuid
import hashlib
from typing import Dict, Any, List, Generator
import logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database fixtures (will be implemented when database modules are available)
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from shared.database.models import Base

# Test Configuration
TEST_CONFIG = {
    "test_company": {
        "id": "company_test_001",
        "name": "PT Test Company",
        "business_type": "PT",
        "required_documents": ["KTP", "NPWP", "Akta", "SIUP"],
        "address": "Jl. Test Street No. 1, Jakarta",
        "phone": "+6221-1234567",
        "email": "test@example.com"
    },
    "test_user": {
        "id": "user_test_001",
        "email": "testuser@example.com",
        "name": "Test User",
        "role": "document_manager",
        "company_id": "company_test_001",
        "is_active": True
    },
    "test_documents": {
        "ktp": {
            "id": "doc_ktp_001",
            "type": "KTP",
            "filename": "ktp_test.pdf",
            "content_type": "application/pdf",
            "size": 1024
        },
        "npwp": {
            "id": "doc_npwp_001",
            "type": "NPWP",
            "filename": "npwp_test.pdf",
            "content_type": "application/pdf",
            "size": 2048
        }
    }
}


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration data."""
    return TEST_CONFIG


@pytest.fixture
def temp_directory():
    """Create a temporary directory for file operations."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_pdf_file(temp_directory):
    """Create a sample PDF file for testing."""
    pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Hello World) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000110 00000 n\n0000000201 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n312\n%%EOF\n'

    pdf_path = temp_directory / "test_document.pdf"
    pdf_path.write_bytes(pdf_content)
    return pdf_path


@pytest.fixture
def sample_image_file(temp_directory):
    """Create a sample image file for testing."""
    # Create a minimal 1x1 PNG image
    png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01\xe2!\xbc\x33\x00\x00\x00\x00IEND\xaeB`\x82'

    image_path = temp_directory / "test_image.png"
    image_path.write_bytes(png_content)
    return image_path


@pytest.fixture
def mock_services():
    """Create mock instances of all microservices."""
    return {
        "document_watcher": AsyncMock(),
        "ai_processor": AsyncMock(),
        "validation_engine": AsyncMock(),
        "google_drive_service": AsyncMock(),
        "audit_service": AsyncMock(),
        "notification_service": AsyncMock(),
        "auth_service": AsyncMock(),
        "web_dashboard": AsyncMock()
    }


@pytest.fixture
def mock_database_session():
    """Create a mock database session."""
    # TODO: Implement when database models are available
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine)
    # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # session = SessionLocal()
    # yield session
    # session.close()

    # Mock session for now
    mock_session = Mock()
    mock_session.add = Mock()
    mock_session.commit = Mock()
    mock_session.rollback = Mock()
    mock_session.query = Mock()
    mock_session.close = Mock()
    return mock_session


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=True)
    mock_redis.exists = AsyncMock(return_value=False)
    mock_redis.expire = AsyncMock(return_value=True)
    return mock_redis


@pytest.fixture
def mock_jwt_token():
    """Create a mock JWT token for testing."""
    payload = {
        "user_id": "user_test_001",
        "company_id": "company_test_001",
        "roles": ["document_manager", "viewer"],
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4())
    }
    # TODO: Implement when jwt module is available
    # token = jwt.encode(payload, "test_secret", algorithm="HS256")
    # return token
    return "mock_jwt_token_12345"


@pytest.fixture
def mock_google_drive_service():
    """Create a mock Google Drive service."""
    mock_drive = Mock()
    mock_drive.files = Mock()
    mock_drive.files.create = Mock(return_value=Mock(execute=Mock(return_value={"id": "file_123"})))
    mock_drive.files.get = Mock(return_value=Mock(execute=Mock(return_value={"name": "test.pdf"})))
    mock_drive.files.list = Mock(return_value=Mock(execute=Mock(return_value={"files": []})))
    mock_drive.permissions = Mock()
    mock_drive.permissions.create = Mock(return_value=Mock(execute=Mock(return_value={"id": "perm_123"})))
    return mock_drive


@pytest.fixture
def mock_whatsapp_service():
    """Create a mock WhatsApp notification service."""
    mock_whatsapp = AsyncMock()
    mock_whatsapp.send_message = AsyncMock(return_value={"status": "sent", "message_id": "msg_123"})
    mock_whatsapp.send_template = AsyncMock(return_value={"status": "sent", "message_id": "msg_124"})
    return mock_whatsapp


@pytest.fixture
def sample_company_data(test_config):
    """Provide sample company data for testing."""
    return test_config["test_company"]


@pytest.fixture
def sample_user_data(test_config):
    """Provide sample user data for testing."""
    return test_config["test_user"]


@pytest.fixture
def sample_document_data(test_config):
    """Provide sample document data for testing."""
    return test_config["test_documents"]


@pytest.fixture
def sample_processing_job():
    """Create a sample document processing job."""
    return {
        "job_id": str(uuid.uuid4()),
        "document_id": "doc_001",
        "company_id": "company_test_001",
        "status": "processing",
        "started_at": datetime.utcnow().isoformat(),
        "steps": [
            {"name": "file_detection", "status": "completed", "duration_ms": 100},
            {"name": "ai_classification", "status": "in_progress", "duration_ms": None},
            {"name": "compliance_validation", "status": "pending", "duration_ms": None},
            {"name": "drive_upload", "status": "pending", "duration_ms": None},
            {"name": "notification", "status": "pending", "duration_ms": None}
        ]
    }


@pytest.fixture
def sample_audit_event():
    """Create a sample audit event."""
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "document_upload",
        "user_id": "user_test_001",
        "company_id": "company_test_001",
        "resource_id": "doc_001",
        "action": "CREATE",
        "timestamp": datetime.utcnow().isoformat(),
        "ip_address": "127.0.0.1",
        "user_agent": "pytest-test-agent",
        "details": {
            "filename": "test_document.pdf",
            "file_size": 1024,
            "document_type": "KTP"
        },
        "outcome": "SUCCESS",
        "risk_score": 2
    }


@pytest.fixture
def sample_compliance_result():
    """Create a sample compliance validation result."""
    return {
        "document_id": "doc_001",
        "company_id": "company_test_001",
        "is_compliant": True,
        "compliance_score": 95,
        "validation_checks": [
            {
                "check_name": "document_format",
                "status": "passed",
                "details": "PDF format is valid"
            },
            {
                "check_name": "document_completeness",
                "status": "passed",
                "details": "All required fields are present"
            },
            {
                "check_name": "expiry_validation",
                "status": "passed",
                "details": "Document is not expired"
            }
        ],
        "missing_documents": [],
        "expiring_documents": [],
        "recommendations": [
            "Document is in good standing",
            "No action required"
        ]
    }


# Async test fixtures
@pytest.fixture
async def async_client():
    """Create an async HTTP client for API testing."""
    # TODO: Implement when httpx is available
    # import httpx
    # async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
    #     yield client

    # Mock client for now
    mock_client = AsyncMock()
    mock_client.get = AsyncMock()
    mock_client.post = AsyncMock()
    mock_client.put = AsyncMock()
    mock_client.delete = AsyncMock()
    yield mock_client


# Environment-specific fixtures
@pytest.fixture
def test_database_url():
    """Provide test database URL."""
    return os.getenv("TEST_DATABASE_URL", "postgresql://test:test@localhost/test_legal_automation")


@pytest.fixture
def test_redis_url():
    """Provide test Redis URL."""
    return os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")


@pytest.fixture
def test_google_drive_credentials():
    """Provide test Google Drive credentials."""
    return {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789012345678901",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com"
    }


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically cleanup test files after each test."""
    yield
    # Cleanup logic can be added here if needed


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks after each test."""
    yield
    # Reset mock call counts
    Mock.reset_mock()


# Performance testing fixtures
@pytest.fixture
def performance_thresholds():
    """Define performance thresholds for testing."""
    return {
        "document_processing": {
            "max_duration_ms": 30000,  # 30 seconds
            "min_throughput_per_hour": 1000
        },
        "api_endpoints": {
            "max_response_time_ms": 2000,  # 2 seconds
            "max_cpu_usage_percent": 70
        },
        "file_upload": {
            "max_upload_time_mb_per_second": 10  # 10 MB/s minimum
        }
    }


# Security testing fixtures
@pytest.fixture
def security_test_data():
    """Provide security test data."""
    return {
        "malicious_file": "test_malicious.pdf",
        "oversized_file_size": 100 * 1024 * 1024,  # 100MB
        "invalid_jwt": "invalid.jwt.token",
        "sql_injection_payloads": [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "1; DELETE FROM users WHERE 1=1 --"
        ],
        "xss_payloads": [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>"
        ]
    }


if __name__ == "__main__":
    # This allows running conftest.py directly for testing
    pytest.main([__file__])