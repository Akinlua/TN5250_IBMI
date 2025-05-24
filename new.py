#!/usr/bin/env python3
"""
IBM i Automation Script using py5250
This script automates the login and accounting operations on an IBM i system
using the py5250 terminal emulator.
"""

import time
import sys
import logging
from p5250 import tn5250

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Configuration
HOST = "10.150.0.59"  # Replace with your IBM i host address
PORT = 23  # Default telnet port
USERNAME = "QPGMR"
PASSWORD = "AUMTQPgm"
ERP_USERNAME = "your_erp_username"  # Replace with actual ERP username
ERP_PASSWORD = "your_erp_password"  # Replace with actual ERP password

def wait_for_system(session, seconds=1):
    """Wait for the system to process the last command"""
    time.sleep(seconds)
    while session.is_busy():
        time.sleep(0.5)

def connect_to_ibm_i():
    """Connect to the IBM i system"""
    try:
        logger.info(f"Connecting to {HOST}:{PORT}")
        session = tn5250.Tn5250Session(HOST, PORT)
        session.connect()
        logger.info("Connected successfully")
        return session
    except Exception as e:
        logger.error(f"Connection failed: {str(e)}")
        sys.exit(1)

def login(session):
    """Login to the IBM i system"""
    try:
        logger.info(f"Logging in as {USERNAME}")
        
        # Wait for login screen
        wait_for_system(session, 2)
        
        # Enter username
        session.send_keys(USERNAME)
        session.send_keys(tn5250.Keys.TAB)
        
        # Enter password
        session.send_keys(PASSWORD)
        session.send_keys(tn5250.Keys.ENTER)
        
        wait_for_system(session, 2)
        logger.info("Login successful")
        
        # Check if we're at a command line
        screen_text = session.get_screen_text()
        if "Command" in screen_text:
            return True
        else:
            logger.warning("Command line not detected after login")
            return False
            
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return False

def edit_library_list(session):
    """Run the EDTLIBL command"""
    try:
        logger.info("Running EDTLIBL command")
        session.send_keys("EDTLIBL")
        session.send_keys(tn5250.Keys.ENTER)
        wait_for_system(session, 2)
        
        # Add entries
        logger.info("Adding entries with KEY")
        session.send_keys("KEY")
        session.send_keys(tn5250.Keys.ENTER)
        wait_for_system(session, 2)
        
        logger.info("Library list edited successfully")
        return True
    except Exception as e:
        logger.error(f"Edit library list failed: {str(e)}")
        return False

def access_accounting(session):
    """Access the accounting module"""
    try:
        logger.info("Accessing accounting module")
        session.send_keys("ACCOUNTING")
        session.send_keys(tn5250.Keys.ENTER)
        wait_for_system(session, 2)
        
        # Enter ERP credentials
        logger.info("Entering ERP credentials")
        session.send_keys(ERP_USERNAME)
        session.send_keys(tn5250.Keys.TAB)
        session.send_keys(ERP_PASSWORD)
        session.send_keys(tn5250.Keys.ENTER)
        wait_for_system(session, 2)
        
        logger.info("Accessed accounting successfully")
        return True
    except Exception as e:
        logger.error(f"Access accounting failed: {str(e)}")
        return False

def select_option_21(session):
    """Select option 21 from the menu"""
    try:
        logger.info("Selecting Option 21")
        session.send_keys("21")
        session.send_keys(tn5250.Keys.ENTER)
        wait_for_system(session, 2)
        
        logger.info("Option 21 selected successfully")
        return True
    except Exception as e:
        logger.error(f"Select option 21 failed: {str(e)}")
        return False

def select_company(session, company_number=1):
    """Select Option 1 for a company"""
    try:
        logger.info(f"Selecting Option 1 for company {company_number}")
        
        # Position cursor at the company row
        for _ in range(company_number):
            session.send_keys(tn5250.Keys.DOWN)
            
        # Enter option 1
        session.send_keys("1")
        session.send_keys(tn5250.Keys.ENTER)
        wait_for_system(session, 2)
        
        logger.info("Company selected successfully")
        return True
    except Exception as e:
        logger.error(f"Select company failed: {str(e)}")
        return False

