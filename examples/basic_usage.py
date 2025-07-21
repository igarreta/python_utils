#!/usr/bin/env python3
"""
Basic usage examples for python_utils library.

This script demonstrates the core functionality of each module
in the python_utils library.
"""

import logging
import sys
from pathlib import Path

# Import all utilities from python_utils
from python_utils import (
    # Size utilities
    parse_size_to_bytes,
    bytes_to_human_readable,
    validate_size_string,
    
    # Filesystem utilities
    is_directory_accessible,
    get_disk_usage,
    get_files_modified_within_days,
    check_minimum_free_space,
    
    # Logging utilities
    setup_backup_logging,
    setup_logger,
    redirect_stdout_stderr,
    
    # Email utilities
    EmailNotifier,
    
    # Pushover utilities
    PushoverNotifier,
    
    # Validation utilities
    BackupCheckConfig,
    AppConfig,
    validate_size_string_simple,
    validate_email_simple,
)


def demo_size_utilities():
    """Demonstrate size parsing and formatting utilities."""
    print("=== Size Utilities Demo ===")
    
    # Parse various size formats
    sizes = ["10 GB", "1.5 TB", "500MB", "256 kb", "1024 B"]
    
    for size_str in sizes:
        if validate_size_string(size_str):
            bytes_val = parse_size_to_bytes(size_str)
            formatted_back = bytes_to_human_readable(bytes_val)
            print(f"{size_str:>8} = {bytes_val:>15,} bytes = {formatted_back}")
        else:
            print(f"{size_str:>8} = INVALID FORMAT")
    
    print()


def demo_filesystem_utilities():
    """Demonstrate filesystem operation utilities."""
    print("=== Filesystem Utilities Demo ===")
    
    # Test current directory (should be accessible)
    test_dir = "."
    print(f"Testing directory: {Path(test_dir).resolve()}")
    
    # Check accessibility
    accessible = is_directory_accessible(test_dir)
    print(f"Directory accessible: {accessible}")
    
    if accessible:
        # Get disk usage
        total, used, free = get_disk_usage(test_dir)
        print(f"Disk usage:")
        print(f"  Total: {bytes_to_human_readable(total)}")
        print(f"  Used:  {bytes_to_human_readable(used)}")
        print(f"  Free:  {bytes_to_human_readable(free)}")
        
        # Check minimum free space (1 GB)
        min_space = parse_size_to_bytes("1 GB")
        has_space, message = check_minimum_free_space(test_dir, min_space)
        print(f"Has 1 GB free: {has_space}")
        if not has_space:
            print(f"  {message}")
        
        # Find recent files
        recent_files = get_files_modified_within_days(test_dir, days=7)
        print(f"Files modified in last 7 days: {len(recent_files)}")
        if recent_files:
            # Show first few files
            for filename, size, mtime in recent_files[:3]:
                print(f"  {filename}: {bytes_to_human_readable(size)}")
    
    print()


def demo_logging_utilities():
    """Demonstrate logging utilities."""
    print("=== Logging Utilities Demo ===")
    
    # Setup basic logging
    logger = setup_backup_logging("demo_app", log_dir=".", redirect_streams=False)
    logger.info("Demo logging started")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Custom logger setup
    custom_logger = logging.getLogger("custom_demo")
    setup_logger(
        custom_logger,
        log_filename="demo_custom.log",
        level=logging.DEBUG,
        handler_config="default",
        formatter_config="detailed"
    )
    
    custom_logger.debug("Debug message from custom logger")
    custom_logger.info("Info message from custom logger")
    
    print("Logging examples written to demo_app.log and demo_custom.log")
    print()


def demo_email_utilities():
    """Demonstrate email utilities (without actually sending)."""
    print("=== Email Utilities Demo ===")
    
    try:
        # Initialize email notifier (will fail gracefully if no config)
        notifier = EmailNotifier()
        print("EmailNotifier initialized successfully")
        
        # Create a sample backup summary
        backup_results = [
            {"name": "database", "success": True, "total_size_human": "2.1 GB"},
            {"name": "files", "success": True, "total_size_human": "1.5 GB"},
            {"name": "config", "success": False, "error": "Directory not accessible"}
        ]
        
        errors = ["Backup drive mounted read-only"]
        
        subject, content = notifier.create_backup_summary_email(
            backup_results, errors, duration=15.7
        )
        
        print(f"Generated email subject: {subject}")
        print("Generated email content:")
        print("-" * 40)
        print(content[:300] + "..." if len(content) > 300 else content)
        print("-" * 40)
        
    except Exception as e:
        print(f"Email demo failed (expected if no SMTP config): {e}")
    
    print()


def demo_pushover_utilities():
    """Demonstrate pushover utilities (without actually sending)."""
    print("=== Pushover Utilities Demo ===")
    
    try:
        # Initialize pushover notifier
        notifier = PushoverNotifier("Demo App")
        print(f"PushoverNotifier initialized (valid credentials: {notifier._valid_credentials})")
        
        # Test parameter validation
        test_message = "Test notification message"
        print(f"Original message: '{test_message}'")
        
        validated_message = notifier._validate_message(test_message)
        print(f"Validated message: '{validated_message}'")
        
        priority, corrected = notifier._validate_priority(5)  # Invalid priority
        print(f"Priority validation: 5 -> {priority} (corrected: {corrected})")
        
        # Test backup-specific methods
        result = notifier.send_backup_alert("test_backup", "Connection timeout")
        print(f"Backup alert result: {result}")
        
        result = notifier.send_backup_summary(3, 2, 1, 25.3)
        print(f"Backup summary result: {result}")
        
    except Exception as e:
        print(f"Pushover demo failed: {e}")
    
    print()


def demo_validation_utilities():
    """Demonstrate configuration validation utilities."""
    print("=== Validation Utilities Demo ===")
    
    # Test simple validators
    test_cases = [
        ("10 GB", validate_size_string_simple),
        ("admin@example.com", validate_email_simple),
    ]
    
    for value, validator in test_cases:
        result = validator(value)
        print(f"{validator.__name__}('{value}') = {result}")
    
    # Test backup configuration validation
    try:
        backup_config = BackupCheckConfig(
            name="demo_backup",
            backup_dir="/tmp",
            days=7,
            min_size="5 GB"
        )
        
        print(f"BackupCheckConfig created successfully:")
        print(f"  Name: {backup_config.name}")
        print(f"  Directory: {backup_config.backup_dir}")
        print(f"  Days: {backup_config.days}")
        print(f"  Min size: {backup_config.min_size}")
        print(f"  Min size bytes: {backup_config.get_min_size_bytes():,}")
        
    except Exception as e:
        print(f"Configuration validation failed: {e}")
    
    print()


def main():
    """Run all demonstration functions."""
    print("Python Utils Library - Basic Usage Examples")
    print("=" * 50)
    print()
    
    # Run all demos
    demo_size_utilities()
    demo_filesystem_utilities()
    demo_logging_utilities()
    demo_email_utilities()
    demo_pushover_utilities()
    demo_validation_utilities()
    
    print("Demo completed successfully!")
    print()
    print("Check the generated log files:")
    print("  - demo_app.log")
    print("  - demo_custom.log")


if __name__ == "__main__":
    main()