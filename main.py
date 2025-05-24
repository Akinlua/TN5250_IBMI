'''
TN5250 Programmatic Interaction POC

This Python script demonstrates programmatic interaction with a TN5250 server using the open-source p5250 library.
It provides a framework for connecting to an IBM i system (formerly AS/400) and automating terminal interactions.

Features:
  - Environment setup and validation
  - Host connectivity checks
  - Connection establishment with various terminal models
  - Screen reading and field interaction
  - Error handling and diagnostics

Dependencies:
  - Python 3.8+
  - p5250 (pip install p5250)
  - p3270 (dependency of p5250, automatically installed)
  - s3270 utility (part of x3270 package), must be installed and in PATH
    - macOS: brew install x3270
    - Linux: apt-get install x3270 or equivalent
    - Windows: Download from http://x3270.bgp.nu/download.html

Setup:
  1. Install dependencies: pip install p5250
  2. Install s3270 utility (use package manager for your OS)
  3. Configure connection details below
  4. Run: python main.py

Troubleshooting:
  - If connection fails, verify the HOST and PORT are correct
  - Check that the IBM i system is accessible from your network
  - Verify that you have the correct credentials
  - Check that s3270 is properly installed and in PATH
'''
import sys
import time
import logging
import os
import socket
from p5250 import P5250Client

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ------------------------- Configuration -------------------------
# IBM i Connection Settings
HOST = "10.150.0.59"       # IP address of the IBM i system
PORT = 23                  # TN5250 port (typically 23 for non-SSL, 992 for SSL)
USE_SSL = False            # Set to True to use SSL/TLS for secure connection

# Authentication
USERNAME = "QPGMR"         # IBM i username
PASSWORD = "AUMTQPgm"              # IBM i password

# Terminal Settings
PREFERRED_MODEL = "3279-2" # Preferred terminal model
CODE_PAGE = "cp037"        # EBCDIC code page (cp037 is US English)
SCREEN_TIMEOUT = 30        # Seconds to wait for screen responses

# ------------------------- Utility Functions -------------------------
def check_s3270_installed():
    """Check if s3270 is available in PATH"""
    paths = os.environ["PATH"].split(os.pathsep)
    for path in paths:
        s3270_path = os.path.join(path, "s3270")
        if os.path.exists(s3270_path) and os.access(s3270_path, os.X_OK):
            logger.info(f"Found s3270 at: {s3270_path}")
            return True
            
    logger.error("s3270 not found in PATH. Please install it using your package manager.")
    logger.info("For macOS: brew install x3270")
    logger.info("For Linux: apt-get install x3270 or equivalent")
    logger.info("For Windows: Download from http://x3270.bgp.nu/download.html")
    return False

def check_host_reachable(host, port, timeout=5):
    """Check if host is reachable via socket connection"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            logger.info(f"Host {host}:{port} is reachable")
            return True
        else:
            logger.error(f"Host {host}:{port} is not reachable (error code: {result})")
            if result == 61:  # Connection refused
                logger.info("Connection refused. The service may not be running or is blocked by a firewall.")
            elif result == 60:  # Operation timed out
                logger.info("Connection timed out. The host might be unreachable or behind a firewall.")
            return False
    except socket.error as e:
        logger.error(f"Socket error while checking host: {str(e)}")
        return False

def connect_to_host(host, port, models=None):
    """Try to connect using various terminal models"""
    if models is None:
        models = [PREFERRED_MODEL, "3279-2", "3278-2", "3278-4"]
    
    client = None
    connected = False
    
    for model in models:
        logger.info(f"Trying connection with model: {model}")
        
        try:
            client = P5250Client(
                hostName=host,
                hostPort=str(port),
                modelName=model,
                timeoutInSec=SCREEN_TIMEOUT,
                verifyCert="no" if not USE_SSL else "yes",
                enableTLS="yes" if USE_SSL else "no",
                codePage=CODE_PAGE
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

# ------------------------- Main Flow -------------------------
def main():
    """Main execution flow"""
    # Check dependencies
    if not check_s3270_installed():
        return
    
    # Check host reachability
    if not check_host_reachable(HOST, PORT):
        logger.error("Please check that the IBM i system is accessible and the connection details are correct.")
        logger.info("If you believe the connection details are correct, the system may be:")
        logger.info("1. Down or not accepting connections")
        logger.info("2. Blocked by a firewall")
        logger.info("3. Not listening on the specified port")
        return
    
    # Attempt connection
    try:
        logger.info(f"Connecting to IBM i system at {HOST}:{PORT}")
        client, connected = connect_to_host(HOST, PORT)
        
        if not connected or not client:
            logger.error("Failed to establish a connection. Please check connection details and try again.")
            return
        
        # Connection established - demonstrate basic operations
        logger.info("Connection established. Attempting basic operations...")
        
        # Get initial screen content
        try:
            screen = client.getScreen()
            logger.info("Current screen content:")
            logger.info("-" * 50)
            logger.info(screen)
            logger.info("-" * 50)
        except Exception as e:
            logger.error(f"Error retrieving screen content: {str(e)}")
        
        # Example: If this was a real automation script, here we'd:
        # 1. Process the screen content
        # 2. Determine the current state (login, menu, etc.)
        # 3. Take appropriate actions (enter credentials, select menu options)
        
        # Disconnect
        logger.info("Demonstration complete. Disconnecting...")
        try:
            client.disconnect()
            logger.info("Successfully disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting: {str(e)}")
            
    except Exception as e:
        logger.error(f"Unexpected error during execution: {str(e)}")

# ------------------------- Script Entry Point -------------------------
if __name__ == "__main__":
    main()
