"""
Logging utilities for backup monitoring applications.

Provides flexible logging setup with stdout/stderr redirection, file rotation,
and configurable formatting for reliable backup monitoring operations.

Based on MyLogger: https://github.com/igarreta/mylogger
"""

import logging
import logging.handlers
import datetime
import sys
from typing import Union, Dict, Any, Optional
from pathlib import Path


class LoggingError(Exception):
    """Raised when logging configuration fails."""
    pass


# Predefined handler configurations for TimedRotatingFileHandler
HANDLER_CONFIGURATIONS: Dict[str, Dict[str, Any]] = {
    'default': {
        'when': 'W0',  # Weekly rotation on Monday
        'atTime': datetime.time(0, 0, 0),  # At midnight
        'backupCount': 4  # Keep 4 backup files
    },
    'weekly_4': {
        'when': 'W0',  # Weekly rotation on Monday
        'atTime': datetime.time(0, 0, 0),  # At midnight
        'backupCount': 4  # Keep 4 backup files
    },
    'daily_7': {
        'when': 'D',  # Daily rotation
        'atTime': datetime.time(2, 0, 0),  # At 2 AM
        'backupCount': 7  # Keep 7 days of backups
    },
    'monthly_12': {
        'when': 'M',  # Monthly rotation
        'interval': 1,  # Every month
        'backupCount': 12  # Keep 12 months of backups
    }
}

# Predefined formatter configurations
FORMATTER_CONFIGURATIONS: Dict[str, str] = {
    'default': '%(asctime)s %(levelname)-8s %(message)s',
    'detailed': '%(asctime)s [%(name)s] %(levelname)-8s %(funcName)s:%(lineno)d - %(message)s',
    'simple': '%(levelname)s: %(message)s',
    'backup_monitor': '%(asctime)s [BACKUP] %(levelname)-8s %(message)s'
}


class StreamLogger:
    """A custom logging class that redirects stdout/stderr to log files.
    
    This class provides stream redirection functionality, capturing stdout and stderr
    and routing them to log files with appropriate filtering and formatting.
    
    Features:
    - Automatic empty line filtering
    - Configurable log levels for different streams
    - Compatible with Python's file-like object interface
    - Thread-safe operation
    """
    
    def __init__(self, logger: logging.Logger, level: int = logging.INFO) -> None:
        """Initialize StreamLogger with a logger instance and log level.
        
        Args:
            logger: The logger instance to use for output
            level: The logging level for messages (e.g., logging.INFO, logging.ERROR)
            
        Example:
            >>> import logging
            >>> logger = logging.getLogger('backup_app')
            >>> setup_logger(logger, 'app.log')
            >>> sys.stdout = StreamLogger(logger, logging.INFO)
            >>> sys.stderr = StreamLogger(logger, logging.ERROR)
            >>> print("This goes to the log file")
        """
        self.logger = logger
        self.level = level
    
    def write(self, message: str) -> None:
        """Write a message to the logger.
        
        This method is called by Python's print() function and other stdout/stderr
        operations. It filters out empty lines and whitespace-only messages.
        
        Args:
            message: The message to log
            
        Note:
            Empty messages (after stripping whitespace) are ignored to prevent
            cluttering the log file with blank lines.
        """
        # Only log if there is a message (not just whitespace or newlines)
        if message.rstrip():
            # Prevent recursive logging cascade by detecting repeated error patterns
            if message.count("ERROR:__main__:") > 1:
                return
            self.logger.log(self.level, message.rstrip())
    
    def flush(self) -> None:
        """Flush the logger output.
        
        This method is required for compatibility with Python's file-like object
        interface. It's called by sys.stdout.flush() and similar operations.
        
        Note:
            This is a no-op since logging handlers manage their own flushing.
        """
        pass
    
    def isatty(self) -> bool:
        """Return False to indicate this is not a terminal."""
        return False


