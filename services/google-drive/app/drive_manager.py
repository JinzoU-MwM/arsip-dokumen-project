"""
Google Drive Manager
Handles interaction with Google Drive API
"""

import asyncio
import os
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import io

from .models import (
    FileMetadata,
    FolderRequest,
    FolderResponse,
    SearchRequest,
    SearchResponse,
    ShareRequest,
    ShareResponse,
    CompanyFolderStructure,
    DocumentType,
    ShareRole
)


class DriveManager:
    """Service for managing Google Drive operations"""

    def __init__(self):
        self.logger = structlog.get_logger().bind(component="DriveManager")
        self.service = None
        self.credentials = None

        # Google Drive API configuration
        self.scopes = ['https://www.googleapis.com/auth/drive']
        self.service_account_key = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY_PATH')
        self.client_secrets_file = os.getenv('GOOGLE_CLIENT_SECRETS_FILE')
        self.credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'token.json')

        # Folder naming conventions
        self.folder_structure = {
            "root": "Legal Documents",
            "document_types": {
                DocumentType.KTP: "KTP",
                DocumentType.KK: "Kartu Keluarga",
                DocumentType.AKTA_KELAHIRAN: "Akta Kelahiran",
                DocumentType.AKTA_KEMATIAN: "Akta Kematian",
                DocumentType.AKTA_PERNIKAHAN: "Akta Pernikahan",
                DocumentType.AKTA_PERCERAIAN: "Akta Perceraian",
                DocumentType.IZIN_LOKASI: "Izin Lokasi",
                DocumentType.SURAT_KEPEMILIKAN_TANAH: "Surat Kepemilikan Tanah",
                DocumentType.NPWP: "NPWP",
                DocumentType.SIUP: "SIUP",
                DocumentType.TDP: "TDP",
                DocumentType.LAINNYA: "Lainnya"
            },
            "special_folders": {
                "archive": "Archive",
                "temp": "Temporary",
                "processing": "Processing"
            }
        }

    async def initialize(self):
        """Initialize the Drive manager"""
        self.logger.info("Initializing Drive Manager")

        try:
            # Authenticate and build service
            await self._authenticate()
            self.service = build('drive', 'v3', credentials=self.credentials)

            # Test connection
            about = self.service.about().get(fields="user").execute()
            self.logger.info("Drive Manager initialized", user=about.get('user', {}).get('emailAddress'))

        except Exception as e:
            self.logger.error("Failed to initialize Drive Manager", error=str(e))
            raise

    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up Drive Manager")
        if self.service:
            self.service.close()

    async def _authenticate(self):
        """Authenticate with Google Drive API"""
        try:
            creds = None

            # Try to load existing credentials
            if os.path.exists(self.credentials_path):
                creds = Credentials.from_authorized_user_file(self.credentials_path, self.scopes)

            # If credentials are invalid or missing, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                elif self.service_account_key:
                    # Use service account
                    from google.oauth2 import service_account
                    creds = service_account.Credentials.from_service_account_file(
                        self.service_account_key, scopes=self.scopes
                    )
                else:
                    # Use OAuth flow
                    flow = Flow.from_client_secrets_file(
                        self.client_secrets_file,
                        scopes=self.scopes,
                        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                    )

                    auth_url, _ = flow.authorization_url(prompt='consent')
                    self.logger.info("Please visit this URL to authorize the application: %s", auth_url)

                    # For automated environments, you might want to handle this differently
                    code = input("Enter the authorization code: ")
                    flow.fetch_token(code=code)
                    creds = flow.credentials

                # Save credentials for future use
                if self.client_secrets_file:  # Only save for OAuth, not service accounts
                    with open(self.credentials_path, 'w') as token:
                        token.write(creds.to_json())

            self.credentials = creds

        except Exception as e:
            self.logger.error("Authentication failed", error=str(e))
            raise

    async def upload_file(self, processed_file: Dict[str, Any], request: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a file to Google Drive"""
        try:
            file_metadata = processed_file['metadata']
            file_content = processed_file['content']

            # Determine folder
            folder_id = request.get('folder_id')
            if not folder_id:
                # Create or get company folder
                company_folder = await self.get_or_create_company_folder(request['company_id'])
                document_type_folder = await self.get_or_create_document_type_folder(
                    company_folder['id'],
                    request['document_type']
                )
                folder_id = document_type_folder['id']

            # Prepare file metadata
            drive_metadata = {
                'name': file_metadata['name'],
                'parents': [folder_id] if folder_id else None
            }

            if request.get('description'):
                drive_metadata['description'] = request['description']

            # Add custom properties
            properties = {
                'company_id': str(request['company_id']),
                'document_type': request['document_type'],
                'uploaded_at': datetime.utcnow().isoformat()
            }

            if request.get('user_id'):
                properties['user_id'] = str(request['user_id'])

            if request.get('tags'):
                properties['tags'] = ','.join(request['tags'])

            drive_metadata['properties'] = properties

            # Upload file
            media = MediaIoBaseUpload(
                io.BytesIO(file_content),
                mimetype=file_metadata['mime_type'],
                resumable=True
            )

            file = self.service.files().create(
                body=drive_metadata,
                media_body=media,
                fields='id,name,size,mimeType,createdTime,modifiedTime,parents,webViewLink,webContentLink,thumbnailLink'
            ).execute()

            # Convert to our metadata format
            response_metadata = await self._convert_drive_metadata(file, request)

            return {
                'success': True,
                'file_id': file['id'],
                'filename': file_metadata['name'],
                'drive_url': file['webViewLink'],
                'file_metadata': response_metadata,
                'folder_id': folder_id
            }

        except Exception as e:
            self.logger.error("File upload failed", error=str(e))
            return {
                'success': False,
                'error_message': str(e)
            }

    async def create_folder(self, request: FolderRequest) -> FolderResponse:
        """Create a folder in Google Drive"""
        try:
            folder_metadata = {
                'name': request.folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'properties': {
                    'company_id': str(request.company_id),
                    'folder_type': 'company_folder',
                    'created_at': datetime.utcnow().isoformat()
                }
            }

            if request.parent_folder_id:
                folder_metadata['parents'] = [request.parent_folder_id]

            if request.description:
                folder_metadata['description'] = request.description

            folder = self.service.files().create(
                body=folder_metadata,
                fields='id,name,createdTime,webViewLink'
            ).execute()

            # Create subfolders if requested
            subfolder_ids = []
            if request.create_structure:
                subfolder_ids = await self._create_standard_subfolders(folder['id'], request.company_id)

            return FolderResponse(
                success=True,
                folder_id=folder['id'],
                folder_name=folder['name'],
                drive_url=folder['webViewLink'],
                parent_folder_id=request.parent_folder_id,
                created_subfolders=subfolder_ids
            )

        except Exception as e:
            self.logger.error("Folder creation failed", error=str(e))
            return FolderResponse(
                success=False,
                folder_id="",
                folder_name=request.folder_name,
                drive_url="",
                error_message=str(e)
            )

    async def list_folder_files(self, folder_id: str) -> List[FileMetadata]:
        """List files in a folder"""
        try:
            query = f"'{folder_id}' in parents and trashed=false"

            results = self.service.files().list(
                q=query,
                fields="files(id,name,mimeType,size,createdTime,modifiedTime,parents,webViewLink,webContentLink,description,properties)"
            ).execute()

            files = results.get('files', [])
            return [await self._convert_drive_metadata(file) for file in files]

        except Exception as e:
            self.logger.error("Failed to list folder files", error=str(e))
            raise

    async def search_files(self, request: SearchRequest) -> SearchResponse:
        """Search for files in Google Drive"""
        try:
            # Build query
            query_parts = []

            # Add name search
            query_parts.append(f"name contains '{request.query}'")

            # Add filters
            if request.company_id:
                query_parts.append("properties has { key='company_id' and value='%s' }" % request.company_id)

            if request.document_type:
                query_parts.append("properties has { key='document_type' and value='%s' }" % request.document_type)

            if request.folder_id:
                query_parts.append(f"'{request.folder_id}' in parents")

            # Date filters
            if request.created_after:
                date_str = request.created_after.isoformat() + 'Z'
                query_parts.append(f"createdTime >= '{date_str}'")

            if request.created_before:
                date_str = request.created_before.isoformat() + 'Z'
                query_parts.append(f"createdTime <= '{date_str}'")

            # File type filters
            if request.file_types:
                mime_query = " or ".join([f"mimeType = '{mt}'" for mt in request.file_types])
                query_parts.append(f"({mime_query})")

            # Combine all parts
            query = " and ".join(query_parts) + " and trashed=false"

            # Execute search
            results = self.service.files().list(
                q=query,
                pageSize=request.max_results,
                pageToken=request.page_token,
                fields="files(id,name,mimeType,size,createdTime,modifiedTime,parents,webViewLink,webContentLink,description,properties),nextPageToken"
            ).execute()

            files = results.get('files', [])
            next_page_token = results.get('nextPageToken')

            # Convert to our format
            file_metadata_list = [await self._convert_drive_metadata(file) for file in files]

            return SearchResponse(
                success=True,
                files=file_metadata_list,
                total_count=len(file_metadata_list),
                query=request.query,
                next_page_token=next_page_token,
                search_applied_filters={
                    "company_id": request.company_id,
                    "document_type": request.document_type,
                    "folder_id": request.folder_id,
                    "created_after": request.created_after,
                    "created_before": request.created_before,
                    "file_types": request.file_types
                }
            )

        except Exception as e:
            self.logger.error("File search failed", error=str(e))
            raise

    async def get_file_metadata(self, file_id: str) -> FileMetadata:
        """Get file metadata"""
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields="id,name,mimeType,size,createdTime,modifiedTime,parents,webViewLink,webContentLink,description,properties"
            ).execute()

            return await self._convert_drive_metadata(file)

        except Exception as e:
            self.logger.error("Failed to get file metadata", error=str(e))
            raise

    async def download_file(self, file_id: str):
        """Download file content"""
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_io = io.BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)

            done = False
            while done is False:
                status, done = downloader.next_chunk()

            file_io.seek(0)
            return file_io

        except Exception as e:
            self.logger.error("File download failed", error=str(e))
            raise

    async def delete_file(self, file_id: str) -> bool:
        """Delete a file"""
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True

        except Exception as e:
            self.logger.error("File deletion failed", error=str(e))
            return False

    async def share_file(self, file_id: str, request: ShareRequest) -> ShareResponse:
        """Share a file with specified user"""
        try:
            # Create permission
            permission = {
                'type': 'user',
                'role': request.role.value,
                'emailAddress': request.email
            }

            if request.role == ShareRole.OWNER:
                # For owner role, we need to use transferOwnership
                permission['transferOwnership'] = True

            result = self.service.permissions().create(
                fileId=file_id,
                body=permission,
                emailMessage=request.message,
                sendNotificationEmail=request.send_notification_email,
                fields='id,emailAddress,role,type,displayName,photoLink,expirationTime'
            ).execute()

            # Generate share URL
            share_url = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

            return ShareResponse(
                success=True,
                file_id=file_id,
                email=request.email,
                role=request.role,
                share_id=result.get('id'),
                share_url=share_url,
                expiration_date=datetime.fromisoformat(result['expirationTime']) if result.get('expirationTime') else None
            )

        except Exception as e:
            self.logger.error("File sharing failed", error=str(e))
            return ShareResponse(
                success=False,
                file_id=file_id,
                email=request.email,
                role=request.role,
                error_message=str(e)
            )

    async def create_company_folder_structure(self, company_id: int) -> Dict[str, Any]:
        """Create standardized folder structure for a company"""
        try:
            # Create root folder
            root_folder_name = f"{self.folder_structure['root']} - Company {company_id}"
            root_request = FolderRequest(
                company_id=company_id,
                folder_name=root_folder_name,
                create_structure=True
            )
            root_folder = await self.create_folder(root_request)

            if not root_folder.success:
                raise Exception("Failed to create root folder")

            # Create document type folders
            document_folders = {}
            for doc_type, folder_name in self.folder_structure['document_types'].items():
                folder_request = FolderRequest(
                    company_id=company_id,
                    folder_name=folder_name,
                    parent_folder_id=root_folder.folder_id
                )
                folder_response = await self.create_folder(folder_request)
                if folder_response.success:
                    document_folders[doc_type.value] = folder_response.folder_id

            # Create special folders
            special_folders = {}
            for folder_type, folder_name in self.folder_structure['special_folders'].items():
                folder_request = FolderRequest(
                    company_id=company_id,
                    folder_name=folder_name,
                    parent_folder_id=root_folder.folder_id
                )
                folder_response = await self.create_folder(folder_request)
                if folder_response.success:
                    special_folders[folder_type] = folder_response.folder_id

            structure = CompanyFolderStructure(
                company_id=company_id,
                root_folder_id=root_folder.folder_id,
                root_folder_name=root_folder_name,
                document_folders=document_folders,
                archive_folder_id=special_folders.get('archive'),
                temp_folder_id=special_folders.get('temp'),
                drive_url=root_folder.drive_url
            )

            return structure.dict()

        except Exception as e:
            self.logger.error("Failed to create company folder structure", error=str(e))
            raise

    async def get_or_create_company_folder(self, company_id: int) -> Dict[str, Any]:
        """Get or create company root folder"""
        try:
            # Search for existing company folder
            search_request = SearchRequest(
                query=f"Legal Documents - Company {company_id}",
                company_id=company_id
            )

            search_response = await self.search_files(search_request)

            if search_response.files and search_response.files[0].mime_type == 'application/vnd.google-apps.folder':
                return {'id': search_response.files[0].id, 'name': search_response.files[0].name}

            # Create new folder structure
            structure = await self.create_company_folder_structure(company_id)
            return {
                'id': structure['root_folder_id'],
                'name': structure['root_folder_name']
            }

        except Exception as e:
            self.logger.error("Failed to get or create company folder", error=str(e))
            raise

    async def get_or_create_document_type_folder(self, company_folder_id: str, document_type: DocumentType) -> Dict[str, Any]:
        """Get or create document type folder within company folder"""
        try:
            folder_name = self.folder_structure['document_types'].get(document_type, 'Lainnya')

            # Search for existing folder
            search_query = f"name = '{folder_name}' and '{company_folder_id}' in parents"
            results = self.service.files().list(
                q=search_query,
                fields="files(id,name)"
            ).execute()

            files = results.get('files', [])
            if files:
                return {'id': files[0]['id'], 'name': files[0]['name']}

            # Create new folder
            folder_request = FolderRequest(
                company_id=0,  # Not used for subfolders
                folder_name=folder_name,
                parent_folder_id=company_folder_id
            )
            folder_response = await self.create_folder(folder_request)

            if folder_response.success:
                return {'id': folder_response.folder_id, 'name': folder_response.folder_name}

            raise Exception("Failed to create document type folder")

        except Exception as e:
            self.logger.error("Failed to get or create document type folder", error=str(e))
            raise

    async def _convert_drive_metadata(self, drive_file: Dict[str, Any], request: Dict[str, Any] = None) -> FileMetadata:
        """Convert Google Drive metadata to our format"""
        properties = drive_file.get('properties', {})

        return FileMetadata(
            id=drive_file['id'],
            name=drive_file['name'],
            mime_type=drive_file['mimeType'],
            size=int(drive_file.get('size', 0)),
            created_time=datetime.fromisoformat(drive_file['createdTime'].replace('Z', '+00:00')),
            modified_time=datetime.fromisoformat(drive_file['modifiedTime'].replace('Z', '+00:00')),
            parents=drive_file.get('parents', []),
            drive_url=drive_file['webViewLink'],
            thumbnail_link=drive_file.get('thumbnailLink'),
            web_view_link=drive_file['webViewLink'],
            web_content_link=drive_file.get('webContentLink'),
            description=drive_file.get('description'),
            tags=properties.get('tags', '').split(',') if properties.get('tags') else [],
            properties=properties,
            company_id=int(properties.get('company_id')) if properties.get('company_id') else None,
            document_type=DocumentType(properties.get('document_type')) if properties.get('document_type') else None,
            user_id=int(properties.get('user_id')) if properties.get('user_id') else None
        )

    async def _create_standard_subfolders(self, parent_folder_id: str, company_id: int) -> List[str]:
        """Create standard subfolders"""
        subfolder_ids = []
        for folder_name in self.folder_structure['special_folders'].values():
            folder_request = FolderRequest(
                company_id=company_id,
                folder_name=folder_name,
                parent_folder_id=parent_folder_id
            )
            folder_response = await self.create_folder(folder_request)
            if folder_response.success:
                subfolder_ids.append(folder_response.folder_id)

        return subfolder_ids

    async def get_stats(self) -> Dict[str, Any]:
        """Get Drive manager statistics"""
        return {
            "service": "drive_manager",
            "status": "active",
            "folder_structure_types": len(self.folder_structure['document_types']),
            "supported_operations": ["upload", "download", "search", "share", "folder_management"]
        }