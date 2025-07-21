"""
Comprehensive tests for size_utils module.

Tests cover normal cases, edge cases, error conditions, and round-trip conversions.
"""

import pytest
from .size_utils import (
    parse_size_to_bytes, 
    bytes_to_human_readable, 
    validate_size_string, 
    InvalidSizeFormatError
)


class TestParseSizeToBytes:
    """Test parse_size_to_bytes function."""
    
    def test_basic_parsing(self):
        """Test basic size string parsing."""
        assert parse_size_to_bytes("1024 B") == 1024
        assert parse_size_to_bytes("1 KB") == 1024
        assert parse_size_to_bytes("1 MB") == 1024 * 1024
        assert parse_size_to_bytes("1 GB") == 1024 * 1024 * 1024
        assert parse_size_to_bytes("1 TB") == 1024 * 1024 * 1024 * 1024
    
    def test_decimal_values(self):
        """Test parsing with decimal values."""
        assert parse_size_to_bytes("1.5 KB") == int(1.5 * 1024)
        assert parse_size_to_bytes("2.5 GB") == int(2.5 * 1024 * 1024 * 1024)
        assert parse_size_to_bytes("0.5 MB") == int(0.5 * 1024 * 1024)
    
    def test_case_insensitive(self):
        """Test case insensitive parsing."""
        assert parse_size_to_bytes("10 gb") == 10 * 1024 * 1024 * 1024
        assert parse_size_to_bytes("10 GB") == 10 * 1024 * 1024 * 1024
        assert parse_size_to_bytes("10 Gb") == 10 * 1024 * 1024 * 1024
        assert parse_size_to_bytes("10 kb") == 10 * 1024
    
    def test_no_space(self):
        """Test parsing without spaces."""
        assert parse_size_to_bytes("500MB") == 500 * 1024 * 1024
        assert parse_size_to_bytes("1GB") == 1024 * 1024 * 1024
        assert parse_size_to_bytes("10KB") == 10 * 1024
    
    def test_zero_value(self):
        """Test zero values."""
        assert parse_size_to_bytes("0 B") == 0
        assert parse_size_to_bytes("0 KB") == 0
        assert parse_size_to_bytes("0 GB") == 0
    
    def test_large_values(self):
        """Test large but reasonable values."""
        assert parse_size_to_bytes("100 TB") == 100 * 1024 * 1024 * 1024 * 1024
        assert parse_size_to_bytes("999 GB") == 999 * 1024 * 1024 * 1024
    
    def test_invalid_formats(self):
        """Test various invalid formats."""
        with pytest.raises(InvalidSizeFormatError):
            parse_size_to_bytes("invalid")
        
        with pytest.raises(InvalidSizeFormatError):
            parse_size_to_bytes("10 XB")  # Invalid unit
        
        with pytest.raises(InvalidSizeFormatError):
            parse_size_to_bytes("GB 10")  # Wrong order
        
        with pytest.raises(InvalidSizeFormatError):
            parse_size_to_bytes("")  # Empty string
        
        with pytest.raises(InvalidSizeFormatError):
            parse_size_to_bytes("   ")  # Only spaces
    
    def test_invalid_types(self):
        """Test non-string inputs."""
        with pytest.raises(InvalidSizeFormatError):
            parse_size_to_bytes(123)
        
        with pytest.raises(InvalidSizeFormatError):
            parse_size_to_bytes(None)
        
        with pytest.raises(InvalidSizeFormatError):
            parse_size_to_bytes(['10', 'GB'])
    
    def test_negative_values(self):
        """Test negative values are rejected."""
        with pytest.raises(InvalidSizeFormatError):
            parse_size_to_bytes("-10 GB")
        
        with pytest.raises(InvalidSizeFormatError):
            parse_size_to_bytes("-1 KB")
    
    def test_very_large_values(self):
        """Test extremely large values are rejected."""
        with pytest.raises(InvalidSizeFormatError):
            parse_size_to_bytes("9999999999999 TB")


