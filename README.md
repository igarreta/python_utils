# Python Utils

A comprehensive Python utility library for backup monitoring, system administration, and server automation tasks.

## Overview

This library provides a collection of utilities commonly needed in backup monitoring and system administration scripts:

- **Size utilities** - Parse and format human-readable sizes (KB, MB, GB, TB)
- **Email utilities** - SMTP email notifications with professional formatting
- **Filesystem utilities** - Directory access, disk usage, and file age checking
- **Validation utilities** - Pydantic-based configuration validation
- **Push notifications** - Pushover.net integration for critical alerts
- **Logging utilities** - Advanced logging with rotation and stream redirection

## Installation

```bash
pip install python-dotenv pydantic PyYAML requests
```

Or install from requirements:
```bash
pip install -r requirements.txt
```

## Quick Start

```python
from python_utils import (
    parse_size_to_bytes,
    setup_backup_logging,
    is_directory_accessible,
    EmailNotifier,
    PushoverNotifier,
    AppConfig,
    parse_config_file
)

# Size utilities
size_bytes = parse_size_to_bytes("10 GB")  # Returns 10737418240

# Logging setup
logger = setup_backup_logging("my_app")
logger.info("Application started")

# Filesystem operations
if is_directory_accessible("/path/to/backup"):
    print("Backup directory is accessible")

# Email notifications
notifier = EmailNotifier()
subject, content = notifier.create_backup_summary_email(
    backup_results=[], errors=[], duration=10.5
)

# Push notifications  
pushover = PushoverNotifier("App Name")
pushover.send("Test message", priority=-1)

# Configuration validation
config = parse_config_file("config.yaml")
print(f"Loaded {len(config.backup_check_list)} backup configurations")
```

## Modules

### size_utils
Parse and format human-readable sizes with binary units.

```python
from python_utils import parse_size_to_bytes, bytes_to_human_readable

# Parse sizes
bytes_val = parse_size_to_bytes("1.5 GB")  # 1610612736
bytes_val = parse_size_to_bytes("500MB")   # 524288000

# Format sizes  
human = bytes_to_human_readable(1073741824)  # "1.0 GB"
```

### email_utils
SMTP email notifications with TLS/SSL support and professional formatting.

```python
from python_utils import EmailNotifier

# Setup (requires ~/etc/grsrv03.env with SMTP settings)
notifier = EmailNotifier()

# Send notification
success = notifier.send_email(
    to_emails=["admin@example.com"],
    subject="Backup Report",
    content="All backups completed successfully"
)

# Create backup summary
subject, content = notifier.create_backup_summary_email(
    backup_results=[
        {"name": "db", "success": True, "total_size_human": "2.1 GB"}
    ],
    errors=[],
    duration=15.7
)
```

### filesystem_utils
Safe filesystem operations with comprehensive error handling.

```python
from python_utils import (
    is_directory_accessible,
    get_disk_usage, 
    get_files_modified_within_days,
    check_minimum_free_space
)

# Check directory access
if is_directory_accessible("/mnt/backup"):
    print("Directory is accessible")

# Get disk usage
total, used, free = get_disk_usage("/mnt/backup")
print(f"Free space: {free / (1024**3):.1f} GB")

# Find recent files
recent_files = get_files_modified_within_days("/mnt/backup", days=7)
print(f"Found {len(recent_files)} files modified in last 7 days")

# Check minimum free space
has_space, message = check_minimum_free_space("/mnt/backup", 10 * 1024**3)
if not has_space:
    print(f"Warning: {message}")
```

### validation_utils
Pydantic-based configuration validation with custom validators.

```python
from python_utils import AppConfig, BackupCheckConfig, parse_config_file

# Define backup configuration
backup_config = BackupCheckConfig(
    name="database",
    backup_dir="/mnt/backups/db",
    days=1,
    min_size="5 GB"
)

print(f"Min size in bytes: {backup_config.get_min_size_bytes()}")

# Load and validate complete configuration
config = parse_config_file("backup_config.yaml")
print(f"Loaded {len(config.backup_check_list)} backup configurations")
print(f"Min free space: {config.get_min_free_space_bytes()} bytes")
```

