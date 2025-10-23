"""
Configuration management system for the AI Legal Document Automation System
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, Type, TypeVar, Union
from pydantic import BaseSettings, Field, validator
from enum import Enum
import structlog

logger = structlog.get_logger()

T = TypeVar("T", bound=BaseSettings)


class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseConfig(BaseSettings):
    """Database configuration"""
    url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/legal_automation",
        env="DATABASE_URL"
    )
    echo: bool = Field(default=False, env="SQL_DEBUG")
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE")

    @validator("url", pre=True)
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v


class RedisConfig(BaseSettings):
    """Redis configuration"""
    url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    max_connections: int = Field(default=100, env="REDIS_MAX_CONNECTIONS")
    retry_on_timeout: bool = Field(default=True, env="REDIS_RETRY_ON_TIMEOUT")
    socket_timeout: int = Field(default=5, env="REDIS_SOCKET_TIMEOUT")
    socket_connect_timeout: int = Field(default=5, env="REDIS_SOCKET_CONNECT_TIMEOUT")


class OllamaConfig(BaseSettings):
    """Ollama AI service configuration"""
    url: str = Field(default="http://localhost:11434", env="OLLAMA_URL")
    model: str = Field(default="llama3:70b", env="OLLAMA_MODEL")
    timeout: int = Field(default=120, env="OLLAMA_TIMEOUT")
    max_tokens: int = Field(default=4096, env="OLLAMA_MAX_TOKENS")
    temperature: float = Field(default=0.7, env="OLLAMA_TEMPERATURE")


class WAHAConfig(BaseSettings):
    """WAHA WhatsApp service configuration"""
    url: str = Field(default="http://localhost:3000", env="WAHA_URL")
    api_key: str = Field(env="WAHA_API_KEY")
    session: str = Field(default="default", env="WAHA_SESSION")
    timeout: int = Field(default=60, env="WAHA_TIMEOUT")


class GoogleDriveConfig(BaseSettings):
    """Google Drive service configuration"""
    credentials_file: str = Field(
        default="./config/google-credentials.json",
        env="GOOGLE_DRIVE_CREDENTIALS_FILE"
    )
    root_folder_id: str = Field(env="GOOGLE_DRIVE_ROOT_FOLDER_ID")
    chunk_size: int = Field(default=8 * 1024 * 1024, env="GOOGLE_DRIVE_CHUNK_SIZE")  # 8MB
    max_retries: int = Field(default=3, env="GOOGLE_DRIVE_MAX_RETRIES")


class SecurityConfig(BaseSettings):
    """Security configuration"""
    jwt_secret_key: str = Field(env="JWT_SECRET_KEY")
    jwt_access_token_expire_minutes: int = Field(
        default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS"
    )
    encryption_key: str = Field(env="ENCRYPTION_KEY")
    password_min_length: int = Field(default=8, env="PASSWORD_MIN_LENGTH")
    session_timeout: int = Field(default=3600, env="SESSION_TIMEOUT")  # 1 hour
    max_login_attempts: int = Field(default=5, env="MAX_LOGIN_ATTEMPTS")
    lockout_duration: int = Field(default=900, env="LOCKOUT_DURATION")  # 15 minutes

    @validator("jwt_secret_key", pre=True)
    def validate_jwt_secret(cls, v):
        if not v:
            raise ValueError("JWT_SECRET_KEY is required")
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v

    @validator("encryption_key", pre=True)
    def validate_encryption_key(cls, v):
        if not v:
            raise ValueError("ENCRYPTION_KEY is required")
        if len(v) < 32:
            raise ValueError("ENCRYPTION_KEY must be at least 32 characters")
        return v


class LoggingConfig(BaseSettings):
    """Logging configuration"""
    level: str = Field(default="info", env="LOG_LEVEL")
    format: str = Field(default="json", env="LOG_FORMAT")
    file: Optional[str] = Field(default=None, env="LOG_FILE")
    max_file_size: int = Field(default=100 * 1024 * 1024, env="LOG_MAX_FILE_SIZE")  # 100MB
    backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    enable_console: bool = Field(default=True, env="LOG_ENABLE_CONSOLE")

    @validator("level")
    def validate_log_level(cls, v):
        valid_levels = ["debug", "info", "warning", "error", "critical"]
        if v.lower() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.lower()

    @validator("format")
    def validate_log_format(cls, v):
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Log format must be one of: {valid_formats}")
        return v.lower()


class MonitoringConfig(BaseSettings):
    """Monitoring configuration"""
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    grafana_port: int = Field(default=3001, env="GRAFANA_PORT")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    metrics_path: str = Field(default="/metrics", env="METRICS_PATH")


class FileProcessingConfig(BaseSettings):
    """File processing configuration"""
    watch_folders: list = Field(
        default=["D:/Download Legalitas", "D:/Documents/Legal/Queue"],
        env="WATCH_FOLDERS"
    )
    supported_extensions: list = Field(
        default=["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "jpg", "jpeg", "png"],
        env="SUPPORTED_EXTENSIONS"
    )
    max_file_size_mb: int = Field(default=100, env="MAX_FILE_SIZE_MB")
    processing_timeout: int = Field(default=300, env="PROCESSING_TIMEOUT")  # 5 minutes
    chunk_size: int = Field(default=8192, env="FILE_CHUNK_SIZE")

    @validator("watch_folders", pre=True)
    def parse_watch_folders(cls, v):
        if isinstance(v, str):
            return [folder.strip() for folder in v.split(",")]
        return v

    @validator("supported_extensions", pre=True)
    def parse_supported_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip().lower() for ext in v.split(",")]
        return v


class NotificationConfig(BaseSettings):
    """Notification configuration"""
    smtp_host: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: str = Field(env="SMTP_USER")
    smtp_password: str = Field(env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, env="SMTP_USE_TLS")

    rate_limit_per_minute: int = Field(default=30, env="RATE_LIMIT_PER_MINUTE")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    retry_delay: int = Field(default=5, env="RETRY_DELAY")  # seconds


class AppConfig(BaseSettings):
    """Main application configuration"""
    name: str = Field(default="AI Legal Document Automation", env="APP_NAME")
    version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default=Environment.DEVELOPMENT.value, env="NODE_ENV")
    debug: bool = Field(default=False, env="DEBUG")

    # Service configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")

    # Sub-configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    waha: WAHAConfig = Field(default_factory=WAHAConfig)
    google_drive: GoogleDriveConfig = Field(default_factory=GoogleDriveConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    file_processing: FileProcessingConfig = Field(default_factory=FileProcessingConfig)
    notification: NotificationConfig = Field(default_factory=NotificationConfig)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("environment", pre=True)
    def validate_environment(cls, v):
        valid_envs = [env.value for env in Environment]
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v.lower()

    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT.value

    @property
    def is_testing(self) -> bool:
        return self.environment == Environment.TESTING.value

    @property
    def is_staging(self) -> bool:
        return self.environment == Environment.STAGING.value

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION.value

    def get_service_url(self, service_name: str, port: int = None) -> str:
        """Get service URL based on environment"""
        if self.is_development or self.is_testing:
            host = "localhost"
        else:
            host = f"{service_name}.legalautomation.local"

        service_port = port or self.port
        return f"http://{host}:{service_port}"

    def get_database_url(self) -> str:
        """Get database URL with proper encoding"""
        return self.database.url

    def get_redis_url(self) -> str:
        """Get Redis URL"""
        return self.redis.url

    def get_log_level(self) -> str:
        """Get log level as uppercase string"""
        return self.logging.level.upper()


class ConfigManager:
    """Configuration manager for loading and managing configurations"""

    def __init__(self):
        self.logger = structlog.get_logger().bind(component="ConfigManager")
        self._config: Optional[AppConfig] = None
        self._config_file: Optional[str] = None

    def load_config(self, config_file: str = None, config_class: Type[T] = AppConfig) -> T:
        """Load configuration from file and environment"""
        try:
            self._config_file = config_file or self._find_config_file()

            # Load configuration
            if self._config_file and os.path.exists(self._config_file):
                self.logger.info("Loading configuration from file", file=self._config_file)
                config = config_class(_env_file=self._config_file)
            else:
                self.logger.info("Loading configuration from environment")
                config = config_class()

            # Validate configuration
            self._validate_config(config)

            self._config = config
            self.logger.info("Configuration loaded successfully",
                           environment=config.environment,
                           debug=config.debug)

            return config

        except Exception as e:
            self.logger.error("Failed to load configuration", error=str(e))
            raise

    def _find_config_file(self) -> Optional[str]:
        """Find configuration file in standard locations"""
        possible_files = [
            "config.yaml",
            "config.yml",
            "config.json",
            ".env",
            os.path.expanduser("~/.legalautomation/config.yaml"),
            "/etc/legalautomation/config.yaml"
        ]

        for file_path in possible_files:
            if os.path.exists(file_path):
                return file_path

        return None

    def _validate_config(self, config: AppConfig) -> None:
        """Validate configuration"""
        validation_errors = []

        # Validate required fields for production
        if config.is_production:
            if not config.security.jwt_secret_key:
                validation_errors.append("JWT_SECRET_KEY is required in production")

            if not config.security.encryption_key:
                validation_errors.append("ENCRYPTION_KEY is required in production")

            if "localhost" in config.database.url:
                validation_errors.append("Database URL should not use localhost in production")

        # Validate security configurations
        if len(config.security.jwt_secret_key) < 32:
            validation_errors.append("JWT_SECRET_KEY must be at least 32 characters")

        if len(config.security.encryption_key) < 32:
            validation_errors.append("ENCRYPTION_KEY must be at least 32 characters")

        # Validate file paths
        if config.google_drive.credentials_file and not os.path.exists(config.google_drive.credentials_file):
            validation_errors.append(f"Google Drive credentials file not found: {config.google_drive.credentials_file}")

        # Validate folders
        for folder in config.file_processing.watch_folders:
            if not os.path.exists(folder):
                validation_errors.append(f"Watch folder not found: {folder}")

        if validation_errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in validation_errors)
            raise ValueError(error_msg)

    def get_config(self) -> AppConfig:
        """Get current configuration"""
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        return self._config

    def reload_config(self) -> AppConfig:
        """Reload configuration"""
        config_class = type(self._config) if self._config else AppConfig
        return self.load_config(self._config_file, config_class)

    def save_config(self, config_file: str = None) -> None:
        """Save current configuration to file"""
        try:
            file_path = config_file or self._config_file or "config.yaml"

            # Convert config to dictionary and save
            config_dict = self._config.dict()

            # Choose format based on file extension
            if file_path.endswith('.json'):
                with open(file_path, 'w') as f:
                    json.dump(config_dict, f, indent=2)
            else:
                with open(file_path, 'w') as f:
                    yaml.dump(config_dict, f, default_flow_style=False)

            self.logger.info("Configuration saved", file=file_path)

        except Exception as e:
            self.logger.error("Failed to save configuration", error=str(e))
            raise

    def get_environment_variables(self) -> Dict[str, str]:
        """Get all relevant environment variables"""
        env_vars = {}

        # Database
        env_vars.update({
            "DATABASE_URL": self._config.database.url,
            "SQL_DEBUG": str(self._config.database.echo).lower(),
            "REDIS_URL": self._config.redis.url,
        })

        # Security
        env_vars.update({
            "JWT_SECRET_KEY": self._config.security.jwt_secret_key,
            "ENCRYPTION_KEY": self._config.security.encryption_key,
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": str(self._config.security.jwt_access_token_expire_minutes),
            "JWT_REFRESH_TOKEN_EXPIRE_DAYS": str(self._config.security.jwt_refresh_token_expire_days),
        })

        # Services
        env_vars.update({
            "OLLAMA_URL": self._config.ollama.url,
            "OLLAMA_MODEL": self._config.ollama.model,
            "WAHA_URL": self._config.waha.url,
            "WAHA_API_KEY": self._config.waha.api_key or "",
            "GOOGLE_DRIVE_CREDENTIALS_FILE": self._config.google_drive.credentials_file,
        })

        # Application
        env_vars.update({
            "APP_NAME": self._config.name,
            "APP_VERSION": self._config.version,
            "NODE_ENV": self._config.environment,
            "DEBUG": str(self._config.debug).lower(),
            "LOG_LEVEL": self._config.logging.level,
            "LOG_FORMAT": self._config.logging.format,
        })

        return env_vars

    def export_environment_variables(self, file_path: str = ".env") -> None:
        """Export configuration to environment file"""
        try:
            env_vars = self.get_environment_variables()

            with open(file_path, 'w') as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")

            self.logger.info("Environment variables exported", file=file_path)

        except Exception as e:
            self.logger.error("Failed to export environment variables", error=str(e))
            raise


# Global configuration manager instance
config_manager = ConfigManager()