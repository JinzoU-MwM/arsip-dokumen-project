"""
Encryption and decryption utilities for data security
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import structlog
from typing import Optional, Union

logger = structlog.get_logger()


class EncryptionService:
    """Encryption service for sensitive data protection"""

    def __init__(self, encryption_key: Optional[str] = None):
        self.logger = structlog.get_logger().bind(component="EncryptionService")

        # Get encryption key from environment or parameter
        key = encryption_key or os.getenv("ENCRYPTION_KEY")

        if not key:
            # Generate a new key if none provided (NOT recommended for production)
            self.logger.warning("No encryption key provided, generating temporary key")
            key = Fernet.generate_key().decode()
            self.logger.warning("Generated encryption key (SAVE THIS KEY):", key=key[:20] + "...")

        # Ensure key is properly encoded
        if isinstance(key, str):
            key = key.encode()

        # Derive encryption key using PBKDF2
        self.fernet = self._create_fernet(key)

    def _create_fernet(self, key: bytes) -> Fernet:
        """Create Fernet instance with key derivation"""
        try:
            # Use PBKDF2 to derive a proper encryption key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'legal_automation_salt',  # In production, use a random salt per deployment
                iterations=100000,
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(key))
            return Fernet(derived_key)
        except Exception as e:
            self.logger.error("Failed to create encryption instance", error=str(e))
            raise

    def encrypt(self, data: Union[str, bytes]) -> str:
        """Encrypt data and return base64 encoded string"""
        try:
            if isinstance(data, str):
                data = data.encode()

            encrypted_data = self.fernet.encrypt(data)
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            self.logger.error("Encryption failed", error=str(e))
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt base64 encoded string and return original data"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            self.logger.error("Decryption failed", error=str(e))
            raise

    def encrypt_sensitive_field(self, field_name: str, value: str) -> str:
        """Encrypt a sensitive field with metadata"""
        try:
            # Add metadata for field identification
            metadata = f"field:{field_name}:"
            combined_data = metadata + value

            encrypted = self.encrypt(combined_data)
            return encrypted
        except Exception as e:
            self.logger.error("Field encryption failed", field_name=field_name, error=str(e))
            raise

    def decrypt_sensitive_field(self, encrypted_value: str) -> str:
        """Decrypt a sensitive field and remove metadata"""
        try:
            decrypted = self.decrypt(encrypted_value)

            # Remove metadata if present
            if decrypted.startswith("field:"):
                parts = decrypted.split(":", 2)
                if len(parts) >= 3:
                    return parts[2]  # Return the actual value

            return decrypted
        except Exception as e:
            self.logger.error("Field decryption failed", error=str(e))
            raise

    def encrypt_dict(self, data: dict) -> dict:
        """Encrypt values in a dictionary (sensitive fields only)"""
        try:
            encrypted_data = {}
            sensitive_fields = [
                'password', 'token', 'secret', 'key', 'credential',
                'ssn', 'social_security', 'tax_id', 'credit_card',
                'bank_account', 'api_key', 'private_key'
            ]

            for key, value in data.items():
                if isinstance(value, str) and any(sensitive in key.lower() for sensitive in sensitive_fields):
                    encrypted_data[key] = self.encrypt_sensitive_field(key, value)
                    encrypted_data[f"{key}_encrypted"] = True
                else:
                    encrypted_data[key] = value
                    encrypted_data[f"{key}_encrypted"] = False

            return encrypted_data
        except Exception as e:
            self.logger.error("Dict encryption failed", error=str(e))
            raise

    def decrypt_dict(self, encrypted_data: dict) -> dict:
        """Decrypt values in a dictionary (only encrypted fields)"""
        try:
            decrypted_data = {}

            for key, value in encrypted_data.items():
                # Skip encryption metadata fields
                if key.endswith('_encrypted'):
                    continue

                # Check if this field was encrypted
                encrypted_flag = encrypted_data.get(f"{key}_encrypted", False)

                if encrypted_flag and isinstance(value, str):
                    try:
                        decrypted_data[key] = self.decrypt_sensitive_field(value)
                    except:
                        # If decryption fails, keep original value
                        decrypted_data[key] = value
                else:
                    decrypted_data[key] = value

            return decrypted_data
        except Exception as e:
            self.logger.error("Dict decryption failed", error=str(e))
            raise

    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure random token"""
        try:
            import secrets
            token = secrets.token_urlsafe(length)
            self.logger.info("Secure token generated", length=length)
            return token
        except Exception as e:
            self.logger.error("Token generation failed", error=str(e))
            raise

    def hash_sensitive_data(self, data: str, salt: Optional[str] = None) -> str:
        """Create a hash of sensitive data (one-way)"""
        try:
            import hashlib

            if salt is None:
                salt = os.getenv("HASH_SALT", "default_salt")

            combined = data + salt
            hash_object = hashlib.sha256(combined.encode())
            return hash_object.hexdigest()
        except Exception as e:
            self.logger.error("Data hashing failed", error=str(e))
            raise

    def verify_hash(self, data: str, hash_value: str, salt: Optional[str] = None) -> bool:
        """Verify data against its hash"""
        try:
            computed_hash = self.hash_sensitive_data(data, salt)
            return computed_hash == hash_value
        except Exception as e:
            self.logger.error("Hash verification failed", error=str(e))
            return False


