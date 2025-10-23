"""
Role-Based Access Control (RBAC) implementation
"""

import os
import enum
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()


class Permission(enum.Enum):
    """System permissions enumeration"""

    # User management
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"

    # Company management
    COMPANY_READ = "company:read"
    COMPANY_WRITE = "company:write"
    COMPANY_DELETE = "company:delete"

    # Document management
    DOCUMENT_READ = "document:read"
    DOCUMENT_WRITE = "document:write"
    DOCUMENT_DELETE = "document:delete"
    DOCUMENT_UPLOAD = "document:upload"
    DOCUMENT_DOWNLOAD = "document:download"

    # Processing management
    PROCESSING_READ = "processing:read"
    PROCESSING_WRITE = "processing:write"
    PROCESSING_CONTROL = "processing:control"

    # Notification management
    NOTIFICATION_READ = "notification:read"
    NOTIFICATION_WRITE = "notification:write"
    NOTIFICATION_SEND = "notification:send"

    # System administration
    SYSTEM_READ = "system:read"
    SYSTEM_WRITE = "system:write"
    SYSTEM_CONFIG = "system:config"

    # Audit and compliance
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"
    COMPLIANCE_READ = "compliance:read"
    COMPLIANCE_WRITE = "compliance:write"

    # API management
    API_READ = "api:read"
    API_WRITE = "api:write"
    API_DELETE = "api:delete"


class Role(enum.Enum):
    """User roles enumeration"""

    ADMIN = "admin"
    LEGAL_ADMIN = "legal_admin"
    COMPANY_ADMIN = "company_admin"
    COMPANY_USER = "company_user"
    VIEWER = "viewer"


@dataclass
class RoleDefinition:
    """Role definition with permissions and scope"""
    name: str
    permissions: Set[Permission]
    description: str
    is_system_role: bool = True
    max_companies: Optional[int] = None


class Resource(BaseModel):
    """Resource model for access control"""
    id: str
    type: str
    owner_id: Optional[int] = None
    company_id: Optional[int] = None
    metadata: Dict[str, Any] = {}


class AccessRequest(BaseModel):
    """Access request model"""
    user_id: int
    resource: Resource
    required_permission: Permission
    context: Dict[str, Any] = {}


class AccessResult(BaseModel):
    """Access control result"""
    granted: bool
    reason: str
    conditions: List[str] = []


