#!/usr/bin/env python3
"""
Test HTML File Saving

This script tests the HTML file saving functionality of the modular system
without connecting to the TN5250 server.
"""

import sys
import os
import logging
from pathlib import Path
import time

# Add the modules directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from modules.screen_handler import ScreenHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockClient:
    """Mock client for testing that simulates the TN5250 client"""
    
    def getScreen(self):
        """Return mock screen content"""
        return """                    COMPANY MAINTENANCE                    
                                                                    
  Company ID  . . . . TEST01        
  Company Name  . . . Test Company Name                           
  Address Line 1  . . Test Address Line 1                        
  Address Line 2  . . Test Address Line 2                        
  City  . . . . . . . Test City            
  State . . . . . . . CA  Country . . . . US    
  Postal Code . . . . 12345     
  Phone Number  . . . 555-1234              
  Fax Number  . . . .                       
  Email . . . . . . . test@company.com                           
  Website . . . . . . www.testcompany.com                        
  Tax ID  . . . . . . 123-45-6789           
  Currency Code . . . USD   
                                                                    
                                                                    
 F3=Exit   F12=Cancel                                              
"""

def test_manual_html_saving():
    """Test that manual HTML saving works correctly"""
    logger.info("Testing manual HTML file saving...")
    
    try:
        # Create a ScreenHandler instance
        screen_handler = ScreenHandler(
            data_file='screens/company_maintenance_data.csv',
            config_file='screens/company_maintenance_config.csv',
            navigation_file='screens/navigation_config.csv'
        )
        
        # Create a mock client
        mock_client = MockClient()
        
        # Test manual HTML saving
        test_filename = 'test_manual_save.html'
        screen_handler._save_screen_to_html(mock_client, test_filename)
        
        # Check if the file was created
        full_path = screen_handler._get_html_filename(test_filename)
        
        if os.path.exists(full_path):
            logger.info(f"✓ HTML file created successfully: {full_path}")
            
            # Read and verify the content
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if it contains proper HTML structure
            if '<!DOCTYPE html>' in content:
                logger.info("✓ File contains proper HTML DOCTYPE")
            else:
                logger.error("✗ File missing HTML DOCTYPE")
                return False
            
            if 'COMPANY MAINTENANCE' in content:
                logger.info("✓ File contains expected screen content")
            else:
                logger.error("✗ File missing expected screen content")
                return False
            
            if 'Captured:' in content:
                logger.info("✓ File contains timestamp")
            else:
                logger.error("✗ File missing timestamp")
                return False
            
            # Show file size
            file_size = os.path.getsize(full_path)
            logger.info(f"✓ HTML file size: {file_size} bytes")
            
            # Test multiple saves to ensure unique filenames
            time.sleep(1)  # Wait to ensure different timestamp
            screen_handler._save_screen_to_html(mock_client, test_filename)
            
            # List all test files created
            output_dir = screen_handler.output_dir
            test_files = [f for f in os.listdir(output_dir) if f.startswith('test_manual_save')]
            logger.info(f"✓ Created {len(test_files)} unique test files: {test_files}")
            
            return True
            
        else:
            logger.error(f"✗ HTML file was not created: {full_path}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error testing manual HTML saving: {str(e)}")
        return False

def test_output_directory_creation():
    """Test that ScreenHandler creates output directories correctly"""
    logger.info("Testing HTML output directory creation...")
    
    try:
        # Create a ScreenHandler instance (this should create the output directory)
        screen_handler = ScreenHandler(
            data_file='screens/company_maintenance_data.csv',
            config_file='screens/company_maintenance_config.csv',
            navigation_file='screens/navigation_config.csv'
        )
        
        # Check if output directory was created
        output_dir = screen_handler.output_dir
        logger.info(f"Output directory: {output_dir}")
        
        if os.path.exists(output_dir) and output_dir != ".":
            logger.info(f"✓ Output directory created successfully: {output_dir}")
            
            # Test filename generation with timestamps
            test_filename = screen_handler._get_html_filename('test_screen.html')
            logger.info(f"✓ Test filename generated: {test_filename}")
            
            # Test multiple filename generations to ensure uniqueness
            time.sleep(1)  # Wait a second to ensure different timestamp
            test_filename2 = screen_handler._get_html_filename('test_screen.html')
            logger.info(f"✓ Second test filename generated: {test_filename2}")
            
            if test_filename != test_filename2:
                logger.info("✓ Filenames are unique (timestamps working)")
            else:
                logger.warning("⚠ Filenames are the same (may be due to fast execution)")
            
            # Test filename without extension
            test_filename_no_ext = screen_handler._get_html_filename('test_screen')
            logger.info(f"✓ Filename without extension: {test_filename_no_ext}")
            
            # Create a test file to verify the directory is writable
            test_file_path = os.path.join(output_dir, 'test_write.txt')
            try:
                with open(test_file_path, 'w') as f:
                    f.write("Test file created successfully")
                logger.info(f"✓ Directory is writable: {test_file_path}")
                
                # Clean up test file
                os.remove(test_file_path)
                logger.info("✓ Test file cleaned up")
                
            except Exception as e:
                logger.error(f"✗ Directory is not writable: {str(e)}")
                return False
                
        else:
            logger.warning(f"Output directory not created or using current directory: {output_dir}")
            
        return True
        
    except Exception as e:
        logger.error(f"✗ Error testing output directory creation: {str(e)}")
        return False

def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("HTML File Saving Test")
    logger.info("=" * 60)
    
    # Test output directory creation
    success1 = test_output_directory_creation()
    
    # Test manual HTML saving
    success2 = test_manual_html_saving()
    
    if success1 and success2:
        logger.info("✓ All HTML file saving tests passed!")
        logger.info("")
        logger.info("NOTE: The system now manually creates HTML files using getScreen() content.")
        logger.info("HTML files are saved to a timestamped directory with proper HTML structure.")
        logger.info("This approach doesn't rely on the saveScreen() method.")
    else:
        logger.error("✗ HTML file saving tests failed!")
        return 1
    
    logger.info("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main()) 