"""
Uptime Kuma monitoring utilities for sending heartbeat notifications.

This module provides functions to send heartbeat notifications to Uptime Kuma 
monitoring systems with intelligent parameter handling and error-safe operation.
"""

import logging
import requests
from typing import Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


class UptimeKumaError(Exception):
    """Base exception for Uptime Kuma related errors."""
    pass


def send_uptime_kuma_heartbeat(
    url: str,
    status: str = 'up',
    msg: str = 'OK',
    ping: Optional[int] = None,
    timeout: int = 5,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Send a heartbeat notification to Uptime Kuma monitoring service.
    
    This function intelligently handles parameters with the following priority:
    1. Parameters explicitly passed to this function
    2. Parameters already present in the URL
    3. Default parameter values
    
    The function is designed to be error-safe and will never raise exceptions
    that could interrupt the calling application.
    
    Args:
        url: The Uptime Kuma push URL (e.g., 'http://localhost:3001/api/push/TOKEN')
        status: Status to report ('up', 'down', 'pending'). Defaults to 'up'.
        msg: Message to include with the heartbeat. Defaults to 'OK'.
        ping: Response time in milliseconds. If None, will use URL param or omit.
        timeout: HTTP request timeout in seconds. Defaults to 5.
        logger: Optional logger instance for logging operations.
        
    Returns:
        bool: True if heartbeat was sent successfully, False otherwise.
        
    Example:
        # Basic usage
        success = send_uptime_kuma_heartbeat('http://localhost:3001/api/push/abc123')
        
        # With custom parameters
        success = send_uptime_kuma_heartbeat(
            url='http://localhost:3001/api/push/abc123',
            status='up',
            msg='Backup completed successfully',
            ping=150
        )
        
        # URL already has parameters (function params take priority)
        success = send_uptime_kuma_heartbeat(
            'http://localhost:3001/api/push/abc123?status=down&msg=Error',
            status='up',  # This overrides the URL parameter
            msg='All good'  # This overrides the URL parameter
        )
    """
    if not url:
        if logger:
            logger.debug("Uptime Kuma heartbeat skipped: no URL provided")
        return False
    
    try:
        # Parse the URL to extract existing parameters
        parsed_url = urlparse(url)
        existing_params = parse_qs(parsed_url.query)
        
        # Build final parameters with priority handling
        final_params = {}
        
        # Handle status parameter
        if status != 'up':  # Function parameter provided and not default
            final_params['status'] = status
        elif 'status' in existing_params:  # Use URL parameter
            final_params['status'] = existing_params['status'][0]
        else:  # Use default
            final_params['status'] = 'up'
            
        # Handle msg parameter
        if msg != 'OK':  # Function parameter provided and not default
            final_params['msg'] = msg
        elif 'msg' in existing_params:  # Use URL parameter
            final_params['msg'] = existing_params['msg'][0]
        else:  # Use default
            final_params['msg'] = 'OK'
            
        # Handle ping parameter (only add if explicitly provided or in URL)
        if ping is not None:  # Function parameter provided
            final_params['ping'] = str(int(ping))
        elif 'ping' in existing_params and existing_params['ping'][0]:  # URL parameter exists and not empty
            try:
                final_params['ping'] = str(int(float(existing_params['ping'][0])))
            except (ValueError, TypeError):
                # Invalid ping value in URL, skip it
                pass
        
        # Reconstruct URL with final parameters
        new_query = urlencode(final_params)
        final_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc, 
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment
        ))
        
        # Send the heartbeat request
        response = requests.get(final_url, timeout=timeout)
        response.raise_for_status()
        
        if logger:
            logger.debug(f"Uptime Kuma heartbeat sent successfully. Status: {response.status_code}")
            
        return True
        
    except requests.exceptions.Timeout:
        if logger:
            logger.warning(f"Uptime Kuma heartbeat timeout after {timeout}s")
        return False
        
    except requests.exceptions.ConnectionError:
        if logger:
            logger.warning("Uptime Kuma heartbeat failed: connection error")
        return False
        
    except requests.exceptions.HTTPError as e:
        if logger:
            logger.warning(f"Uptime Kuma heartbeat failed: HTTP {e.response.status_code}")
        return False
        
    except Exception as e:
        if logger:
            logger.error(f"Uptime Kuma heartbeat failed with unexpected error: {e}")
        return False