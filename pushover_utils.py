"""
Pushover notification utilities for backup monitoring alerts.

Provides reliable push notifications via Pushover.net API with automatic
error correction, credential validation, and logging integration.
"""

import os
import requests
from pathlib import Path
from typing import Optional, Union, Dict, Any
import logging
from dotenv import load_dotenv


class PushoverError(Exception):
    """Raised when Pushover configuration or API errors occur."""
    pass


class PushoverNotifier:
    """Pushover.net API client for sending push notifications.
    
    This class provides a reliable interface to send push notifications
    using the Pushover.net service with automatic error correction,
    credential validation, and comprehensive logging.
    
    Features:
    - Exception-safe initialization and operation
    - Automatic parameter correction (length limits, priority ranges)
    - Credential validation with clear error reporting
    - Support for all Pushover priority levels including emergency
    - Integration with dotenv for credential management
    """
    
    def __init__(
        self, 
        title: str = "Backup Monitor", 
        env_file: Union[str, Path] = "~/etc/pushover.env",
        device: str = "default",
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialize Pushover client with credentials from environment file.
        
        Args:
            title: Default title for notifications
            env_file: Path to environment file containing PUSHOVER_TOKEN and PUSHOVER_USER
            device: Target device name (optional)
            logger: Optional logger instance for error reporting
            
        Note:
            This constructor never raises exceptions. Invalid configurations are logged
            and will cause send() to return False.
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Auto-correct title
        self.title = self._validate_title(title)
        self.device = device
        
        # Load credentials safely
        self._valid_credentials = False
        self.token = "invalid_token"
        self.user = "invalid_user"
        
        try:
            self._load_credentials(env_file)
        except Exception as e:
            self.logger.error(f"Failed to load Pushover credentials: {e}")
        
        if self._valid_credentials:
            self.logger.info("Pushover client initialized successfully")
        else:
            self.logger.warning("Pushover client initialized with invalid credentials - send() will fail")
    
    def _load_credentials(self, env_file: Union[str, Path]) -> None:
        """Load credentials from environment file using dotenv."""
        # Expand user path
        env_path = os.path.expanduser(str(env_file))
        
        if not os.path.exists(env_path):
            self.logger.warning(f"Pushover environment file not found: {env_path}")
            return
        
        # Load environment variables
        if not load_dotenv(env_path, override=True):
            self.logger.warning(f"Failed to load dotenv from {env_path}")
        
        # Get credentials
        token = os.environ.get('PUSHOVER_TOKEN')
        user = os.environ.get('PUSHOVER_USER')
        
        # Validate token format (30 characters for Pushover)
        if not token or len(token) != 30:
            self.logger.error("Invalid PUSHOVER_TOKEN format (expected 30 characters)")
            return
        
        if not user or len(user) != 30:
            self.logger.error("Invalid PUSHOVER_USER format (expected 30 characters)")  
            return
        
        self.token = token
        self.user = user
        self._valid_credentials = True
    
    def _validate_title(self, title: str) -> str:
        """Validate and correct title format."""
        if not isinstance(title, str):
            title = str(title)
            self.logger.warning("Title converted to string")
        
        if len(title) > 250:
            title = title[:230] + " [TRUNCATED]"
            self.logger.warning("Title truncated to fit 250 character limit")
        
        return title
    
    def _validate_message(self, message: str) -> str:
        """Validate and correct message format."""
        if not isinstance(message, str):
            message = str(message)
            self.logger.warning("Message converted to string")
        
        if len(message) > 1024:
            message = message[:1010] + " [TRUNCATED]"
            self.logger.warning("Message truncated to fit 1024 character limit")
        
        return message
    
    def _validate_priority(self, priority: Optional[int]) -> tuple[int, bool]:
        """Validate and correct priority value.
        
        Returns:
            Tuple of (corrected_priority, was_corrected)
        """
        if priority is None:
            return 0, False
        
        if not isinstance(priority, int) or not (-2 <= priority <= 2):
            self.logger.warning(f"Invalid priority {priority} corrected to -1 (low priority)")
            return -1, True
        
        return priority, False
    
    def send(
        self, 
        message: str, 
        priority: Optional[int] = None, 
        title: Optional[str] = None,
        retry: int = 600, 
        expire: int = 7200
    ) -> bool:
        """Send a push notification via Pushover API.
        
        Args:
            message: The message text to send (auto-truncated if >1024 characters)
            priority: Priority level (-2 to 2, auto-corrected if invalid)
            title: Custom title for this message (uses default if None)
            retry: How often (in seconds) to retry emergency notifications
            expire: How many seconds emergency notifications will retry
            
        Returns:
            bool: True if message sent successfully, False otherwise
            
        Priority levels:
            -2: Lowest priority (no notification)
            -1: Low priority (quiet notification)
             0: Normal priority (default)
             1: High priority (bypass quiet hours) 
             2: Emergency priority (requires acknowledgment)
             
        Note:
            This method never raises exceptions. Invalid parameters are auto-corrected
            and logged. Network/API errors are logged and return False.
        """
        # Check credentials first
        if not self._valid_credentials:
            self.logger.error("Cannot send notification: invalid credentials")
            return False
        
        # Validate and correct parameters
        message = self._validate_message(message)
        priority, was_corrected = self._validate_priority(priority)
        
        # Use provided title or default
        notification_title = self._validate_title(title) if title else self.title
        
        # Auto-correct retry and expire for emergency priority
        if priority == 2:
            if retry < 30:
                retry = 30
                self.logger.warning("Emergency retry interval corrected to minimum 30 seconds")
            if expire > 10800:
                expire = 10800
                self.logger.warning("Emergency expire time corrected to maximum 10800 seconds")
        
        # Add correction note to message if needed
        if was_corrected:
            message += " [Priority auto-corrected]"
        
        # Prepare API payload
        payload = {
            "token": self.token,
            "user": self.user,
            "message": message,
            "title": notification_title,
            "priority": priority,
            "device": self.device
        }
        
        # Add emergency parameters if needed
        if priority == 2:
            payload["retry"] = retry
            payload["expire"] = expire
        
        # Send notification
        try:
            response = requests.post(
                "https://api.pushover.net/1/messages.json",
                data=payload,
                timeout=30
            )
            response.raise_for_status()
            
            # Parse and validate response
            try:
                result = response.json()
                if result.get('status') == 1:
                    self.logger.info(f"Pushover notification sent successfully: {response.status_code}")
                    if 'receipt' in result:
                        self.logger.info(f"Emergency notification receipt: {result['receipt']}")
                    return True
                else:
                    errors = result.get('errors', ['Unknown error'])
                    self.logger.error(f"Pushover API error: {', '.join(errors)}")
                    return False
            except ValueError:
                # Response is not JSON, but HTTP status was OK
                self.logger.info(f"Pushover notification sent successfully: {response.status_code}")
                return True
                
        except requests.exceptions.Timeout:
            self.logger.error("Pushover notification timeout after 30 seconds")
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send Pushover notification: {e}")
            return False
    
    def send_backup_alert(
        self, 
        backup_name: str, 
        error_message: str, 
        priority: int = 1
    ) -> bool:
        """Send a backup-specific alert notification.
        
        Args:
            backup_name: Name of the backup that failed
            error_message: Description of the error
            priority: Notification priority (default: high priority)
            
        Returns:
            bool: True if notification sent successfully
        """
        title = f"Backup Alert: {backup_name}"
        message = f"Backup '{backup_name}' encountered an issue:\n{error_message}"
        
        return self.send(message, priority=priority, title=title)
    
    def send_backup_summary(
        self, 
        total_backups: int, 
        successful_backups: int, 
        failed_backups: int,
        duration: float,
        priority: int = -1
    ) -> bool:
        """Send a backup summary notification.
        
        Args:
            total_backups: Total number of backups checked
            successful_backups: Number of successful backups
            failed_backups: Number of failed backups  
            duration: Total check duration in seconds
            priority: Notification priority (default: low priority)
            
        Returns:
            bool: True if notification sent successfully
        """
        if failed_backups > 0:
            status_emoji = "❌"
            title = "Backup Check: Issues Detected"
            priority = 1  # High priority for failures
        else:
            status_emoji = "✅"
            title = "Backup Check: All OK"
        
        message = (
            f"{status_emoji} Backup Check Complete\n"
            f"Total: {total_backups}, Success: {successful_backups}, Failed: {failed_backups}\n"
            f"Duration: {duration:.1f}s"
        )
        
        return self.send(message, priority=priority, title=title)
    
    def test_notification(self) -> bool:
        """Send a test notification to verify configuration.
        
        Returns:
            bool: True if test notification sent successfully
        """
        return self.send(
            "Test notification from Proxmox Backup Checker",
            priority=-1,
            title="Test Notification"
        )


def send_critical_backup_alert(
    message: str, 
    env_file: str = "~/etc/pushover.env",
    logger: Optional[logging.Logger] = None
) -> bool:
    """Convenience function to send a critical backup alert.
    
    Args:
        message: Alert message to send
        env_file: Path to Pushover credentials file
        logger: Optional logger for error reporting
        
    Returns:
        bool: True if notification sent successfully
    """
    try:
        notifier = PushoverNotifier("Critical Backup Alert", env_file, logger=logger)
        return notifier.send(message, priority=2)  # Emergency priority
    except Exception as e:
        if logger:
            logger.error(f"Failed to send critical backup alert: {e}")
        return False