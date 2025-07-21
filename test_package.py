#!/usr/bin/env python3
"""
Quick test script to validate the python_utils package.
Run this to ensure all modules import and basic functionality works.
"""

def test_imports():
    """Test that all modules import correctly."""
    print("Testing imports...")
    
    try:
        from python_utils import (
            parse_size_to_bytes,
            bytes_to_human_readable,
            EmailNotifier, 
            PushoverNotifier,
            is_directory_accessible,
            setup_backup_logging,
            BackupCheckConfig,
            validate_size_string_simple
        )
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_basic_functionality():
    """Test basic functionality of each module."""
    print("\nTesting basic functionality...")
    
    # Test size utilities
    try:
        size = parse_size_to_bytes("10 GB")
        formatted = bytes_to_human_readable(size)
        assert size == 10737418240
        print(f"✅ Size utilities: 10 GB = {size} bytes = {formatted}")
    except Exception as e:
        print(f"❌ Size utilities failed: {e}")
        return False
    
    # Test filesystem utilities
    try:
        accessible = is_directory_accessible(".")
        assert accessible is True
        print("✅ Filesystem utilities: Directory access check works")
    except Exception as e:
        print(f"❌ Filesystem utilities failed: {e}")
        return False
    
    # Test validation utilities  
    try:
        backup = BackupCheckConfig(
            name="test",
            backup_dir="/tmp",
            days=1,
            min_size="1 GB"
        )
        assert backup.get_min_size_bytes() == 1073741824
        print("✅ Validation utilities: Configuration validation works")
    except Exception as e:
        print(f"❌ Validation utilities failed: {e}")
        return False
    
    # Test logging utilities
    try:
        import logging
        logger = setup_backup_logging("test_pkg", redirect_streams=False)
        logger.info("Test log message")
        print("✅ Logging utilities: Logger setup works")
    except Exception as e:
        print(f"❌ Logging utilities failed: {e}")
        return False
    
    # Test email utilities (initialization only)
    try:
        notifier = EmailNotifier()
        print("✅ Email utilities: Initialization works")
    except Exception as e:
        print(f"❌ Email utilities failed: {e}")
        return False
    
    # Test pushover utilities (initialization only)
    try:
        notifier = PushoverNotifier("Test")
        print("✅ Pushover utilities: Initialization works")
    except Exception as e:
        print(f"❌ Pushover utilities failed: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("Python Utils Package Test")
    print("=" * 30)
    
    if not test_imports():
        exit(1)
    
    if not test_basic_functionality():
        exit(1)
    
    print("\n🎉 All tests passed! Package is working correctly.")


if __name__ == "__main__":
    main()