### pushover_utils
Pushover.net push notifications with automatic error correction.

```python
from python_utils import PushoverNotifier, send_critical_backup_alert

# Setup (requires ~/etc/pushover.env with credentials)
notifier = PushoverNotifier("Backup Monitor")

# Send notification
success = notifier.send("Backup completed successfully", priority=-1)

# Send backup-specific alerts
notifier.send_backup_alert("database", "Connection failed", priority=1)

# Send summary notification
notifier.send_backup_summary(
    total_backups=3, successful_backups=2, failed_backups=1, duration=25.3
)

# Convenience function for critical alerts
send_critical_backup_alert("CRITICAL: All backup drives offline!")
```

### logging_utils
Advanced logging with rotation, formatting, and stream redirection.

```python
from python_utils import setup_backup_logging, StreamLogger, redirect_stdout_stderr

# Quick setup for backup applications
logger = setup_backup_logging("my_backup_app")
logger.info("Backup started")

# Custom logging setup
from python_utils import setup_logger
import logging

logger = logging.getLogger("custom_app")
setup_logger(
    logger,
    log_filename="log/custom.log",
    level=logging.DEBUG,
    handler_config="daily_7",  # Daily rotation, 7 days retention
    formatter_config="detailed"
)

# Redirect stdout/stderr to log
stdout_logger, stderr_logger = redirect_stdout_stderr(logger)
print("This goes to the log file")  # Logged as INFO
print("Error message", file=sys.stderr)  # Logged as ERROR
```

## Configuration Files

### SMTP Configuration (`~/etc/grsrv03.env`)
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
FROM_EMAIL=backup-monitor@example.com
TO_EMAIL=admin@example.com
SMTP_TOKEN=your-app-password
```

### Pushover Configuration (`~/etc/pushover.env`)
```bash
PUSHOVER_TOKEN=your-30-character-app-token
PUSHOVER_USER=your-30-character-user-key
```

### Example Application Configuration (`config.yaml`)
```yaml
to_email:
  - admin@example.com
pushover_priority: -1
log_level: INFO
min_free_space: 100 GB
backup_check_list:
  - name: database
    backup_dir: /mnt/backups/db
    days: 1
    min_size: 5 GB
  - name: files
    backup_dir: /mnt/backups/files  
    days: 7
    min_size: 1 GB
```

## Dependencies

- `pydantic>=2.11.7` - Configuration validation
- `PyYAML>=6.0.2` - YAML configuration parsing  
- `python-dotenv>=1.1.1` - Environment variable management
- `requests>=2.31.0` - HTTP requests for Pushover API

## Error Handling

All utilities are designed to be exception-safe and suitable for production use:

- **Email utilities** return boolean success/failure instead of raising exceptions
- **Pushover utilities** auto-correct invalid parameters and never block execution
- **Filesystem utilities** handle permission errors and missing paths gracefully
- **Validation utilities** provide detailed error messages for configuration issues
- **Logging utilities** create directories automatically and handle rotation errors

## Use Cases

This library is particularly well-suited for:

- **Backup monitoring systems** - Validate backup integrity and send notifications
- **System administration scripts** - Check disk usage, file ages, and system health
- **Automated reporting** - Generate and send professional status reports
- **Service monitoring** - Log application status with rotation and alerting
- **Configuration management** - Validate complex YAML/JSON configurations

## Development

The library follows Python best practices:

- Type hints throughout for better IDE support
- Comprehensive docstrings for all public functions  
- Exception-safe design suitable for cron jobs
- Modular design allowing selective imports
- Production-ready error handling and logging

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## Support

For issues and questions:

1. Check the docstrings for detailed parameter information
2. Review the example configurations above  
3. Test individual components in isolation
4. Create an issue with detailed error information and configuration