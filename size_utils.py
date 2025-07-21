"""
Size parsing and conversion utilities for backup monitoring.

Handles conversion between human-readable size strings and bytes,
supporting decimal values and various units (B, KB, MB, GB, TB).
"""

import re
from typing import Dict


class InvalidSizeFormatError(ValueError):
    """Raised when size string format is invalid or cannot be parsed."""
    pass


# Size unit multipliers (binary: 1 KB = 1024 bytes)
SIZE_UNITS: Dict[str, int] = {
    'B': 1,
    'KB': 1024,
    'MB': 1024 ** 2,
    'GB': 1024 ** 3,
    'TB': 1024 ** 4,
}

# Ordered units for human-readable conversion
UNIT_ORDER = ['TB', 'GB', 'MB', 'KB', 'B']


def parse_size_to_bytes(size_str: str) -> int:
    """
    Convert human-readable size string to bytes.
    
    Args:
        size_str: Size string like "10 GB", "500MB", "1.5 TB", "100 kb"
                 Case insensitive, spaces optional
    
    Returns:
        Integer number of bytes
        
    Raises:
        InvalidSizeFormatError: If format is invalid or unsupported unit
        
    Examples:
        >>> parse_size_to_bytes("10 GB")
        10737418240
        >>> parse_size_to_bytes("1.5TB")
        1649267441664
        >>> parse_size_to_bytes("100kb")
        102400
    """
    if not isinstance(size_str, str):
        raise InvalidSizeFormatError(f"Size must be string, got {type(size_str)}")
    
    # Clean and normalize input
    size_str = size_str.strip().upper()
    
    if not size_str:
        raise InvalidSizeFormatError("Size string cannot be empty")
    
    # Pattern to match: number (with optional decimal) + optional space + unit
    pattern = r'^(\d+(?:\.\d+)?)\s*([KMGT]?B)$'
    match = re.match(pattern, size_str)
    
    if not match:
        raise InvalidSizeFormatError(f"Invalid size format: '{size_str}'. Expected format like '10 GB', '1.5TB', '500MB'")
    
    value_str, unit = match.groups()
    
    try:
        value = float(value_str)
    except ValueError:
        raise InvalidSizeFormatError(f"Invalid numeric value: '{value_str}'")
    
    if value < 0:
        raise InvalidSizeFormatError(f"Size cannot be negative: {value}")
    
    if unit not in SIZE_UNITS:
        raise InvalidSizeFormatError(f"Unsupported unit: '{unit}'. Supported: {list(SIZE_UNITS.keys())}")
    
    # Convert to bytes and return as integer
    bytes_value = value * SIZE_UNITS[unit]
    
    # Check for overflow (Python int can handle very large numbers, but be reasonable)
    if bytes_value > 1024 ** 5:  # More than 1 PB
        raise InvalidSizeFormatError(f"Size too large: {size_str}")
    
    return int(bytes_value)


def bytes_to_human_readable(bytes_count: int, decimal_places: int = 1) -> str:
    """
    Convert bytes to human-readable size string.
    
    Args:
        bytes_count: Number of bytes
        decimal_places: Number of decimal places to show (default: 1)
    
    Returns:
        Human-readable size string
        
    Examples:
        >>> bytes_to_human_readable(1073741824)
        '1.0 GB'
        >>> bytes_to_human_readable(1536)
        '1.5 KB'
        >>> bytes_to_human_readable(512)
        '512 B'
    """
    if not isinstance(bytes_count, (int, float)):
        raise InvalidSizeFormatError(f"Bytes count must be numeric, got {type(bytes_count)}")
    
    if bytes_count < 0:
        raise InvalidSizeFormatError(f"Bytes count cannot be negative: {bytes_count}")
    
    bytes_count = int(bytes_count)
    
    if bytes_count == 0:
        return "0 B"
    
    # Find the appropriate unit
    for unit in UNIT_ORDER:
        unit_size = SIZE_UNITS[unit]
        if bytes_count >= unit_size:
            value = bytes_count / unit_size
            # Format with specified decimal places, but remove trailing zeros
            formatted = f"{value:.{decimal_places}f}".rstrip('0').rstrip('.')
            return f"{formatted} {unit}"
    
    # Should never reach here, but fallback to bytes
    return f"{bytes_count} B"


def validate_size_string(size_str: str) -> bool:
    """
    Validate size string format without conversion.
    
    Args:
        size_str: Size string to validate
        
    Returns:
        True if valid format, False otherwise
        
    Examples:
        >>> validate_size_string("10 GB")
        True
        >>> validate_size_string("invalid")
        False
        >>> validate_size_string("1.5TB")
        True
    """
    try:
        parse_size_to_bytes(size_str)
        return True
    except InvalidSizeFormatError:
        return False