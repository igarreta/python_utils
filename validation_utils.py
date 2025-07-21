"""
Configuration validation utilities using Pydantic for backup monitoring.

Provides robust configuration validation with custom validators for backup
monitoring specific requirements like size strings, directory paths, and
email configurations.
"""

import os
import yaml
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
import logging
import re

from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError
from pydantic_core import ValidationError as CoreValidationError

# Import size utilities to avoid circular imports in validators
from .size_utils import validate_size_string, parse_size_to_bytes


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


# Email validation regex
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class BackupCheckConfig(BaseModel):
    """Configuration model for individual backup check."""
    
    name: str = Field(..., description="Short identifier for the backup")
    backup_dir: str = Field(..., description="Path to backup directory")
    days: int = Field(..., gt=0, description="Maximum age in days for backup files")
    min_size: str = Field(default="1 KB", description="Minimum expected backup size")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate backup name format."""
        if not v or not v.strip():
            raise ValueError("Backup name cannot be empty")
        
        # Check for reasonable characters
        if not re.match(r'^[a-zA-Z0-9_-]+$', v.strip()):
            raise ValueError("Backup name must contain only alphanumeric characters, hyphens, and underscores")
        
        return v.strip()
    
    @field_validator('backup_dir')
    @classmethod
    def validate_backup_dir(cls, v):
        """Validate and expand backup directory path."""
        if not v or not v.strip():
            raise ValueError("Backup directory path cannot be empty")
        
        try:
            # Expand user path and resolve
            expanded_path = Path(v).expanduser().resolve()
            return str(expanded_path)
        except Exception as e:
            raise ValueError(f"Invalid directory path '{v}': {e}")
    
    @field_validator('days')
    @classmethod
    def validate_days(cls, v):
        """Validate days is reasonable."""
        if not isinstance(v, int) or v <= 0:
            raise ValueError("Days must be a positive integer")
        
        if v > 365:
            raise ValueError("Days cannot exceed 365 (1 year)")
        
        return v
    
    @field_validator('min_size')
    @classmethod
    def validate_min_size(cls, v):
        """Validate size string format."""
        if not v or not v.strip():
            raise ValueError("Minimum size cannot be empty")
        
        # Use our size validation utility
        size_str = v.strip()
        if not validate_size_string(size_str):
            raise ValueError(f"Invalid size format: '{size_str}'. Expected format like '10 GB', '500 MB'")
        
        return size_str
    
    def get_min_size_bytes(self) -> int:
        """Get minimum size in bytes."""
        return parse_size_to_bytes(self.min_size)
    
    class Config:
        """Pydantic model configuration."""
        validate_assignment = True
        extra = 'forbid'  # Don't allow extra fields


class AppConfig(BaseModel):
    """Main application configuration model."""
    
    # Email settings
    to_email: Optional[List[str]] = Field(default=None, description="List of notification email recipients")
    
    # Pushover settings  
    pushover_priority: int = Field(default=-1, ge=-2, le=2, description="Pushover notification priority")
    
    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="log/proxmox_backup_checker.log", description="Log file path")
    
    # Backup settings
    min_free_space: str = Field(default="100 GB", description="Minimum free space required")
    backup_check_list: List[BackupCheckConfig] = Field(..., min_items=1, description="List of backups to check")
    
    
    @field_validator('to_email')
    @classmethod
    def validate_to_email(cls, v):
        """Validate email addresses."""
        if v is None:
            return v
        
        if not isinstance(v, list):
            raise ValueError("to_email must be a list of email addresses")
        
        if not v:  # Empty list
            return v
        
        validated_emails = []
        for email in v:
            if not isinstance(email, str):
                raise ValueError(f"Email must be string, got {type(email)}: {email}")
            
            email = email.strip()
            if not email:
                continue  # Skip empty strings
            
            if not EMAIL_PATTERN.match(email):
                raise ValueError(f"Invalid email format: {email}")
            
            validated_emails.append(email)
        
        return validated_emails
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate logging level."""
        if not v or not isinstance(v, str):
            raise ValueError("log_level must be a non-empty string")
        
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level '{v}'. Must be one of: {valid_levels}")
        
        return v_upper
    
    @field_validator('log_file')
    @classmethod
    def validate_log_file(cls, v):
        """Validate and expand log file path."""
        if not v or not isinstance(v, str):
            raise ValueError("log_file must be a non-empty string")
        
        try:
            # Expand user path and resolve parent directory
            log_path = Path(v).expanduser()
            
            # Ensure parent directory exists or can be created
            parent_dir = log_path.parent
            parent_dir.mkdir(parents=True, exist_ok=True)
            
            return str(log_path)
        except Exception as e:
            raise ValueError(f"Invalid log file path '{v}': {e}")
    
    @field_validator('min_free_space')
    @classmethod
    def validate_min_free_space(cls, v):
        """Validate minimum free space format."""
        if not v or not isinstance(v, str):
            raise ValueError("min_free_space must be a non-empty string")
        
        size_str = v.strip()
        if not validate_size_string(size_str):
            raise ValueError(f"Invalid size format: '{size_str}'. Expected format like '100 GB', '50 TB'")
        
        return size_str
    
    @field_validator('backup_check_list')
    @classmethod
    def validate_backup_names_unique(cls, v):
        """Ensure backup names are unique."""
        if not v:
            raise ValueError("At least one backup must be configured")
        
        names = [backup.name for backup in v]
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(f"Backup names must be unique. Duplicates found: {list(set(duplicates))}")
        
        return v
    
    def get_min_free_space_bytes(self) -> int:
        """Get minimum free space in bytes."""
        return parse_size_to_bytes(self.min_free_space)
    
    class Config:
        """Pydantic model configuration."""
        validate_assignment = True
        extra = 'forbid'