def setup_logger(
    logger: logging.Logger,
    log_filename: str = "backup_monitor.log",
    level: int = logging.INFO,
    handler_config: Union[str, Dict[str, Any], logging.Handler] = 'default',
    formatter_config: Union[str, logging.Formatter] = 'default',
    create_dirs: bool = True
) -> None:
    """Configure a logger with rotating file handler and formatting.
    
    This function sets up a logger with a TimedRotatingFileHandler that rotates
    log files based on time intervals and maintains backup files.
    
    Args:
        logger: The logger instance to configure
        log_filename: Path to the log file (supports ~ expansion)
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        handler_config: Handler configuration:
            - str: Key from HANDLER_CONFIGURATIONS ('default', 'daily_7', etc.)
            - dict: Parameters for TimedRotatingFileHandler
            - logging.Handler: Pre-configured handler instance
        formatter_config: Formatter configuration:
            - str: Key from FORMATTER_CONFIGURATIONS ('default', 'detailed', etc.)
            - logging.Formatter: Pre-configured formatter instance
        create_dirs: Whether to create parent directories if they don't exist
        
    Raises:
        LoggingError: If configuration fails or invalid parameters provided
        
    Example:
        Basic setup:
        >>> import logging
        >>> logger = logging.getLogger('backup_app')
        >>> setup_logger(logger, 'log/backup.log', logging.DEBUG)
        
        Daily rotation with detailed formatting:
        >>> setup_logger(
        ...     logger, 
        ...     'log/backup_daily.log',
        ...     handler_config='daily_7',
        ...     formatter_config='detailed'
        ... )
        
        Custom configuration:
        >>> custom_handler = {
        ...     'when': 'H',  # Hourly rotation
        ...     'interval': 6,  # Every 6 hours
        ...     'backupCount': 48  # Keep 12 days of backups
        ... }
        >>> setup_logger(logger, 'log/hourly.log', handler_config=custom_handler)
    """
    try:
        # Expand user path and create directories if needed
        log_path = Path(log_filename).expanduser()
        
        if create_dirs:
            log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Process handler configuration
        if isinstance(handler_config, str):
            if handler_config not in HANDLER_CONFIGURATIONS:
                available = list(HANDLER_CONFIGURATIONS.keys())
                raise LoggingError(f"Handler '{handler_config}' not found. Available: {available}")
            handler_params = HANDLER_CONFIGURATIONS[handler_config]
            handler = logging.handlers.TimedRotatingFileHandler(str(log_path), **handler_params)
        elif isinstance(handler_config, dict):
            handler = logging.handlers.TimedRotatingFileHandler(str(log_path), **handler_config)
        elif isinstance(handler_config, logging.Handler):
            handler = handler_config
        else:
            raise LoggingError(f"Invalid handler_config type: {type(handler_config)}")
        
        # Process formatter configuration
        if isinstance(formatter_config, str):
            if formatter_config not in FORMATTER_CONFIGURATIONS:
                available = list(FORMATTER_CONFIGURATIONS.keys())
                raise LoggingError(f"Formatter '{formatter_config}' not found. Available: {available}")
            formatter_str = FORMATTER_CONFIGURATIONS[formatter_config]
            formatter = logging.Formatter(formatter_str)
        elif isinstance(formatter_config, logging.Formatter):
            formatter = formatter_config
        else:
            raise LoggingError(f"Invalid formatter_config type: {type(formatter_config)}")
        
        # Configure logger
        logger.setLevel(level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Prevent duplicate messages in parent loggers
        logger.propagate = False
        
    except Exception as e:
        raise LoggingError(f"Failed to setup logger: {e}") from e


def redirect_stdout_stderr(
    logger: logging.Logger,
    stdout_level: int = logging.INFO,
    stderr_level: int = logging.ERROR
) -> tuple[StreamLogger, StreamLogger]:
    """Redirect stdout and stderr to logger streams.
    
    Args:
        logger: Logger instance to redirect to
        stdout_level: Log level for stdout messages
        stderr_level: Log level for stderr messages
        
    Returns:
        Tuple of (stdout_logger, stderr_logger) for potential restoration
        
    Example:
        >>> import logging
        >>> logger = logging.getLogger('backup_app')
        >>> setup_logger(logger, 'log/backup.log')
        >>> old_stdout, old_stderr = redirect_stdout_stderr(logger)
        >>> print("This goes to the log file")
        >>> print("Error message", file=sys.stderr)  # Goes to log as ERROR
    """
    stdout_logger = StreamLogger(logger, stdout_level)
    stderr_logger = StreamLogger(logger, stderr_level)
    
    # Store original streams for potential restoration
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    # Redirect streams
    sys.stdout = stdout_logger
    sys.stderr = stderr_logger
    
    return stdout_logger, stderr_logger


def restore_stdout_stderr(original_stdout=None, original_stderr=None) -> None:
    """Restore original stdout and stderr streams.
    
    Args:
        original_stdout: Original stdout stream (uses sys.__stdout__ if None)
        original_stderr: Original stderr stream (uses sys.__stderr__ if None)
    """
    sys.stdout = original_stdout or sys.__stdout__
    sys.stderr = original_stderr or sys.__stderr__


def setup_backup_logging(
    app_name: str = "backup_monitor",
    log_dir: str = "log",
    log_level: str = "INFO",
    redirect_streams: bool = True,
    rotation: str = "weekly_4"
) -> logging.Logger:
    """Convenience function to setup logging for backup monitoring applications.
    
    Args:
        app_name: Name of the application (used for logger name and log filename)
        log_dir: Directory for log files (relative to current working directory)
        log_level: Logging level as string ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        redirect_streams: Whether to redirect stdout/stderr to log file
        rotation: Handler configuration name for log rotation
        
    Returns:
        Configured logger instance
        
    Raises:
        LoggingError: If logging setup fails
        
    Example:
        >>> logger = setup_backup_logging('proxmox_backup_checker')
        >>> logger.info("Backup check started")
        >>> print("This also goes to the log")  # Due to redirect_streams=True
    """
    try:
        # Convert log level string to constant
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Create logger
        logger = logging.getLogger(app_name)
        
        # Setup file logging
        log_filename = f"{log_dir}/{app_name}.log"
        setup_logger(
            logger,
            log_filename,
            level=numeric_level,
            handler_config=rotation,
            formatter_config='backup_monitor'
        )
        
        # Redirect stdout/stderr if requested
        if redirect_streams:
            redirect_stdout_stderr(logger)
        
        logger.info(f"Logging initialized for {app_name}")
        logger.info(f"Log file: {Path(log_filename).resolve()}")
        logger.info(f"Log level: {log_level}")
        logger.info(f"Rotation: {rotation}")
        
        return logger
        
    except Exception as e:
        raise LoggingError(f"Failed to setup backup logging: {e}") from e


def get_log_info(logger: logging.Logger) -> Dict[str, Any]:
    """Get information about a logger's configuration.
    
    Args:
        logger: Logger instance to inspect
        
    Returns:
        Dictionary with logger information
    """
    handlers = []
    for handler in logger.handlers:
        handler_info = {
            'type': type(handler).__name__,
            'level': logging.getLevelName(handler.level) if hasattr(handler, 'level') else 'UNSET'
        }
        
        if hasattr(handler, 'baseFilename'):
            handler_info['filename'] = handler.baseFilename
        
        if hasattr(handler, 'when'):
            handler_info['rotation'] = f"{handler.when} every {getattr(handler, 'interval', 1)}"
            handler_info['backup_count'] = getattr(handler, 'backupCount', 0)
        
        handlers.append(handler_info)
    
    return {
        'name': logger.name,
        'level': logging.getLevelName(logger.level),
        'propagate': logger.propagate,
        'handlers': handlers,
        'effective_level': logging.getLevelName(logger.getEffectiveLevel())
    }
