"""
Security module for the AI Legal Document Automation System
"""

from .auth import (
    AuthenticationService,
    PermissionManager,
    Token,
    TokenData,
    AuthUser,
    UserCreate,
    UserLogin,
    PasswordReset,
    auth_service,
    permission_manager,
)
from .encryption import (
    EncryptionService,
    DataMaskingService,
    encryption_service,
    data_masking_service,
)
from .rbac import (
    RBACManager,
    Permission,
    Role,
    RoleDefinition,
    Resource,
    AccessRequest,
    AccessResult,
    rbac_manager,
)

__all__ = [
    "AuthenticationService",
    "PermissionManager",
    "Token",
    "TokenData",
    "AuthUser",
    "UserCreate",
    "UserLogin",
    "PasswordReset",
    "auth_service",
    "permission_manager",
    "EncryptionService",
    "DataMaskingService",
    "encryption_service",
    "data_masking_service",
    "RBACManager",
    "Permission",
    "Role",
    "RoleDefinition",
    "Resource",
    "AccessRequest",
    "AccessResult",
    "rbac_manager",
]