class SMTPConfig(BaseModel):
    """SMTP configuration model."""
    
    smtp_server: str = Field(..., description="SMTP server hostname")
    smtp_port: int = Field(..., ge=1, le=65535, description="SMTP server port")
    smtp_token: str = Field(..., description="SMTP authentication token/password")
    from_email: str = Field(..., description="From email address")
    to_email: Optional[str] = Field(default=None, description="Default recipient email")
    
    @field_validator('smtp_server')
    @classmethod
    def validate_smtp_server(cls, v):
        """Validate SMTP server hostname."""
        if not v or not v.strip():
            raise ValueError("SMTP server cannot be empty")
        
        # Basic hostname validation
        v = v.strip()
        if len(v) > 253:
            raise ValueError("SMTP server hostname too long")
        
        return v
    
    @field_validator('from_email', 'to_email')
    @classmethod
    def validate_email_format(cls, v):
        """Validate email format."""
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError("Email must be a string")
        
        v = v.strip()
        if not v:
            return None
        
        if not EMAIL_PATTERN.match(v):
            raise ValueError(f"Invalid email format: {v}")
        
        return v
    
    class Config:
        """Pydantic model configuration."""
        validate_assignment = True
        extra = 'forbid'


def parse_config_file(config_path: str, logger: Optional[logging.Logger] = None) -> AppConfig:
    """
    Load and validate configuration from YAML file.
    
    Args:
        config_path: Path to YAML configuration file
        logger: Optional logger for error reporting
        
    Returns:
        Validated AppConfig instance
        
    Raises:
        ConfigValidationError: If file cannot be loaded or validation fails
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    
    try:
        # Expand user path
        config_path = os.path.expanduser(config_path)
        
        # Check if file exists
        if not os.path.exists(config_path):
            raise ConfigValidationError(f"Configuration file not found: {config_path}")
        
        # Load YAML
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        if not isinstance(config_data, dict):
            raise ConfigValidationError(f"Configuration must be a YAML object, got {type(config_data)}")
        
        logger.debug(f"Loaded configuration from {config_path}")
        
        # Validate using Pydantic model
        try:
            config = AppConfig(**config_data)
            logger.info("Configuration validation successful")
            return config
            
        except ValidationError as e:
            # Format validation errors nicely
            error_messages = []
            for error in e.errors():
                field = " -> ".join(str(loc) for loc in error['loc'])
                message = error['msg']
                error_messages.append(f"{field}: {message}")
            
            formatted_errors = "\n  ".join(error_messages)
            raise ConfigValidationError(f"Configuration validation failed:\n  {formatted_errors}")
    
    except ConfigValidationError:
        raise  # Re-raise our own errors
    except yaml.YAMLError as e:
        raise ConfigValidationError(f"YAML parsing error in {config_path}: {e}")
    except Exception as e:
        raise ConfigValidationError(f"Unexpected error loading configuration from {config_path}: {e}")


def create_example_config() -> Dict[str, Any]:
    """
    Create example configuration dictionary.
    
    Returns:
        Dictionary with example configuration values
    """
    return {
        "to_email": [
            "admin@example.com",
            "backup-admin@example.com"
        ],
        "pushover_priority": -1,
        "log_level": "INFO",
        "log_file": "log/proxmox_backup_checker.log",
        "min_free_space": "100 GB",
        "backup_check_list": [
            {
                "name": "proxmox",
                "backup_dir": "/mnt/backup_usb1/vm-containers/dump",
                "days": 8,
                "min_size": "10 GB"
            },
            {
                "name": "homeassistant", 
                "backup_dir": "/mnt/backup_usb1/homeassistant",
                "days": 1,
                "min_size": "30 GB"
            },
            {
                "name": "proxmox-config",
                "backup_dir": "/mnt/backup_usb1/proxmox-config/daily",
                "days": 1,
                "min_size": "10 KB"
            }
        ]
    }


def save_example_config(config_path: str) -> None:
    """
    Save example configuration to YAML file.
    
    Args:
        config_path: Path where to save example config
        
    Raises:
        ConfigValidationError: If file cannot be written
    """
    try:
        config_path = os.path.expanduser(config_path)
        
        # Ensure parent directory exists
        parent_dir = os.path.dirname(config_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        
        # Create example config
        example_config = create_example_config()
        
        # Save to YAML
        with open(config_path, 'w') as f:
            yaml.safe_dump(example_config, f, default_flow_style=False, sort_keys=False)
        
        print(f"Example configuration saved to: {config_path}")
        
    except Exception as e:
        raise ConfigValidationError(f"Failed to save example configuration to {config_path}: {e}")


# Convenience validation functions for non-Pydantic usage
def validate_size_string_simple(size_str: str) -> bool:
    """Simple size string validation without Pydantic."""
    try:
        return validate_size_string(size_str)
    except:
        return False


def validate_email_simple(email: str) -> bool:
    """Simple email validation without Pydantic."""
    if not isinstance(email, str):
        return False
    
    email = email.strip()
    return bool(email and EMAIL_PATTERN.match(email))


def validate_pushover_priority_simple(priority: int) -> bool:
    """Simple pushover priority validation without Pydantic."""
    return isinstance(priority, int) and -2 <= priority <= 2