"""
Connection Manager Module

This module handles TN5250 connections and provides utility functions
for checking dependencies and host connectivity.
"""

import os
import socket
import time
import logging
from p5250 import P5250Client
from typing import Tuple, List, Optional

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages TN5250 connections and provides connection utilities"""
    
    def __init__(self, config: dict):
        self.host = config['HOST']
        self.port = config['PORT']
        self.use_ssl = config['USE_SSL']
        self.username = config['USERNAME']
        self.password = config['PASSWORD']
        self.preferred_model = config['PREFERRED_MODEL']
        self.code_page = config['CODE_PAGE']
        self.screen_timeout = config['SCREEN_TIMEOUT']
    
    def check_s3270_installed(self) -> bool:
        """Check if s3270 is available in PATH"""
        paths = os.environ["PATH"].split(os.pathsep)
        for path in paths:
            s3270_path = os.path.join(path, "s3270")
            if os.path.exists(s3270_path) and os.access(s3270_path, os.X_OK):
                logger.info(f"Found s3270 at: {s3270_path}")
                return True
            else:
                s3270_path = os.path.join(path, "s3270.exe")
                if os.path.exists(s3270_path) and os.access(s3270_path, os.X_OK):
                    logger.info(f"Found s3270 at: {s3270_path}")
                    return True
                
        logger.error("s3270 not found in PATH. Please install it using your package manager.")
        logger.info("For macOS: brew install x3270")
        logger.info("For Linux: apt-get install x3270 or equivalent")
        logger.info("For Windows: Download from http://x3270.bgp.nu/download.html")
        return False
    
    def check_host_reachable(self, timeout: int = 5) -> bool:
        """Check if host is reachable via socket connection"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            if result == 0:
                logger.info(f"Host {self.host}:{self.port} is reachable")
                return True
            else:
                logger.error(f"Host {self.host}:{self.port} is not reachable (error code: {result})")
                if result == 61:  # Connection refused
                    logger.info("Connection refused. The service may not be running or is blocked by a firewall.")
                elif result == 60:  # Operation timed out
                    logger.info("Connection timed out. The host might be unreachable or behind a firewall.")
                return False
        except socket.error as e:
            logger.error(f"Socket error while checking host: {str(e)}")
            return False
    
    def connect_to_host(self, models: Optional[List[str]] = None) -> Tuple[Optional[P5250Client], bool]:
        """Try to connect using various terminal models"""
        if models is None:
            models = [self.preferred_model, "3279-2", "3278-2", "3278-4"]
        
        client = None
        connected = False
        
        for model in models:
            logger.info(f"Trying connection with model: {model}")
            
            try:
                client = P5250Client(
                    hostName=self.host,
                    hostPort=str(self.port),
                    modelName=model,
                    timeoutInSec=self.screen_timeout,
                    verifyCert="no" if not self.use_ssl else "yes",
                    enableTLS="yes" if self.use_ssl else "no",
                    codePage=self.code_page
                )
                
                logger.info("Establishing connection...")
                client.connect()
                time.sleep(3)
                
                # Check connection status
                if hasattr(client, 'isConnected') and callable(client.isConnected):
                    connected = client.isConnected()
                    if connected:
                        logger.info(f"Successfully connected using model {model}")
                        return client, True
                    else:
                        logger.error(f"Failed to connect with model {model}")
                else:
                    # If no isConnected method exists, try getting screen content
                    try:
                        screen = client.getScreen()
                        logger.info(f"Connection verified by retrieving screen content")
                        return client, True
                    except:
                        logger.error(f"Could not verify connection with model {model}")
                        
            except Exception as e:
                logger.error(f"Error connecting with model {model}: {str(e)}")
                if client:
                    try:
                        client.disconnect()
                    except:
                        pass
                continue
        
        return None, False
    
    def cleanup_connection(self, client: Optional[P5250Client]):
        """Safely disconnect and cleanup the client connection"""
        if not client:
            return
        
        try:
            # Check if client still has an active connection before attempting disconnect
            if hasattr(client, 'isConnected') and callable(client.isConnected):
                if client.isConnected():
                    client.disconnect()
                    logger.info("Successfully disconnected")
                    return
                else:
                    logger.info("Connection already closed")
                    return
            else:
                # Try to disconnect anyway if we can't check connection status
                client.disconnect()
                logger.info("Successfully disconnected")
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            # These are expected errors when the connection is already closed
            logger.info(f"Connection was already closed (this is normal): {type(e).__name__}")
        except Exception as e:
            logger.warning(f"Unexpected error during disconnect: {str(e)}")
    
    def validate_environment(self) -> bool:
        """Validate that all dependencies and connectivity requirements are met"""
        logger.info("Validating environment...")
        
        # Check s3270 dependency
        if not self.check_s3270_installed():
            return False
        
        # Check host reachability
        if not self.check_host_reachable():
            logger.error("Please check that the IBM i system is accessible and the connection details are correct.")
            logger.info("If you believe the connection details are correct, the system may be:")
            logger.info("1. Down or not accepting connections")
            logger.info("2. Blocked by a firewall")
            logger.info("3. Not listening on the specified port")
            return False
        
        logger.info("Environment validation passed!")
        return True 