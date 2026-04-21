"""
Configuration management module for the Project application.

This module handles loading and validation of configuration from environment
variables and configuration files. It provides a centralized configuration
object that can be used throughout the application.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

import yaml
from dotenv import load_dotenv
from pydantic import BaseSettings, Field, validator, ValidationError


class Environment(str, Enum):
    """Enum representing different deployment environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Enum representing different log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    host: str = "localhost"
    port: int = 5432
    name: str = "project_db"
    user: str = "postgres"
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False
    
    @property
    def connection_string(self) -> str:
        """Generate database connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


@dataclass
class RedisConfig:
    """Redis configuration settings."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    decode_responses: bool = True
    
    @property
    def connection_string(self) -> str:
        """Generate Redis connection string."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


@dataclass
class APIConfig:
    """API server configuration settings."""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = False
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    api_prefix: str = "/api/v1"
    secret_key: str = ""
    token_expire_minutes: int = 30


@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[Path] = None
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5


class Settings(BaseSettings):
    """
    Main application settings.
    
    This class loads configuration from multiple sources with the following
    priority (highest to lowest):
    1. Environment variables
    2. .env file
    3. config.yaml file
    4. Default values
    """
    
    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Application
    app_name: str = Field(default="Project", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    
    # Database
    database_host: str = Field(default="localhost", env="DB_HOST")
    database_port: int = Field(default=5432, env="DB_PORT")
    database_name: str = Field(default="project_db", env="DB_NAME")
    database_user: str = Field(default="postgres", env="DB_USER")
    database_password: str = Field(default="", env="DB_PASSWORD")
    database_pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    database_max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    database_echo: bool = Field(default=False, env="DB_ECHO")
    
    # Redis
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # API
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=4, env="API_WORKERS")
    api_reload: bool = Field(default=False, env="API_RELOAD")
    api_cors_origins: str = Field(default="*", env="API_CORS_ORIGINS")
    api_secret_key: str = Field(default="", env="API_SECRET_KEY")
    api_token_expire_minutes: int = Field(default=30, env="API_TOKEN_EXPIRE_MINUTES")
    
    # Logging
    log_level: LogLevel = Field(default=LogLevel.INFO, env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    config_dir: Path = base_dir / "config"
    data_dir: Path = base_dir / "data"
    log_dir: Path = base_dir / "logs"
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("environment", pre=True)
    def validate_environment(cls, v: Any) -> Environment:
        """Validate and convert environment string to Environment enum."""
        if isinstance(v, str):
            try:
                return Environment(v.lower())
            except ValueError:
                raise ValueError(
                    f"Invalid environment '{v}'. Must be one of: "
                    f"{', '.join(e.value for e in Environment)}"
                )
        return v
    
    @validator("log_level", pre=True)
    def validate_log_level(cls, v: Any) -> LogLevel:
        """Validate and convert log level string to LogLevel enum."""
        if isinstance(v, str):
            try:
                return LogLevel(v.upper())
            except ValueError:
                raise ValueError(
                    f"Invalid log level '{v}'. Must be one of: "
                    f"{', '.join(e.value for e in LogLevel)}"
                )
        return v
    
    @validator("api_cors_origins", pre=True)
    def parse_cors_origins(cls, v: Any) -> str:
        """Parse CORS origins from string."""
        if isinstance(v, list):
            return ",".join(v)
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if current environment is development."""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        """Check if current environment is production."""
        return self.environment == Environment.PRODUCTION
    
    @property
    def database(self) -> DatabaseConfig:
        """Get database configuration."""
        return DatabaseConfig(
            host=self.database_host,
            port=self.database_port,
            name=self.database_name,
            user=self.database_user,
            password=self.database_password,
            pool_size=self.database_pool_size,
            max_overflow=self.database_max_overflow,
            echo=self.database_echo,
        )
    
    @property
    def redis(self) -> RedisConfig:
        """Get Redis configuration."""
        return RedisConfig(
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            password=self.redis_password,
        )
    
    @property
    def api(self) -> APIConfig:
        """Get API configuration."""
        return APIConfig(
            host=self.api_host,
            port=self.api_port,
            workers=self.api_workers,
            reload=self.api_reload,
            cors_origins=self.api_cors_origins.split(","),
            secret_key=self.api_secret_key,
            token_expire_minutes=self.api_token_expire_minutes,
        )
    
    @property
    def logging(self) -> LoggingConfig:
        """Get logging configuration."""
        file_path = None
        if self.log_file:
            file_path = self.log_dir / self.log_file
        return LoggingConfig(
            level=self.log_level,
            file_path=file_path,
        )


