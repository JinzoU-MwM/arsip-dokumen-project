"""
Authentication and authorization framework for the AI Legal Document Automation System
"""

import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from passlib.context import CryptContext
from passlib.hash import bcrypt
import structlog
from pydantic import BaseModel, EmailStr

logger = structlog.get_logger()

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Token data model"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None
    company_id: Optional[int] = None
    permissions: List[str] = []


class Token(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthUser(BaseModel):
    """User model for authentication"""
    id: int
    email: EmailStr
    username: str
    full_name: str
    role: str
    company_id: Optional[int] = None
    permissions: List[str] = []
    is_active: bool = True


class UserCreate(BaseModel):
    """User creation model"""
    email: EmailStr
    username: str
    full_name: str
    password: str
    role: str = "company_user"
    company_id: Optional[int] = None
    phone_number: Optional[str] = None


class UserLogin(BaseModel):
    """User login model"""
    username: str
    password: str


class PasswordReset(BaseModel):
    """Password reset model"""
    email: EmailStr
    new_password: str
    reset_token: str


class AuthenticationService:
    """Authentication service for handling user authentication and authorization"""

    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM
        self.access_token_expire_minutes = JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = JWT_REFRESH_TOKEN_EXPIRE_DAYS
        self.logger = structlog.get_logger().bind(component="AuthenticationService")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            self.logger.error("Password verification error", error=str(e))
            return False

    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        try:
            return pwd_context.hash(password)
        except Exception as e:
            self.logger.error("Password hashing error", error=str(e))
            raise

    def generate_salt(self) -> str:
        """Generate a random salt"""
        return secrets.token_hex(16)

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.access_token_expire_minutes
            )

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        self.logger.info("Access token created", user_id=data.get("sub"))
        return encoded_jwt

    def create_refresh_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=self.refresh_token_expire_days
            )

        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        self.logger.info("Refresh token created", user_id=data.get("sub"))
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            user_id: int = payload.get("sub")
            username: str = payload.get("username")
            role: str = payload.get("role")
            company_id: int = payload.get("company_id")
            permissions: List[str] = payload.get("permissions", [])
            token_type: str = payload.get("type")

            if user_id is None:
                return None

            token_data = TokenData(
                username=username,
                user_id=user_id,
                role=role,
                company_id=company_id,
                permissions=permissions
            )

            return token_data

        except jwt.ExpiredSignatureError:
            self.logger.warning("Token expired")
            return None
        except jwt.JWTError as e:
            self.logger.warning("Invalid token", error=str(e))
            return None

    def authenticate_user(self, username: str, password: str, user_data: Dict[str, Any]) -> Optional[AuthUser]:
        """Authenticate user with username and password"""
        try:
            if not self.verify_password(password, user_data.get("password_hash", "")):
                return None

            user = AuthUser(
                id=user_data["id"],
                email=user_data["email"],
                username=user_data["username"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                company_id=user_data.get("company_id"),
                permissions=user_data.get("permissions", []),
                is_active=user_data.get("status") == "active"
            )

            self.logger.info("User authenticated successfully", username=username)
            return user

        except Exception as e:
            self.logger.error("User authentication failed", username=username, error=str(e))
            return None

    def create_tokens_for_user(self, user: AuthUser) -> Token:
        """Create access and refresh tokens for user"""
        try:
            # Prepare token data
            token_data = {
                "sub": str(user.id),
                "username": user.username,
                "role": user.role,
                "company_id": user.company_id,
                "permissions": user.permissions
            }

            # Create tokens
            access_token = self.create_access_token(token_data)
            refresh_token = self.create_refresh_token(token_data)

            # Calculate expiration time in seconds
            expires_in = self.access_token_expire_minutes * 60

            self.logger.info("Tokens created for user", user_id=user.id, role=user.role)

            return Token(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=expires_in
            )

        except Exception as e:
            self.logger.error("Token creation failed", user_id=user.id, error=str(e))
            raise

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Create new access token from refresh token"""
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])

            # Verify it's a refresh token
            if payload.get("type") != "refresh":
                return None

            # Create new access token
            token_data = {
                "sub": payload.get("sub"),
                "username": payload.get("username"),
                "role": payload.get("role"),
                "company_id": payload.get("company_id"),
                "permissions": payload.get("permissions", [])
            }

            new_access_token = self.create_access_token(token_data)

            self.logger.info("Access token refreshed", user_id=payload.get("sub"))
            return new_access_token

        except jwt.ExpiredSignatureError:
            self.logger.warning("Refresh token expired")
            return None
        except jwt.JWTError as e:
            self.logger.warning("Invalid refresh token", error=str(e))
            return None

    def generate_password_reset_token(self, email: str) -> str:
        """Generate password reset token"""
        try:
            expires_delta = timedelta(hours=1)  # Reset token expires in 1 hour
            token_data = {"email": email, "type": "password_reset"}
            reset_token = self.create_access_token(token_data, expires_delta)

            self.logger.info("Password reset token generated", email=email)
            return reset_token

        except Exception as e:
            self.logger.error("Password reset token generation failed", email=email, error=str(e))
            raise

    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """Verify password reset token and return email"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            if payload.get("type") != "password_reset":
                return None

            email = payload.get("email")
            if not email:
                return None

            self.logger.info("Password reset token verified", email=email)
            return email

        except jwt.ExpiredSignatureError:
            self.logger.warning("Password reset token expired")
            return None
        except jwt.JWTError as e:
            self.logger.warning("Invalid password reset token", error=str(e))
            return None

    def hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def generate_api_key(self) -> str:
        """Generate new API key"""
        return f"la_{secrets.token_urlsafe(32)}"  # la_ prefix for "legal automation"

    def validate_api_key(self, api_key: str, stored_hash: str) -> bool:
        """Validate API key against stored hash"""
        return self.hash_api_key(api_key) == stored_hash


class PermissionManager:
    """Permission management for role-based access control"""

    def __init__(self):
        self.logger = structlog.get_logger().bind(component="PermissionManager")

        # Define role permissions
        self.role_permissions = {
            "admin": [
                "user:read", "user:write", "user:delete",
                "company:read", "company:write", "company:delete",
                "document:read", "document:write", "document:delete",
                "system:read", "system:write",
                "audit:read"
            ],
            "legal_admin": [
                "document:read", "document:write", "document:delete",
                "company:read", "company:write",
                "user:read", "user:write",
                "notification:read", "notification:write",
                "audit:read"
            ],
            "company_user": [
                "document:read", "document:write",
                "company:read",
                "notification:read"
            ],
            "viewer": [
                "document:read",
                "company:read"
            ]
        }

        # Define resource-based permissions
        self.resource_permissions = {
            "document": ["read", "write", "delete"],
            "company": ["read", "write", "delete"],
            "user": ["read", "write", "delete"],
            "notification": ["read", "write"],
            "system": ["read", "write"],
            "audit": ["read"]
        }

    def has_permission(self, user: User, required_permission: str) -> bool:
        """Check if user has required permission"""
        try:
            # Check user-specific permissions first
            if required_permission in user.permissions:
                return True

            # Check role-based permissions
            role_perms = self.role_permissions.get(user.role, [])
            if required_permission in role_perms:
                return True

            self.logger.warning(
                "Permission denied",
                user_id=user.id,
                role=user.role,
                required_permission=required_permission
            )
            return False

        except Exception as e:
            self.logger.error("Permission check failed", error=str(e))
            return False

    def has_company_access(self, user: User, company_id: int) -> bool:
        """Check if user has access to specific company"""
        # Admins have access to all companies
        if user.role == "admin":
            return True

        # Legal admins have access to all companies
        if user.role == "legal_admin":
            return True

        # Other users can only access their own company
        return user.company_id == company_id

    def get_user_permissions(self, user: User) -> List[str]:
        """Get all permissions for a user"""
        try:
            # Start with role-based permissions
            role_perms = self.role_permissions.get(user.role, [])

            # Add user-specific permissions
            all_perms = set(role_perms) | set(user.permissions)

            return list(all_perms)

        except Exception as e:
            self.logger.error("Failed to get user permissions", user_id=user.id, error=str(e))
            return []

    def can_access_resource(
        self,
        user: User,
        resource_type: str,
        action: str,
        resource_company_id: Optional[int] = None
    ) -> bool:
        """Check if user can access a specific resource with specific action"""
        try:
            # Check permission
            permission = f"{resource_type}:{action}"
            if not self.has_permission(user, permission):
                return False

            # Check company access if resource belongs to a company
            if resource_company_id and not self.has_company_access(user, resource_company_id):
                return False

            return True

        except Exception as e:
            self.logger.error("Resource access check failed", error=str(e))
            return False


# Global authentication service instance
auth_service = AuthenticationService()
permission_manager = PermissionManager()