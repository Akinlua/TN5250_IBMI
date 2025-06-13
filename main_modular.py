#!/usr/bin/env python3
"""
Modular TN5250 Programmatic Interaction System

This Python script provides a modular framework for interacting with TN5250 servers.
It uses CSV files for data and configuration, making it easy to support multiple screens
and different data sets without modifying the core code.

Features:
  - Modular screen handling using CSV configuration
  - Configurable field validation and tab behavior
  - Support for multiple screen types through configuration
  - Reusable connection management
  - Environment validation

Dependencies:
  - Python 3.8+
  - p5250 (pip install p5250)
  - s3270 utility (part of x3270 package)

Usage:
  python main_modular.py [screen_name]
  
  If no screen_name is provided, defaults to 'company_maintenance'
  
Examples:
  python main_modular.py company_maintenance
  python main_modular.py customer_maintenance
  python main_modular.py vendor_maintenance
"""

import sys
import logging
import signal
import atexit
import os
from pathlib import Path

# Add the modules directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from modules.screen_handler import ScreenHandler
from modules.connection_manager import ConnectionManager
from config.screen_configs import SCREEN_CONFIGS, CONNECTION_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global client reference for cleanup
_global_client = None
_connection_manager = None

def signal_handler(signum, frame):
    """Handle script interruption signals"""
    logger.info(f"Received signal {signum}. Cleaning up...")
    if _connection_manager and _global_client:
        _connection_manager.cleanup_connection(_global_client)
    sys.exit(0)

def exit_handler():
    """Cleanup function called on script exit"""
    if _connection_manager and _global_client:
        _connection_manager.cleanup_connection(_global_client)

# Register signal handlers and exit cleanup
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination
atexit.register(exit_handler)

def get_screen_name_from_args() -> str:
    """Get screen name from command line arguments"""
    if len(sys.argv) > 1:
        screen_name = sys.argv[1]
        if screen_name in SCREEN_CONFIGS:
            return screen_name
        else:
            logger.error(f"Unknown screen name: {screen_name}")
            logger.info(f"Available screens: {', '.join(SCREEN_CONFIGS.keys())}")
            sys.exit(1)
    else:
        # Default to company_maintenance
        return 'company_maintenance'

def validate_screen_files(screen_config: dict) -> bool:
    """Validate that all required files exist for the screen"""
    required_files = ['data_file', 'config_file', 'navigation_file']
    
    for file_key in required_files:
        file_path = screen_config.get(file_key)
        if not file_path:
            logger.error(f"Missing {file_key} in screen configuration")
            return False
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
    
    return True

def main():
    """Main execution flow"""
    global _global_client, _connection_manager
    
    logger.info("=" * 60)
    logger.info("Modular TN5250 Interaction System Starting")
    logger.info("=" * 60)
    
    # Get screen name from command line arguments
    screen_name = get_screen_name_from_args()
    logger.info(f"Processing screen: {screen_name}")
    
    # Get screen configuration
    if screen_name not in SCREEN_CONFIGS:
        logger.error(f"No configuration found for screen: {screen_name}")
        logger.info(f"Available screens: {', '.join(SCREEN_CONFIGS.keys())}")
        return
    
    screen_config = SCREEN_CONFIGS[screen_name]
    logger.info(f"Screen description: {screen_config['description']}")
    
    # Validate that all required files exist
    if not validate_screen_files(screen_config):
        logger.error("Screen file validation failed. Please ensure all required files exist.")
        return
    
    try:
        # Initialize connection manager
        _connection_manager = ConnectionManager(CONNECTION_CONFIG)
        
        # Validate environment
        if not _connection_manager.validate_environment():
            logger.error("Environment validation failed. Please fix the issues above.")
            return
        
        # Initialize screen handler
        screen_handler = ScreenHandler(
            data_file=screen_config['data_file'],
            config_file=screen_config['config_file'],
            navigation_file=screen_config['navigation_file']
        )
        
        # Validate screen data
        validation_success, validation_messages = screen_handler.validate_all_fields()
        if not validation_success:
            logger.error("Screen data validation failed. Please fix the errors above before proceeding.")
            # Print all validation messages
            for msg in validation_messages:
                if "ERROR" in msg:
                    logger.error(msg)
                else:
                    logger.info(msg)
            return
        
        logger.info("All validations passed successfully!")
        
        # Establish connection
        logger.info(f"Connecting to IBM i system at {CONNECTION_CONFIG['HOST']}:{CONNECTION_CONFIG['PORT']}")
        client, connected = _connection_manager.connect_to_host()
        
        if not connected or not client:
            logger.error("Failed to establish a connection. Please check connection details and try again.")
            return
        
        # Set global client reference for cleanup
        _global_client = client
        
        logger.info("Connection established. Starting screen processing...")
        
        # Process the screen
        success, processing_messages = screen_handler.process_screen(
            client,
            username=CONNECTION_CONFIG['USERNAME'],
            password=CONNECTION_CONFIG['PASSWORD'],
            company_id=screen_config['company_id'],
            option=screen_config['option'],
            operation=screen_config['operation']
        )
        
        # Print all processing messages
        for msg in processing_messages:
            if "ERROR" in msg or "VALIDATION ERROR" in msg:
                logger.error(msg)
            elif "SUCCESS" in msg or "✓" in msg:
                logger.info(msg)
            else:
                logger.info(msg)
        
        if success:
            logger.info("Screen processing completed successfully!")
        else:
            logger.error("Screen processing failed. Please check the logs above.")
        
        # Disconnect
        logger.info("Processing complete. Disconnecting...")
        _connection_manager.cleanup_connection(client)
        _global_client = None
        
        logger.info("=" * 60)
        logger.info("Modular TN5250 Interaction System Completed")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        if _connection_manager and _global_client:
            _connection_manager.cleanup_connection(_global_client)
    except Exception as e:
        logger.error(f"Unexpected error during execution: {str(e)}")
        if _connection_manager and _global_client:
            _connection_manager.cleanup_connection(_global_client)
        _global_client = None

if __name__ == "__main__":
    main() 