class TestBytesToHumanReadable:
    """Test bytes_to_human_readable function."""
    
    def test_basic_conversion(self):
        """Test basic byte to string conversion."""
        assert bytes_to_human_readable(1024) == "1.0 KB"
        assert bytes_to_human_readable(1024 * 1024) == "1.0 MB"
        assert bytes_to_human_readable(1024 * 1024 * 1024) == "1.0 GB"
        assert bytes_to_human_readable(1024 * 1024 * 1024 * 1024) == "1.0 TB"
    
    def test_decimal_values(self):
        """Test conversion with decimal results."""
        assert bytes_to_human_readable(1536) == "1.5 KB"  # 1.5 * 1024
        assert bytes_to_human_readable(int(2.5 * 1024 * 1024)) == "2.5 MB"
    
    def test_small_values(self):
        """Test small values in bytes."""
        assert bytes_to_human_readable(512) == "512 B"
        assert bytes_to_human_readable(1) == "1 B"
        assert bytes_to_human_readable(0) == "0 B"
    
    def test_decimal_places(self):
        """Test custom decimal places."""
        value = int(1.2345 * 1024)
        assert bytes_to_human_readable(value, decimal_places=0) == "1 KB"
        assert bytes_to_human_readable(value, decimal_places=2) == "1.23 KB"
        assert bytes_to_human_readable(value, decimal_places=3) == "1.235 KB"
    
    def test_removes_trailing_zeros(self):
        """Test that trailing zeros are removed."""
        assert bytes_to_human_readable(1024, decimal_places=3) == "1 KB"
        assert bytes_to_human_readable(1024 * 1024, decimal_places=2) == "1 MB"
    
    def test_unit_selection(self):
        """Test appropriate unit selection."""
        # Should use TB for very large values
        large_value = 5 * 1024 * 1024 * 1024 * 1024
        result = bytes_to_human_readable(large_value)
        assert "TB" in result
        
        # Should use KB for medium values
        medium_value = 5 * 1024
        result = bytes_to_human_readable(medium_value)
        assert "KB" in result
    
    def test_invalid_inputs(self):
        """Test invalid input types."""
        with pytest.raises(InvalidSizeFormatError):
            bytes_to_human_readable("1024")
        
        with pytest.raises(InvalidSizeFormatError):
            bytes_to_human_readable(None)
        
        with pytest.raises(InvalidSizeFormatError):
            bytes_to_human_readable(-1024)


class TestValidateSizeString:
    """Test validate_size_string function."""
    
    def test_valid_strings(self):
        """Test validation of valid size strings."""
        assert validate_size_string("10 GB") is True
        assert validate_size_string("1.5 TB") is True
        assert validate_size_string("500MB") is True
        assert validate_size_string("0 B") is True
        assert validate_size_string("100 kb") is True
    
    def test_invalid_strings(self):
        """Test validation of invalid size strings."""
        assert validate_size_string("invalid") is False
        assert validate_size_string("10 XB") is False
        assert validate_size_string("GB 10") is False
        assert validate_size_string("") is False
        assert validate_size_string("-10 GB") is False


class TestRoundTripConversion:
    """Test round-trip conversions (parse -> convert back)."""
    
    def test_round_trip_exact(self):
        """Test round-trip for exact values."""
        test_cases = [
            "1 KB",
            "10 MB", 
            "5 GB",
            "2 TB"
        ]
        
        for original in test_cases:
            bytes_val = parse_size_to_bytes(original)
            converted_back = bytes_to_human_readable(bytes_val)
            # Should be equivalent (though format might differ slightly)
            assert validate_size_string(converted_back)
            assert parse_size_to_bytes(converted_back) == bytes_val
    
    def test_round_trip_decimal(self):
        """Test round-trip for decimal values."""
        original = "1.5 GB"
        bytes_val = parse_size_to_bytes(original)
        converted_back = bytes_to_human_readable(bytes_val)
        
        # Should be very close (within rounding error)
        bytes_back = parse_size_to_bytes(converted_back)
        assert abs(bytes_val - bytes_back) < 1024  # Within 1KB tolerance


# Integration test
def test_backup_checker_integration():
    """Test typical usage in backup checker context."""
    # Simulate config file values
    config_sizes = [
        "10 GB",  # Minimum backup size
        "100 GB",  # Minimum free space
        "500 MB"   # Small backup
    ]
    
    # Parse all sizes
    parsed_sizes = [parse_size_to_bytes(size) for size in config_sizes]
    
    # Verify reasonable values
    assert parsed_sizes[0] == 10 * 1024 * 1024 * 1024  # 10 GB
    assert parsed_sizes[1] == 100 * 1024 * 1024 * 1024  # 100 GB
    assert parsed_sizes[2] == 500 * 1024 * 1024  # 500 MB
    
    # Convert back for reporting
    human_sizes = [bytes_to_human_readable(size) for size in parsed_sizes]
    
    # Should be readable
    assert all("B" in size for size in human_sizes)
    assert all(validate_size_string(size) for size in human_sizes)