def change_values(session, field_values):
    """Change values in the form"""
    try:
        logger.info("Changing values")
        
        for field, value in field_values.items():
            # This is simplified - in a real scenario, you'd need to know
            # the exact field positions or navigate using TAB
            logger.info(f"Setting {field} to {value}")
            session.send_keys(value)
            session.send_keys(tn5250.Keys.TAB)
            
        # Confirm changes
        session.send_keys(tn5250.Keys.ENTER)
        wait_for_system(session, 2)
        
        logger.info("Values changed successfully")
        return True
    except Exception as e:
        logger.error(f"Change values failed: {str(e)}")
        return False

def add_new_company(session, company_data):
    """Add a new company"""
    try:
        logger.info("Adding a new company")
        
        # Enter 'A' to add a new company
        session.send_keys("A")
        session.send_keys(tn5250.Keys.ENTER)
        wait_for_system(session, 2)
        
        # Fill in company details
        for field, value in company_data.items():
            # This is simplified - in a real scenario, you'd need to know
            # the exact field positions or navigate using TAB
            logger.info(f"Setting {field} to {value}")
            session.send_keys(value)
            session.send_keys(tn5250.Keys.TAB)
            
        # Confirm addition
        session.send_keys(tn5250.Keys.ENTER)
        wait_for_system(session, 2)
        
        logger.info("Company added successfully")
        return True
    except Exception as e:
        logger.error(f"Add company failed: {str(e)}")
        return False

def delete_company(session, company_number):
    """Delete a company"""
    try:
        logger.info(f"Deleting company {company_number}")
        
        # Position cursor at the company row
        for _ in range(company_number):
            session.send_keys(tn5250.Keys.DOWN)
            
        # Enter 'D' to delete
        session.send_keys("D")
        session.send_keys(tn5250.Keys.ENTER)
        wait_for_system(session, 2)
        
        # Confirm deletion (assuming there's a confirmation prompt)
        session.send_keys("Y")
        session.send_keys(tn5250.Keys.ENTER)
        wait_for_system(session, 2)
        
        logger.info("Company deleted successfully")
        return True
    except Exception as e:
        logger.error(f"Delete company failed: {str(e)}")
        return False

def logout(session):
    """Logout from the system"""
    try:
        logger.info("Logging out")
        
        # Press F3 multiple times to exit menus
        for _ in range(5):
            session.send_keys(tn5250.Keys.F3)
            wait_for_system(session, 1)
        
        # Final logout - could be F3 or a specific command
        session.send_keys("SIGNOFF")
        session.send_keys(tn5250.Keys.ENTER)
        wait_for_system(session, 2)
        
        logger.info("Logged out successfully")
        return True
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        return False

def main():
    """Main function to run the automation script"""
    session = connect_to_ibm_i()
    
    try:
        # Login to IBM i
        if not login(session):
            raise Exception("Login failed")
        
        # Edit library list
        if not edit_library_list(session):
            raise Exception("Edit library list failed")
        
        # Access accounting
        if not access_accounting(session):
            raise Exception("Access accounting failed")
        
        # Select option 21
        if not select_option_21(session):
            raise Exception("Select option 21 failed")
        
        # Select a company (example: first company)
        if not select_company(session, 1):
            raise Exception("Select company failed")
        
        # Change values (example values)
        field_values = {
            "field1": "value1",
            "field2": "value2",
            "field3": "value3"
        }
        if not change_values(session, field_values):
            raise Exception("Change values failed")
        
        # Go back to company list (assuming F3 goes back)
        session.send_keys(tn5250.Keys.F3)
        wait_for_system(session, 2)
        
        # Add a new company (example data)
        company_data = {
            "name": "New Company Inc",
            "address": "123 Main St",
            "city": "Anytown",
            "zip": "12345"
        }
        if not add_new_company(session, company_data):
            raise Exception("Add company failed")
        
        # Delete a company (example: third company)
        if not delete_company(session, 3):
            raise Exception("Delete company failed")
        
    except Exception as e:
        logger.error(f"Automation failed: {str(e)}")
    finally:
        # Always attempt to logout cleanly
        logout(session)
        session.disconnect()
        logger.info("Session disconnected")

if __name__ == "__main__":
    main()