class DataMaskingService:
    """Service for masking sensitive data in logs and outputs"""

    def __init__(self):
        self.logger = structlog.get_logger().bind(component="DataMaskingService")

    def mask_email(self, email: str) -> str:
        """Mask email address"""
        try:
            if '@' not in email:
                return email[:2] + '*' * (len(email) - 2)

            local, domain = email.split('@', 1)
            if len(local) <= 2:
                masked_local = local[0] + '*' * (len(local) - 1)
            else:
                masked_local = local[:2] + '*' * (len(local) - 3) + local[-1]

            return f"{masked_local}@{domain}"
        except Exception as e:
            self.logger.error("Email masking failed", error=str(e))
            return "masked@email.com"

    def mask_phone(self, phone: str) -> str:
        """Mask phone number"""
        try:
            # Remove non-digit characters
            digits = ''.join(filter(str.isdigit, phone))

            if len(digits) <= 4:
                return '*' * len(phone)

            # Show last 4 digits
            return '*' * (len(phone) - 4) + phone[-4:]
        except Exception as e:
            self.logger.error("Phone masking failed", error=str(e))
            return "****"

    def mask_credit_card(self, card_number: str) -> str:
        """Mask credit card number"""
        try:
            # Remove non-digit characters
            digits = ''.join(filter(str.isdigit, card_number))

            if len(digits) != 16:
                return '*' * 16

            # Show last 4 digits
            return '*' * 12 + digits[-4:]
        except Exception as e:
            self.logger.error("Credit card masking failed", error=str(e))
            return "**** **** **** ****"

    def mask_text(self, text: str, visible_chars: int = 4) -> str:
        """General text masking"""
        try:
            if len(text) <= visible_chars:
                return '*' * len(text)

            return text[:visible_chars] + '*' * (len(text) - visible_chars)
        except Exception as e:
            self.logger.error("Text masking failed", error=str(e))
            return "****"

    def mask_dict_values(self, data: dict, sensitive_keys: list = None) -> dict:
        """Mask sensitive values in a dictionary"""
        try:
            if sensitive_keys is None:
                sensitive_keys = [
                    'password', 'token', 'secret', 'key', 'credential',
                    'ssn', 'social_security', 'tax_id', 'credit_card',
                    'bank_account', 'api_key', 'private_key', 'phone',
                    'email', 'address'
                ]

            masked_data = {}

            for key, value in data.items():
                if isinstance(value, str) and any(sensitive in key.lower() for sensitive in sensitive_keys):
                    if 'email' in key.lower():
                        masked_data[key] = self.mask_email(value)
                    elif 'phone' in key.lower() or 'mobile' in key.lower():
                        masked_data[key] = self.mask_phone(value)
                    elif 'credit_card' in key.lower() or 'card' in key.lower():
                        masked_data[key] = self.mask_credit_card(value)
                    else:
                        masked_data[key] = self.mask_text(value)
                else:
                    masked_data[key] = value

            return masked_data
        except Exception as e:
            self.logger.error("Dict masking failed", error=str(e))
            return data


# Global service instances
encryption_service = EncryptionService()
data_masking_service = DataMaskingService()