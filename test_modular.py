#!/usr/bin/env python3
"""
Test Script for Modular TN5250 System

This script tests the modular system configuration without requiring
an actual TN5250 connection. It validates:
- File existence
- CSV parsing
- Field validation
- Configuration loading

Usage: python test_modular.py [screen_name]
"""

import sys
import logging
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

def test_screen_configuration(screen_name: str):
    """Test a specific screen configuration"""
    logger.info(f"Testing screen configuration: {screen_name}")
    
    if screen_name not in SCREEN_CONFIGS:
        logger.error(f"Screen '{screen_name}' not found in configuration")
        return False
    
    screen_config = SCREEN_CONFIGS[screen_name]
    logger.info(f"Description: {screen_config['description']}")
    
    try:
        # Test file existence
        for file_key in ['data_file', 'config_file', 'navigation_file']:
            file_path = screen_config[file_key]
            if not Path(file_path).exists():
                logger.error(f"File not found: {file_path}")
                return False
            logger.info(f"✓ File exists: {file_path}")
        
        # Test screen handler initialization
        screen_handler = ScreenHandler(
            data_file=screen_config['data_file'],
            config_file=screen_config['config_file'],
            navigation_file=screen_config['navigation_file']
        )
        
        logger.info(f"✓ Loaded {len(screen_handler.screen_data)} data fields")
        logger.info(f"✓ Loaded {len(screen_handler.field_config)} field configurations")
        logger.info(f"✓ Loaded {len(screen_handler.navigation_steps)} navigation steps")
        
        # Test field validation
        if screen_handler.validate_all_fields():
            logger.info("✓ All field validations passed")
        else:
            logger.error("✗ Field validation failed")
            return False
        
        # Display configuration summary
        logger.info("\nConfiguration Summary:")
        logger.info("-" * 40)
        
        logger.info("Screen Data:")
        for field_name, value in screen_handler.screen_data.items():
            config = screen_handler.field_config.get(field_name, {})
            max_length = config.get('max_length', 0)
            tabs_needed = config.get('tabs_needed', 1)
            logger.info(f"  {field_name}: '{value}' ({len(value)}/{max_length} chars, {tabs_needed} tabs)")
        
        logger.info("\nNavigation Steps:")
        for step in screen_handler.navigation_steps:
            logger.info(f"  Step {step['step_order']}: {step['description']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing screen configuration: {str(e)}")
        return False

def test_connection_configuration():
    """Test connection configuration (without actual connection)"""
    logger.info("Testing connection configuration...")
    
    try:
        connection_manager = ConnectionManager(CONNECTION_CONFIG)
        logger.info(f"✓ Host: {connection_manager.host}:{connection_manager.port}")
        logger.info(f"✓ SSL: {connection_manager.use_ssl}")
        logger.info(f"✓ Model: {connection_manager.preferred_model}")
        logger.info(f"✓ Code Page: {connection_manager.code_page}")
        logger.info(f"✓ Timeout: {connection_manager.screen_timeout}s")
        
        # Test s3270 availability (optional)
        if connection_manager.check_s3270_installed():
            logger.info("✓ s3270 utility found")
        else:
            logger.warning("⚠ s3270 utility not found (required for actual connections)")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing connection configuration: {str(e)}")
        return False

def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("Modular TN5250 System Configuration Test")
    logger.info("=" * 60)
    
    # Get screen name from command line or test all
    if len(sys.argv) > 1:
        screen_names = [sys.argv[1]]
    else:
        screen_names = list(SCREEN_CONFIGS.keys())
    
    # Test connection configuration
    if not test_connection_configuration():
        logger.error("Connection configuration test failed")
        return
    
    logger.info("\n" + "=" * 60)
    
    # Test each screen configuration
    all_passed = True
    for screen_name in screen_names:
        logger.info(f"\nTesting screen: {screen_name}")
        logger.info("-" * 40)
        
        if not test_screen_configuration(screen_name):
            logger.error(f"Configuration test failed for screen: {screen_name}")
            all_passed = False
        else:
            logger.info(f"✓ Configuration test passed for screen: {screen_name}")
    
    logger.info("\n" + "=" * 60)
    
    if all_passed:
        logger.info("🎉 All configuration tests passed!")
        logger.info("The modular system is ready for use.")
    else:
        logger.error("❌ Some configuration tests failed.")
        logger.info("Please fix the issues above before running the main system.")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main() 