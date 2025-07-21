"""
Filesystem utilities for backup monitoring operations.

Provides secure and efficient filesystem operations including mount checking,
disk space analysis, and file age scanning for backup validation systems.
"""

import os
import shutil
import stat
import time
from typing import List, Tuple, Optional
from pathlib import Path
import logging
from datetime import datetime, timedelta


class FilesystemError(Exception):
    """Raised when filesystem operations fail."""
    pass


def is_directory_accessible(path: str, logger: Optional[logging.Logger] = None) -> bool:
    """
    Check if backup directory is mounted, accessible, and readable.
    
    Args:
        path: Directory path to check
        logger: Optional logger for detailed error reporting
        
    Returns:
        True if directory is accessible, False otherwise
        
    Examples:
        >>> is_directory_accessible("/mnt/backup")
        True
        >>> is_directory_accessible("/nonexistent")
        False
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        # Expand user path and resolve symlinks
        full_path = Path(path).expanduser().resolve()
        
        # Check if path exists
        if not full_path.exists():
            logger.warning(f"Directory does not exist: {path}")
            return False
        
        # Check if it's actually a directory
        if not full_path.is_dir():
            logger.warning(f"Path is not a directory: {path}")
            return False
        
        # Test read access by attempting to list contents
        try:
            # This will raise PermissionError if not readable
            list(full_path.iterdir())
        except PermissionError:
            logger.warning(f"Directory not readable (permission denied): {path}")
            return False
        except OSError as e:
            logger.warning(f"Directory not accessible (OS error): {path} - {e}")
            return False
        
        # Additional check for mount points (Linux/Unix)
        if hasattr(os, 'statvfs'):
            try:
                os.statvfs(str(full_path))
            except OSError as e:
                logger.warning(f"Directory mount issue: {path} - {e}")
                return False
        
        logger.debug(f"Directory accessible: {path}")
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error checking directory accessibility: {path} - {e}")
        return False


def get_disk_usage(path: str, logger: Optional[logging.Logger] = None) -> Tuple[int, int, int]:
    """
    Get disk usage statistics for a given path.
    
    Args:
        path: Directory path to analyze
        logger: Optional logger for error reporting
        
    Returns:
        Tuple of (total_bytes, used_bytes, free_bytes)
        Returns (0, 0, 0) if path is not accessible
        
    Raises:
        FilesystemError: If disk usage cannot be determined
        
    Examples:
        >>> total, used, free = get_disk_usage("/mnt/backup")
        >>> print(f"Free space: {free / (1024**3):.1f} GB")
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        # Expand and resolve path
        full_path = Path(path).expanduser().resolve()
        
        # Check if path is accessible first
        if not is_directory_accessible(str(full_path), logger):
            logger.error(f"Cannot get disk usage - path not accessible: {path}")
            return (0, 0, 0)
        
        # Get disk usage using shutil (cross-platform)
        total, used, free = shutil.disk_usage(str(full_path))
        
        logger.debug(f"Disk usage for {path}: total={total}, used={used}, free={free}")
        return (total, used, free)
        
    except OSError as e:
        logger.error(f"OS error getting disk usage for {path}: {e}")
        raise FilesystemError(f"Failed to get disk usage for {path}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error getting disk usage for {path}: {e}")
        raise FilesystemError(f"Unexpected error getting disk usage for {path}: {e}")


