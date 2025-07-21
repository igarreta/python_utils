"""
Email notification utilities using smtplib for backup monitoring alerts.

Provides secure SMTP email functionality with proper error handling,
configuration management, and formatted notifications for backup systems.
"""

import smtplib
import ssl
import os
from typing import List, Union, Optional, Dict, Any, Tuple
from email.message import EmailMessage
from email.utils import formatdate
import logging
from datetime import datetime

from dotenv import load_dotenv


class EmailConfigError(Exception):
    """Raised when email configuration is invalid or missing."""
    pass


class EmailSendError(Exception):
    """Raised when email sending fails."""
    pass


class EmailNotifier:
    """
    SMTP email notifier for backup monitoring alerts and summaries.
    
    Handles secure email delivery with proper configuration management
    and professional formatting for monitoring notifications.
    """
    
    def __init__(self, env_file_path: str = "~/etc/grsrv03.env", logger: Optional[logging.Logger] = None):
        """
        Initialize email notifier with SMTP configuration.
        
        Args:
            env_file_path: Path to environment file with SMTP settings
            logger: Optional logger instance for error reporting
            
        Raises:
            EmailConfigError: If required SMTP configuration is missing
        """
        self.logger = logger or logging.getLogger(__name__)
        self.config = self._load_smtp_config(env_file_path)
        self._validate_config()
    
    def _load_smtp_config(self, env_file_path: str) -> Dict[str, str]:
        """
        Load SMTP configuration from environment file.
        
        Args:
            env_file_path: Path to dotenv file
            
        Returns:
            Dictionary with SMTP configuration
            
        Raises:
            EmailConfigError: If file cannot be loaded or required vars missing
        """
        # Expand user path
        full_path = os.path.expanduser(env_file_path)
        
        if not os.path.exists(full_path):
            raise EmailConfigError(f"SMTP config file not found: {full_path}")
        
        # Load environment variables
        if not load_dotenv(full_path, override=True):
            self.logger.warning(f"Failed to load dotenv from {full_path}")
        
        config = {
            'smtp_server': os.environ.get('SMTP_SERVER'),
            'smtp_port': os.environ.get('SMTP_PORT'),
            'smtp_token': os.environ.get('SMTP_TOKEN'),  # App password
            'from_email': os.environ.get('FROM_EMAIL'),
            'to_email': os.environ.get('TO_EMAIL'),
        }
        
        return config
    
    def _validate_config(self) -> None:
        """
        Validate that required SMTP configuration is present.
        
        Raises:
            EmailConfigError: If required configuration is missing
        """
        required_fields = ['smtp_server', 'smtp_port', 'smtp_token', 'from_email']
        missing_fields = [field for field in required_fields if not self.config.get(field)]
        
        if missing_fields:
            raise EmailConfigError(f"Missing required SMTP configuration: {missing_fields}")
        
        # Validate port is numeric
        try:
            self.config['smtp_port'] = int(self.config['smtp_port'])
        except (ValueError, TypeError):
            raise EmailConfigError(f"Invalid SMTP port: {self.config.get('smtp_port')}")
    
    def send_email(
        self, 
        to_emails: Union[str, List[str]], 
        subject: str, 
        content: str, 
        content_type: str = 'plain',
        override_to_emails: Optional[List[str]] = None
    ) -> bool:
        """
        Send email with proper error handling and logging.
        
        Args:
            to_emails: Recipient email(s) - string or list
            subject: Email subject line
            content: Email body content
            content_type: 'plain' or 'html' (default: 'plain')
            override_to_emails: If provided, use these instead of to_emails
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Prepare recipients
            recipients = override_to_emails or self._prepare_recipients(to_emails)
            if not recipients:
                self.logger.error("No valid recipients provided")
                return False
            
            # Create message
            msg = self._create_message(recipients, subject, content, content_type)
            
            # Send via SMTP
            self._send_via_smtp(msg, recipients)
            
            self.logger.info(f"Email sent successfully to {len(recipients)} recipients: {subject}")
            return True
            
        except EmailSendError as e:
            self.logger.error(f"Failed to send email '{subject}': {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending email '{subject}': {e}")
            return False
    
    def _prepare_recipients(self, to_emails: Union[str, List[str]]) -> List[str]:
        """
        Prepare and validate recipient email addresses.
        
        Args:
            to_emails: Email addresses as string or list
            
        Returns:
            List of valid email addresses
        """
        if isinstance(to_emails, str):
            recipients = [to_emails.strip()]
        elif isinstance(to_emails, list):
            recipients = [email.strip() for email in to_emails if email.strip()]
        else:
            # Fallback to default from config
            default_email = self.config.get('to_email')
            if default_email:
                recipients = [default_email.strip()]
            else:
                recipients = []
        
        # Basic email validation
        valid_recipients = []
        for email in recipients:
            if '@' in email and '.' in email.split('@')[-1]:
                valid_recipients.append(email)
            else:
                self.logger.warning(f"Invalid email address skipped: {email}")
        
        return valid_recipients
    
    def _create_message(
        self, 
        recipients: List[str], 
        subject: str, 
        content: str, 
        content_type: str
    ) -> EmailMessage:
        """
        Create properly formatted email message.
        
        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            content: Email body
            content_type: 'plain' or 'html'
            
        Returns:
            Configured EmailMessage object
        """
        msg = EmailMessage()
        
        # Set content based on type
        if content_type.lower() == 'html':
            msg.set_content(content, subtype='html')
        else:
            msg.set_content(content)
        
        # Set headers
        msg['Subject'] = subject
        msg['From'] = self.config['from_email']
        msg['To'] = ', '.join(recipients)
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = f"<{datetime.now().timestamp()}@backup-checker>"
        
        return msg
    
    def _send_via_smtp(self, msg: EmailMessage, recipients: List[str]) -> None:
        """
        Send email message via SMTP with proper security.
        
        Args:
            msg: Configured EmailMessage
            recipients: List of recipient addresses
            
        Raises:
            EmailSendError: If SMTP operation fails
        """
        try:
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect and send
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls(context=context)
                server.login(self.config['from_email'], self.config['smtp_token'])
                server.send_message(msg, to_addrs=recipients)
                
        except smtplib.SMTPAuthenticationError as e:
            raise EmailSendError(f"SMTP authentication failed: {e}")
        except smtplib.SMTPRecipientsRefused as e:
            raise EmailSendError(f"Recipients refused: {e}")
        except smtplib.SMTPServerDisconnected as e:
            raise EmailSendError(f"SMTP server disconnected: {e}")
        except smtplib.SMTPException as e:
            raise EmailSendError(f"SMTP error: {e}")
        except Exception as e:
            raise EmailSendError(f"Network/connection error: {e}")
    
    def create_backup_summary_email(
        self, 
        backup_results: List[Dict[str, Any]], 
        errors: List[str], 
        duration: float,
        timestamp: Optional[datetime] = None
    ) -> Tuple[str, str]:
        """
        Create formatted backup summary email content.
        
        Args:
            backup_results: List of backup check results
            errors: List of error messages
            duration: Total execution time in seconds
            timestamp: Check timestamp (default: now)
            
        Returns:
            Tuple of (subject, content) for email
        """
        timestamp = timestamp or datetime.now()
        
        # Determine overall status
        if errors:
            status = "❌ ERRORS DETECTED"
            subject_prefix = "[ALERT]"
        else:
            status = "✅ ALL CHECKS PASSED"
            subject_prefix = "[OK]"
        
        subject = f"{subject_prefix} Backup Check Report - {timestamp.strftime('%Y-%m-%d %H:%M')}"
        
        # Build content
        content_lines = [
            "Proxmox Backup Checker Report",
            "=" * 40,
            f"Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Status: {status}",
            f"Duration: {duration:.2f} seconds",
            "",
        ]
        
        # Backup results section
        if backup_results:
            content_lines.extend([
                "BACKUP CHECK RESULTS:",
                "-" * 25,
            ])
            
            for result in backup_results:
                name = result.get('name', 'Unknown')
                size = result.get('total_size_human', 'N/A')
                status_icon = "✅" if result.get('success', False) else "❌"
                
                content_lines.append(f"{status_icon} {name}: {size}")
                
                if not result.get('success', False):
                    error_msg = result.get('error', 'Unknown error')
                    content_lines.append(f"   Error: {error_msg}")
            
            content_lines.append("")
        
        # Errors section
        if errors:
            content_lines.extend([
                "ERRORS DETECTED:",
                "-" * 17,
            ])
            
            for i, error in enumerate(errors, 1):
                content_lines.append(f"{i}. {error}")
            
            content_lines.append("")
        
        # Footer
        content_lines.extend([
            "-" * 40,
            "Generated by Proxmox Backup Checker",
            f"Server: {os.uname().nodename if hasattr(os, 'uname') else 'Unknown'}",
        ])
        
        content = "\n".join(content_lines)
        
        return subject, content


def send_backup_notification(
    backup_results: List[Dict[str, Any]], 
    errors: List[str], 
    duration: float,
    config_to_emails: Optional[List[str]] = None,
    env_file_path: str = "~/etc/grsrv03.env",
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Convenience function to send backup notification email.
    
    Args:
        backup_results: List of backup check results
        errors: List of error messages  
        duration: Total execution time in seconds
        config_to_emails: Override recipient emails from config
        env_file_path: Path to SMTP configuration file
        logger: Optional logger for error reporting
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Initialize notifier
        notifier = EmailNotifier(env_file_path, logger)
        
        # Create email content
        subject, content = notifier.create_backup_summary_email(
            backup_results, errors, duration
        )
        
        # Send email
        return notifier.send_email(
            to_emails=[], # Will use default from config
            subject=subject,
            content=content,
            override_to_emails=config_to_emails
        )
        
    except Exception as e:
        if logger:
            logger.error(f"Failed to send backup notification: {e}")
        return False