class RBACManager:
    """Role-Based Access Control Manager"""

    def __init__(self):
        self.logger = structlog.get_logger().bind(component="RBACManager")

        # Define role permissions
        self.role_definitions = self._initialize_roles()

        # Cache for user permissions (in production, use Redis)
        self.user_permissions_cache: Dict[int, Set[Permission]] = {}

    def _initialize_roles(self) -> Dict[Role, RoleDefinition]:
        """Initialize role definitions"""
        return {
            Role.ADMIN: RoleDefinition(
                name=Role.ADMIN.value,
                permissions=set(Permission),  # All permissions
                description="System administrator with full access",
                is_system_role=True
            ),

            Role.LEGAL_ADMIN: RoleDefinition(
                name=Role.LEGAL_ADMIN.value,
                permissions={
                    Permission.USER_READ, Permission.USER_WRITE,
                    Permission.COMPANY_READ, Permission.COMPANY_WRITE,
                    Permission.DOCUMENT_READ, Permission.DOCUMENT_WRITE, Permission.DOCUMENT_DELETE,
                    Permission.PROCESSING_READ, Permission.PROCESSING_WRITE, Permission.PROCESSING_CONTROL,
                    Permission.NOTIFICATION_READ, Permission.NOTIFICATION_WRITE, Permission.NOTIFICATION_SEND,
                    Permission.AUDIT_READ, Permission.AUDIT_EXPORT,
                    Permission.COMPLIANCE_READ, Permission.COMPLIANCE_WRITE,
                    Permission.SYSTEM_READ
                },
                description="Legal administrator with company and document management access",
                is_system_role=True
            ),

            Role.COMPANY_ADMIN: RoleDefinition(
                name=Role.COMPANY_ADMIN.value,
                permissions={
                    Permission.USER_READ, Permission.USER_WRITE,
                    Permission.COMPANY_READ,
                    Permission.DOCUMENT_READ, Permission.DOCUMENT_WRITE, Permission.DOCUMENT_DELETE,
                    Permission.DOCUMENT_UPLOAD, Permission.DOCUMENT_DOWNLOAD,
                    Permission.PROCESSING_READ, Permission.PROCESSING_WRITE,
                    Permission.NOTIFICATION_READ, Permission.NOTIFICATION_WRITE, Permission.NOTIFICATION_SEND,
                    Permission.AUDIT_READ,
                    Permission.COMPLIANCE_READ
                },
                description="Company administrator with full company access",
                is_system_role=False,
                max_companies=1
            ),

            Role.COMPANY_USER: RoleDefinition(
                name=Role.COMPANY_USER.value,
                permissions={
                    Permission.DOCUMENT_READ, Permission.DOCUMENT_WRITE,
                    Permission.DOCUMENT_UPLOAD, Permission.DOCUMENT_DOWNLOAD,
                    Permission.PROCESSING_READ,
                    Permission.NOTIFICATION_READ,
                    Permission.AUDIT_READ,
                    Permission.COMPLIANCE_READ
                },
                description="Company user with basic document access",
                is_system_role=False,
                max_companies=1
            ),

            Role.VIEWER: RoleDefinition(
                name=Role.VIEWER.value,
                permissions={
                    Permission.DOCUMENT_READ,
                    Permission.NOTIFICATION_READ,
                    Permission.AUDIT_READ,
                    Permission.COMPLIANCE_READ
                },
                description="Read-only access to documents and notifications",
                is_system_role=False,
                max_companies=None
            )
        }

    def get_role_permissions(self, role: Role) -> Set[Permission]:
        """Get permissions for a role"""
        return self.role_definitions.get(role, RoleDefinition("", set(), "")).permissions

    def get_user_permissions(self, user_id: int, user_role: Role, user_permissions: List[str] = None) -> Set[Permission]:
        """Get all permissions for a user (role + custom permissions)"""
        # Check cache first
        if user_id in self.user_permissions_cache:
            return self.user_permissions_cache[user_id]

        # Get role permissions
        role_perms = self.get_role_permissions(user_role)

        # Add custom permissions if provided
        if user_permissions:
            try:
                custom_perms = {Permission(perm) for perm in user_permissions if perm in [p.value for p in Permission]}
                role_perms = role_perms.union(custom_perms)
            except ValueError as e:
                self.logger.warning("Invalid custom permissions", user_id=user_id, error=str(e))

        # Cache the result
        self.user_permissions_cache[user_id] = role_perms

        return role_perms

    def has_permission(self, user_id: int, user_role: Role, permission: Permission, user_permissions: List[str] = None) -> bool:
        """Check if user has a specific permission"""
        user_perms = self.get_user_permissions(user_id, user_role, user_permissions)
        return permission in user_perms

    def can_access_resource(
        self,
        user_id: int,
        user_role: Role,
        user_company_id: int,
        resource: Resource,
        required_permission: Permission,
        user_permissions: List[str] = None
    ) -> AccessResult:
        """Check if user can access a specific resource"""
        try:
            # Check basic permission
            if not self.has_permission(user_id, user_role, required_permission, user_permissions):
                return AccessResult(
                    granted=False,
                    reason=f"User lacks required permission: {required_permission.value}"
                )

            # System admins can access everything
            if user_role == Role.ADMIN:
                return AccessResult(
                    granted=True,
                    reason="System administrator has full access"
                )

            # Check company-based access control
            if resource.company_id:
                if user_role in [Role.LEGAL_ADMIN]:
                    # Legal admins can access all companies
                    return AccessResult(
                        granted=True,
                        reason="Legal administrator has cross-company access"
                    )
                elif user_role in [Role.COMPANY_ADMIN, Role.COMPANY_USER]:
                    # Company users can only access their own company
                    if resource.company_id != user_company_id:
                        return AccessResult(
                            granted=False,
                            reason=f"User cannot access company {resource.company_id}"
                        )
                elif user_role == Role.VIEWER:
                    # Viewers need explicit company assignment
                    if resource.company_id != user_company_id:
                        return AccessResult(
                            granted=False,
                            reason=f"Viewer cannot access company {resource.company_id}"
                        )

            # Check resource ownership (for user-specific resources)
            if resource.owner_id and resource.owner_id != user_id:
                if user_role not in [Role.ADMIN, Role.LEGAL_ADMIN]:
                    return AccessResult(
                        granted=False,
                        reason="User can only access their own resources"
                    )

            # Check resource type specific rules
            if resource.type == "user":
                return self._check_user_access(user_role, resource, required_permission)
            elif resource.type == "document":
                return self._check_document_access(user_role, resource, required_permission)
            elif resource.type == "company":
                return self._check_company_access(user_role, resource, required_permission)

            return AccessResult(
                granted=True,
                reason="Access granted"
            )

        except Exception as e:
            self.logger.error("Access check failed", error=str(e))
            return AccessResult(
                granted=False,
                reason="Access check failed due to system error"
            )

    def _check_user_access(self, user_role: Role, resource: Resource, required_permission: Permission) -> AccessResult:
        """Check user-specific access rules"""
        # Only admins and legal admins can manage other users
        if required_permission in [Permission.USER_WRITE, Permission.USER_DELETE]:
            if user_role not in [Role.ADMIN, Role.LEGAL_ADMIN]:
                return AccessResult(
                    granted=False,
                    reason="Only administrators can manage users"
                )

        # Company admins can only manage users in their company
        if user_role == Role.COMPANY_ADMIN and required_permission == Permission.USER_WRITE:
            if resource.company_id != resource.metadata.get("user_company_id"):
                return AccessResult(
                    granted=False,
                    reason="Company admin can only manage users in their company"
                )

        return AccessResult(granted=True, reason="User access granted")

    def _check_document_access(self, user_role: Role, resource: Resource, required_permission: Permission) -> AccessResult:
        """Check document-specific access rules"""
        # Viewers can only read documents
        if user_role == Role.VIEWER and required_permission != Permission.DOCUMENT_READ:
            return AccessResult(
                granted=False,
                reason="Viewers can only read documents"
            )

        # Company users need to belong to the same company as the document
        if user_role in [Role.COMPANY_ADMIN, Role.COMPANY_USER]:
            if resource.company_id != resource.metadata.get("user_company_id"):
                return AccessResult(
                    granted=False,
                    reason="User can only access documents from their company"
                )

        return AccessResult(granted=True, reason="Document access granted")

    def _check_company_access(self, user_role: Role, resource: Resource, required_permission: Permission) -> AccessResult:
        """Check company-specific access rules"""
        # Only admins and legal admins can delete companies
        if required_permission == Permission.COMPANY_DELETE:
            if user_role not in [Role.ADMIN, Role.LEGAL_ADMIN]:
                return AccessResult(
                    granted=False,
                    reason="Only administrators can delete companies"
                )

        # Company admins can only manage their own company
        if user_role == Role.COMPANY_ADMIN:
            if resource.id != str(resource.metadata.get("user_company_id")):
                return AccessResult(
                    granted=False,
                    reason="Company admin can only manage their own company"
                )

        return AccessResult(granted=True, reason="Company access granted")

    def create_custom_role(self, name: str, permissions: List[Permission], description: str) -> bool:
        """Create a custom role (for future implementation)"""
        try:
            # This would be implemented with database storage
            self.logger.info("Custom role creation requested", name=name, permissions=len(permissions))
            return True
        except Exception as e:
            self.logger.error("Custom role creation failed", error=str(e))
            return False

    def update_user_permissions(self, user_id: int, permissions: List[Permission]) -> bool:
        """Update user's custom permissions"""
        try:
            # Update cache
            if user_id in self.user_permissions_cache:
                del self.user_permissions_cache[user_id]

            self.logger.info("User permissions updated", user_id=user_id, permissions=len(permissions))
            return True
        except Exception as e:
            self.logger.error("User permission update failed", user_id=user_id, error=str(e))
            return False

    def clear_user_cache(self, user_id: int):
        """Clear cached permissions for a user"""
        if user_id in self.user_permissions_cache:
            del self.user_permissions_cache[user_id]
            self.logger.info("User permission cache cleared", user_id=user_id)

    def get_role_hierarchy(self) -> Dict[str, int]:
        """Get role hierarchy levels (higher number = more privileged)"""
        return {
            Role.VIEWER.value: 1,
            Role.COMPANY_USER.value: 2,
            Role.COMPANY_ADMIN.value: 3,
            Role.LEGAL_ADMIN.value: 4,
            Role.ADMIN.value: 5
        }

    def can_manage_role(self, manager_role: Role, target_role: Role) -> bool:
        """Check if a user with manager_role can manage users with target_role"""
        hierarchy = self.get_role_hierarchy()
        return hierarchy.get(manager_role.value, 0) > hierarchy.get(target_role.value, 0)


# Global RBAC manager instance
rbac_manager = RBACManager()