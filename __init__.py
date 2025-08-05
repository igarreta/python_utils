"""
Python utilities collection for backup monitoring and system administration tasks.

This package provides common utilities for:
- Size parsing and conversion
- Email notifications
- Filesystem operations
- Configuration validation
"""

__version__ = "1.1.0"
__author__ = "igarreta"

from .size_utils import parse_size_to_bytes, bytes_to_human_readable, validate_size_string, InvalidSizeFormatError
from .email_utils import EmailNotifier, EmailConfigError, EmailSendError, send_backup_notification
from .filesystem_utils import (
    is_directory_accessible, 
    get_disk_usage, 
    get_files_modified_within_days,
    calculate_total_size,
    format_disk_usage,
    check_minimum_free_space,
    get_file_age_summary,
    FilesystemError
)
from .validation_utils import (
    BackupCheckConfig,
    AppConfig,
    SMTPConfig,
    ConfigValidationError,
    parse_config_file,
    create_example_config,
    save_example_config,
    validate_size_string_simple,
    validate_email_simple,
    validate_pushover_priority_simple
)
from .pushover_utils import (
    PushoverNotifier,
    PushoverError,
    send_critical_backup_alert
)
from .uptime_kuma_utils import (
    send_uptime_kuma_heartbeat,
    UptimeKumaError
)
from .logging_utils import (
    StreamLogger,
    LoggingError,
    setup_logger,
    redirect_stdout_stderr,
    restore_stdout_stderr,
    setup_backup_logging,
    get_log_info,
    HANDLER_CONFIGURATIONS,
    FORMATTER_CONFIGURATIONS
)

__all__ = [
    "parse_size_to_bytes",
    "bytes_to_human_readable", 
    "validate_size_string",
    "InvalidSizeFormatError",
    "EmailNotifier",
    "EmailConfigError", 
    "EmailSendError",
    "send_backup_notification",
    "is_directory_accessible",
    "get_disk_usage",
    "get_files_modified_within_days", 
    "calculate_total_size",
    "format_disk_usage",
    "check_minimum_free_space",
    "get_file_age_summary",
    "FilesystemError",
    "BackupCheckConfig",
    "AppConfig", 
    "SMTPConfig",
    "ConfigValidationError",
    "parse_config_file",
    "create_example_config",
    "save_example_config",
    "validate_size_string_simple",
    "validate_email_simple",
    "validate_pushover_priority_simple",
    "PushoverNotifier",
    "PushoverError",
    "send_critical_backup_alert",
    "send_uptime_kuma_heartbeat",
    "UptimeKumaError",
    "StreamLogger",
    "LoggingError",
    "setup_logger",
    "redirect_stdout_stderr",
    "restore_stdout_stderr", 
    "setup_backup_logging",
    "get_log_info",
    "HANDLER_CONFIGURATIONS",
    "FORMATTER_CONFIGURATIONS"
]