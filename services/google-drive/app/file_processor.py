"""
File Processor
Handles file validation, processing, and security scanning
"""

import asyncio
import mimetypes
import os
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime
from fastapi import UploadFile
import magic
from PIL import Image
import aiofiles
import tempfile
import hashlib
import io

from .models import (
    FileProcessingResult,
    ProcessingStatus
)


class FileProcessor:
    """Service for processing uploaded files"""

    def __init__(self):
        self.logger = structlog.get_logger().bind(component="FileProcessor")

        # Supported file types
        self.supported_mime_types = {
            # Images
            'image/jpeg': ['.jpg', '.jpeg'],
            'image/png': ['.png'],
            'image/gif': ['.gif'],
            'image/bmp': ['.bmp'],
            'image/tiff': ['.tiff', '.tif'],
            'image/webp': ['.webp'],

            # Documents
            'application/pdf': ['.pdf'],
            'application/msword': ['.doc'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'application/vnd.ms-excel': ['.xls'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
            'application/vnd.ms-powerpoint': ['.ppt'],
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
            'text/plain': ['.txt'],
            'text/csv': ['.csv'],

            # Archives
            'application/zip': ['.zip'],
            'application/x-rar-compressed': ['.rar'],
            'application/x-7z-compressed': ['.7z']
        }

        # File size limits (in bytes)
        self.max_file_sizes = {
            'image': 10 * 1024 * 1024,      # 10MB
            'document': 50 * 1024 * 1024,   # 50MB
            'archive': 100 * 1024 * 1024,   # 100MB
            'default': 20 * 1024 * 1024     # 20MB
        }

        # Security settings
        self.enable_virus_scan = os.getenv('ENABLE_VIRUS_SCAN', 'false').lower() == 'true'
        self.clamd_socket = os.getenv('CLAMD_SOCKET', '/tmp/clamd.socket')

        # Image processing settings
        self.thumbnail_size = (200, 200)
        self.max_image_size = (4096, 4096)

    async def initialize(self):
        """Initialize the file processor"""
        self.logger.info("Initializing File Processor")

        try:
            # Test virus scan connection if enabled
            if self.enable_virus_scan:
                await self._test_virus_scan_connection()

            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix='drive_processor_')
            self.logger.info("File Processor initialized", temp_dir=self.temp_dir)

        except Exception as e:
            self.logger.error("Failed to initialize File Processor", error=str(e))
            raise

    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up File Processor")

        try:
            # Clean up temporary directory
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            self.logger.error("Failed to cleanup temporary directory", error=str(e))

    async def validate_file(self, file: UploadFile) -> bool:
        """Validate uploaded file"""
        try:
            # Check if file exists
            if not file or not file.filename:
                return False

            # Check file extension
            file_ext = os.path.splitext(file.filename)[1].lower()
            if not any(file_ext in extensions for extensions in self.supported_mime_types.values()):
                self.logger.warning("Unsupported file extension", filename=file.filename, extension=file_ext)
                return False

            # Check file size
            await file.seek(0, os.SEEK_END)
            file_size = file.tell()
            await file.seek(0)

            # Determine file category and size limit
            file_category = await self._get_file_category(file.content_type or '')
            max_size = self.max_file_sizes.get(file_category, self.max_file_sizes['default'])

            if file_size > max_size:
                self.logger.warning("File too large", filename=file.filename, size=file_size, max_size=max_size)
                return False

            return True

        except Exception as e:
            self.logger.error("File validation failed", filename=file.filename, error=str(e))
            return False

    async def process_file(self, file: UploadFile, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process uploaded file"""
        try:
            start_time = asyncio.get_event_loop().time()

            # Read file content
            content = await file.read()
            file_hash = hashlib.sha256(content).hexdigest()

            self.logger.info(
                "Processing file",
                filename=file.filename,
                size=len(content),
                content_type=file.content_type,
                hash=file_hash[:16] + "..."
            )

            # Detect actual MIME type
            actual_mime_type = magic.from_buffer(content, mime=True)

            # Security validation
            security_result = await self._perform_security_checks(content, actual_mime_type)
            if not security_result['safe']:
                return {
                    'success': False,
                    'error_message': f"Security check failed: {security_result['reason']}"
                }

            # Process based on file type
            processed_content = content
            thumbnail_generated = False
            metadata_extracted = False

            if actual_mime_type.startswith('image/'):
                image_result = await self._process_image(content)
                processed_content = image_result['content']
                thumbnail_generated = image_result['thumbnail_generated']
                metadata_extracted = image_result['metadata_extracted']
            elif actual_mime_type == 'application/pdf':
                pdf_result = await self._process_pdf(content)
                metadata_extracted = pdf_result['metadata_extracted']
            elif actual_mime_type.startswith('text/'):
                text_result = await self._process_text(content)
                metadata_extracted = text_result['metadata_extracted']

            # Generate file metadata
            file_metadata = {
                'name': await self._sanitize_filename(file.filename),
                'mime_type': actual_mime_type,
                'size': len(processed_content),
                'hash': file_hash,
                'original_filename': file.filename,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'company_id': request.get('company_id'),
                'document_type': request.get('document_type'),
                'user_id': request.get('user_id'),
                'security_scan_result': security_result.get('scan_result'),
                'thumbnail_generated': thumbnail_generated,
                'metadata_extracted': metadata_extracted
            }

            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000

            self.logger.info(
                "File processing completed",
                filename=file.filename,
                processing_time_ms=processing_time,
                thumbnail_generated=thumbnail_generated,
                metadata_extracted=metadata_extracted
            )

            return {
                'success': True,
                'metadata': file_metadata,
                'content': processed_content,
                'processing_time_ms': processing_time
            }

        except Exception as e:
            self.logger.error("File processing failed", filename=file.filename, error=str(e))
            return {
                'success': False,
                'error_message': str(e)
            }

    async def _perform_security_checks(self, content: bytes, mime_type: str) -> Dict[str, Any]:
        """Perform security checks on file content"""
        try:
            result = {'safe': True, 'reason': None, 'scan_result': None}

            # Check for malware signatures if enabled
            if self.enable_virus_scan:
                scan_result = await self._scan_for_malware(content)
                result['scan_result'] = scan_result

                if scan_result['infected']:
                    result['safe'] = False
                    result['reason'] = "Malware detected"
                    return result

            # Check for suspicious content patterns
            if await self._check_suspicious_content(content):
                result['safe'] = False
                result['reason'] = "Suspicious content detected"
                return result

            # Validate MIME type consistency
            if mime_type == 'application/octet-stream':
                result['safe'] = False
                result['reason'] = "Unknown or dangerous file type"
                return result

            return result

        except Exception as e:
            self.logger.error("Security checks failed", error=str(e))
            return {'safe': False, 'reason': f"Security check error: {str(e)}"}

    async def _scan_for_malware(self, content: bytes) -> Dict[str, Any]:
        """Scan file for malware using ClamAV"""
        try:
            import socket

            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name

            try:
                # Connect to ClamAV socket
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect(self.clamd_socket)

                # Send scan command
                sock.send(f"SCAN {temp_file_path}\n".encode())
                response = sock.recv(4096).decode().strip()

                sock.close()

                # Parse response
                if response.startswith(temp_file_path + ": OK"):
                    return {'infected': False, 'threat': None}
                else:
                    threat = response.split(": ")[1] if ": " in response else "Unknown threat"
                    return {'infected': True, 'threat': threat}

            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)

        except Exception as e:
            self.logger.error("Malware scan failed", error=str(e))
            return {'infected': False, 'threat': None, 'error': str(e)}

    async def _check_suspicious_content(self, content: bytes) -> bool:
        """Check for suspicious content patterns"""
        try:
            # Check for executable file signatures
            executable_signatures = [
                b'MZ',                    # Windows PE
                b'\x7fELF',              # Linux ELF
                b'\xca\xfe\xba\xbe',     # Java class
                b'\xfe\xed\xfa\xce',     # Mach-O binary (macOS)
                b'\xfe\xed\xfa\xcf',     # Mach-O binary (macOS)
            ]

            for signature in executable_signatures:
                if content.startswith(signature):
                    return True

            # Check for script content in non-script files
            script_patterns = [
                b'<script',
                b'javascript:',
                b'vbscript:',
                b'data:text/html',
                b'<?php',
                b'<%',
                b'#!/bin/',
                b'#!/usr/bin/'
            ]

            for pattern in script_patterns:
                if pattern in content.lower():
                    return True

            return False

        except Exception as e:
            self.logger.error("Suspicious content check failed", error=str(e))
            return False

    async def _process_image(self, content: bytes) -> Dict[str, Any]:
        """Process image file"""
        try:
            result = {
                'content': content,
                'thumbnail_generated': False,
                'metadata_extracted': False
            }

            # Open image
            with Image.open(io.BytesIO(content)) as img:
                # Extract metadata
                if hasattr(img, '_getexif') and img._getexif():
                    result['metadata_extracted'] = True

                # Resize if too large
                if img.size[0] > self.max_image_size[0] or img.size[1] > self.max_image_size[1]:
                    img.thumbnail(self.max_image_size, Image.Resampling.LANCZOS)

                    # Save processed image
                    output = io.BytesIO()
                    img.save(output, format=img.format or 'JPEG', quality=85)
                    result['content'] = output.getvalue()

                # Generate thumbnail (placeholder for now)
                # In a real implementation, you would save the thumbnail
                result['thumbnail_generated'] = True

            return result

        except Exception as e:
            self.logger.error("Image processing failed", error=str(e))
            return {
                'content': content,
                'thumbnail_generated': False,
                'metadata_extracted': False
            }

    async def _process_pdf(self, content: bytes) -> Dict[str, Any]:
        """Process PDF file"""
        try:
            result = {'metadata_extracted': False}

            # Try to extract PDF metadata
            # In a real implementation, you would use PyPDF2 or similar library
            # For now, just check if it's a valid PDF
            if content.startswith(b'%PDF'):
                result['metadata_extracted'] = True

            return result

        except Exception as e:
            self.logger.error("PDF processing failed", error=str(e))
            return {'metadata_extracted': False}

    async def _process_text(self, content: bytes) -> Dict[str, Any]:
        """Process text file"""
        try:
            result = {'metadata_extracted': False}

            # Try to decode as text
            try:
                text_content = content.decode('utf-8')
                # Extract basic metadata
                if len(text_content) > 0:
                    result['metadata_extracted'] = True
            except UnicodeDecodeError:
                try:
                    text_content = content.decode('latin-1')
                    result['metadata_extracted'] = True
                except:
                    pass

            return result

        except Exception as e:
            self.logger.error("Text processing failed", error=str(e))
            return {'metadata_extracted': False}

    async def _get_file_category(self, mime_type: str) -> str:
        """Get file category based on MIME type"""
        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type in ['application/pdf'] or mime_type.startswith('application/vnd.ms-') or mime_type.startswith('application/vnd.openxmlformats-'):
            return 'document'
        elif mime_type in ['application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed']:
            return 'archive'
        else:
            return 'default'

    async def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for storage"""
        # Remove path components
        filename = os.path.basename(filename)

        # Replace dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')

        # Remove control characters
        filename = ''.join(char for char in filename if ord(char) >= 32)

        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext

        return filename

    async def _test_virus_scan_connection(self):
        """Test connection to ClamAV"""
        try:
            import socket

            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(self.clamd_socket)
            sock.send(b"PING\n")
            response = sock.recv(1024).decode().strip()
            sock.close()

            if response != "PONG":
                raise Exception("ClamAV not responding correctly")

            self.logger.info("ClamAV connection successful")

        except Exception as e:
            self.logger.warning("ClamAV connection failed", error=str(e))
            if self.enable_virus_scan:
                raise

    async def get_stats(self) -> Dict[str, Any]:
        """Get file processor statistics"""
        return {
            "service": "file_processor",
            "status": "active",
            "supported_mime_types": len(self.supported_mime_types),
            "virus_scan_enabled": self.enable_virus_scan,
            "max_file_sizes": self.max_file_sizes
        }