class ConfigManager:
    """
    Configuration manager for loading and accessing application settings.
    
    This class provides a singleton pattern for accessing configuration
    throughout the application and handles loading from multiple sources.
    """
    
    _instance: Optional['ConfigManager'] = None
    _settings: Optional[Settings] = None
    
    def __new__(cls) -> 'ConfigManager':
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize configuration manager."""
        if self._settings is None:
            self._settings = self._load_settings()
    
    def _load_settings(self) -> Settings:
        """
        Load settings from multiple sources.
        
        Returns:
            Settings: Loaded application settings.
            
        Raises:
            FileNotFoundError: If required configuration file is not found.
            ValidationError: If configuration validation fails.
            yaml.YAMLError: If YAML configuration file is malformed.
        """
        try:
            # Load environment variables from .env file if it exists
            env_path = Path(__file__).parent.parent.parent / ".env"
            if env_path.exists():
                load_dotenv(env_path)
            
            # Try to load YAML configuration if it exists
            yaml_config = self._load_yaml_config()
            
            # Create settings with environment variables taking precedence
            settings = Settings(**yaml_config)
            
            # Create necessary directories
            self._create_directories(settings)
            
            return settings
            
        except ValidationError as e:
            print(f"Configuration validation error: {e}", file=sys.stderr)
            raise
        except yaml.YAMLError as e:
            print(f"YAML configuration error: {e}", file=sys.stderr)
            raise
        except Exception as e:
            print(f"Unexpected error loading configuration: {e}", file=sys.stderr)
            raise
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Returns:
            Dict[str, Any]: Configuration dictionary from YAML file.
            
        Raises:
            FileNotFoundError: If config.yaml file is not found.
            yaml.YAMLError: If YAML file is malformed.
        """
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
        
        if not config_path.exists():
            # Return empty dict if config file doesn't exist
            return {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if config_data is None:
                return {}
            
            return config_data
            
        except yaml.YAMLError as e:
            print(f"Error parsing YAML configuration file: {e}", file=sys.stderr)
            raise
    
    def _create_directories(self, settings: Settings) -> None:
        """
        Create necessary directories if they don't exist.
        
        Args:
            settings: Application settings.
        """
        try:
            settings.data_dir.mkdir(parents=True, exist_ok=True)
            settings.log_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"Error creating directories: {e}", file=sys.stderr)
            raise
    
    @property
    def settings(self) -> Settings:
        """
        Get application settings.
        
        Returns:
            Settings: Application settings.
            
        Raises:
            RuntimeError: If settings are not loaded.
        """
        if self._settings is None:
            raise RuntimeError("Settings not loaded. Call load() first.")
        return self._settings
    
    def reload(self) -> None:
        """Reload configuration from sources."""
        self._settings = self._load_settings()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key.
            default: Default value if key not found.
            
        Returns:
            Configuration value or default.
        """
        try:
            return getattr(self.settings, key)
        except AttributeError:
            return default


# Global configuration instance
config_manager = ConfigManager()


def get_config() -> Settings:
    """
    Get application configuration.
    
    Returns:
        Settings: Application settings.
        
    Example:
        >>> config = get_config()
        >>> print(config.environment)
        development
    """
    return config_manager.settings


def get_database_config() -> DatabaseConfig:
    """
    Get database configuration.
    
    Returns:
        DatabaseConfig: Database settings.
    """
    return get_config().database


def get_redis_config() -> RedisConfig:
    """
    Get Redis configuration.
    
    Returns:
        RedisConfig: Redis settings.
    """
    return get_config().redis


def get_api_config() -> APIConfig:
    """
    Get API configuration.