def get_files_modified_within_days(
    directory: str, 
    days: int, 
    include_subdirs: bool = False,
    logger: Optional[logging.Logger] = None
) -> List[Tuple[str, int, float]]:
    """
    Find files modified within specified number of days.
    
    Args:
        directory: Directory path to scan
        days: Maximum age in days
        include_subdirs: Whether to scan subdirectories recursively
        logger: Optional logger for error reporting
        
    Returns:
        List of tuples: (filename, size_bytes, modification_timestamp)
        Returns empty list if directory not accessible
        
    Examples:
        >>> files = get_files_modified_within_days("/mnt/backup", 7)
        >>> total_size = sum(size for _, size, _ in files)
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        # Expand and resolve path
        full_path = Path(directory).expanduser().resolve()
        
        # Check if directory is accessible
        if not is_directory_accessible(str(full_path), logger):
            logger.error(f"Cannot scan files - directory not accessible: {directory}")
            return []
        
        # Calculate cutoff time
        cutoff_time = time.time() - (days * 24 * 3600)
        recent_files = []
        
        # Scan files
        try:
            if include_subdirs:
                # Recursive scan
                for item in full_path.rglob('*'):
                    if item.is_file():
                        file_info = _get_file_info(item, cutoff_time, logger)
                        if file_info:
                            recent_files.append(file_info)
            else:
                # Top-level only scan
                for item in full_path.iterdir():
                    if item.is_file():
                        file_info = _get_file_info(item, cutoff_time, logger)
                        if file_info:
                            recent_files.append(file_info)
        
        except PermissionError as e:
            logger.error(f"Permission denied scanning directory {directory}: {e}")
            return []
        except OSError as e:
            logger.error(f"OS error scanning directory {directory}: {e}")
            return []
        
        logger.debug(f"Found {len(recent_files)} files modified within {days} days in {directory}")
        return recent_files
        
    except Exception as e:
        logger.error(f"Unexpected error scanning files in {directory}: {e}")
        return []


def _get_file_info(
    file_path: Path, 
    cutoff_time: float, 
    logger: logging.Logger
) -> Optional[Tuple[str, int, float]]:
    """
    Get file information if modified after cutoff time.
    
    Args:
        file_path: Path object for the file
        cutoff_time: Unix timestamp cutoff
        logger: Logger for error reporting
        
    Returns:
        Tuple of (filename, size, mtime) or None if too old or error
    """
    try:
        stat_result = file_path.stat()
        mtime = stat_result.st_mtime
        
        # Check if file was modified recently enough
        if mtime >= cutoff_time:
            size = stat_result.st_size
            return (file_path.name, size, mtime)
        
        return None
        
    except (OSError, PermissionError) as e:
        logger.warning(f"Cannot stat file {file_path}: {e}")
        return None


def calculate_total_size(file_list: List[Tuple[str, int, float]]) -> int:
    """
    Calculate total size of files from file info list.
    
    Args:
        file_list: List of (filename, size_bytes, mtime) tuples
        
    Returns:
        Total size in bytes
        
    Examples:
        >>> files = [("backup1.tar", 1000, 123456), ("backup2.tar", 2000, 123457)]
        >>> total = calculate_total_size(files)
        >>> assert total == 3000
    """
    if not file_list:
        return 0
    
    try:
        return sum(size for _, size, _ in file_list)
    except (TypeError, ValueError) as e:
        logging.getLogger(__name__).error(f"Error calculating total size: {e}")
        return 0


def format_disk_usage(total: int, used: int, free: int) -> str:
    """
    Format disk usage statistics as human-readable string.
    
    Args:
        total: Total disk space in bytes
        used: Used disk space in bytes  
        free: Free disk space in bytes
        
    Returns:
        Formatted string with sizes and percentage
        
    Examples:
        >>> usage_str = format_disk_usage(1000000000, 600000000, 400000000)
        >>> print(usage_str)
        "953.7 MB total, 572.2 MB used (60.0%), 381.5 MB free"
    """
    try:
        # Import size formatting from our utils
        from .size_utils import bytes_to_human_readable
        
        if total == 0:
            return "Disk usage unavailable"
        
        # Calculate usage percentage
        used_percent = (used / total) * 100 if total > 0 else 0
        
        # Format components
        total_str = bytes_to_human_readable(total)
        used_str = bytes_to_human_readable(used)  
        free_str = bytes_to_human_readable(free)
        
        return f"{total_str} total, {used_str} used ({used_percent:.1f}%), {free_str} free"
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error formatting disk usage: {e}")
        return f"Total: {total}, Used: {used}, Free: {free} (bytes)"


def check_minimum_free_space(path: str, min_free_bytes: int, logger: Optional[logging.Logger] = None) -> Tuple[bool, str]:
    """
    Check if directory has minimum required free space.
    
    Args:
        path: Directory path to check
        min_free_bytes: Minimum required free space in bytes
        logger: Optional logger for reporting
        
    Returns:
        Tuple of (has_enough_space, status_message)
        
    Examples:
        >>> has_space, msg = check_minimum_free_space("/mnt/backup", 10 * 1024**3)  # 10GB
        >>> if not has_space:
        ...     print(f"Warning: {msg}")
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        # Get disk usage
        total, used, free = get_disk_usage(path, logger)
        
        if total == 0:
            return False, f"Cannot determine disk usage for {path}"
        
        # Check if we have enough space
        has_enough = free >= min_free_bytes
        
        # Create status message
        from .size_utils import bytes_to_human_readable
        free_str = bytes_to_human_readable(free)
        required_str = bytes_to_human_readable(min_free_bytes)
        
        if has_enough:
            status = f"Sufficient free space: {free_str} available (required: {required_str})"
            logger.debug(status)
        else:
            status = f"Insufficient free space: {free_str} available, {required_str} required"
            logger.warning(status)
        
        return has_enough, status
        
    except FilesystemError as e:
        error_msg = f"Cannot check free space for {path}: {e}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error checking free space for {path}: {e}"
        logger.error(error_msg)
        return False, error_msg


def get_file_age_summary(file_list: List[Tuple[str, int, float]]) -> str:
    """
    Create summary of file ages from file list.
    
    Args:
        file_list: List of (filename, size_bytes, mtime) tuples
        
    Returns:
        Human-readable summary of file ages
        
    Examples:
        >>> files = get_files_modified_within_days("/backup", 7)  
        >>> summary = get_file_age_summary(files)
        >>> print(summary)  # "3 files: newest 1.2 hours ago, oldest 2.5 days ago"
    """
    if not file_list:
        return "No files found"
    
    try:
        current_time = time.time()
        
        # Calculate ages in seconds
        ages = [(current_time - mtime) for _, _, mtime in file_list]
        
        newest_age = min(ages)
        oldest_age = max(ages)
        
        def format_age(seconds: float) -> str:
            """Format age in appropriate units."""
            if seconds < 3600:  # Less than 1 hour
                return f"{seconds / 60:.1f} minutes ago"
            elif seconds < 86400:  # Less than 1 day
                return f"{seconds / 3600:.1f} hours ago"
            else:
                return f"{seconds / 86400:.1f} days ago"
        
        count = len(file_list)
        newest_str = format_age(newest_age)
        oldest_str = format_age(oldest_age)
        
        if count == 1:
            return f"1 file: modified {newest_str}"
        else:
            return f"{count} files: newest {newest_str}, oldest {oldest_str}"
            
    except Exception as e:
        logging.getLogger(__name__).error(f"Error creating file age summary: {e}")
        return f"{len(file_list)} files (age calculation failed)"