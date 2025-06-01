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
import signal
import atexit
from p5250 import P5250Client

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global client reference for cleanup
_global_client = None

def signal_handler(signum, frame):
    """Handle script interruption signals"""
    logger.info(f"Received signal {signum}. Cleaning up...")
    cleanup_connection(_global_client)
    sys.exit(0)

def exit_handler():
    """Cleanup function called on script exit"""
    cleanup_connection(_global_client)

# Register signal handlers and exit cleanup
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination
atexit.register(exit_handler)

# ------------------------- Configuration -------------------------
# IBM i Connection Settings
HOST = "10.150.0.59"       # IP address of the IBM i system
PORT = 23                  # TN5250 port (typically 23 for non-SSL, 992 for SSL)
USE_SSL = False            # Set to True to use SSL/TLS for secure connection

# Authentication
USERNAME = "QPGMR"         # IBM i username
PASSWORD = "AUMTQPgm"      # IBM i password

# Terminal Settings
PREFERRED_MODEL = "3279-2" # Preferred terminal model
CODE_PAGE = "cp037"        # EBCDIC code page (cp037 is US English)
SCREEN_TIMEOUT = 30        # Seconds to wait for screen responses

# Company Data Configuration
NEW_COMPANY_ID = "689"     # Company ID for the new company to be added
COMPANY_OPTION = "A"       # Option: A=Add, C=Change, D=Delete

# Field Configuration with validation rules
FIELD_CONFIG = {
    'COMPANY_NAME': {'max_length': 28, 'required': True, 'type': 'text'},
    'COMPANY_ADDRESS': {'max_length': 60, 'required': True, 'type': 'text'},
    'COMPANY_LOCATION': {'max_length': 20, 'required': True, 'type': 'text'},
    'COMPANY_REGION': {'max_length': 2, 'required': True, 'type': 'text'},
    'COMPANY_POSTAL_CODE': {'max_length': 10, 'required': True, 'type': 'text'},
    'COMPANY_COUNTRY': {'max_length': 2, 'required': True, 'type': 'text'},
    'COMPANY_PHONE': {'max_length': 10, 'required': False, 'type': 'digits'},
    'COMPANY_FAX': {'max_length': 10, 'required': False, 'type': 'digits'},
    'COMPANY_TYPE': {'max_length': 1, 'required': True, 'type': 'text', 'valid_values': ['F', 'S']},
    'PERIODS_PER_YEAR': {'max_length': 2, 'required': True, 'type': 'digits'},
    'FISCAL_YEAR_ENDING': {'max_length': 2, 'required': True, 'type': 'digits'},
    'CLOSING_ACCOUNT': {'max_length': 6, 'required': True, 'type': 'digits'},
    'BASE_CURRENCY': {'max_length': 3, 'required': True, 'type': 'text'},
    'EXCHANGE_ACCOUNT': {'max_length': 6, 'required': True, 'type': 'digits'}
}

# Company Details (validated against FIELD_CONFIG)
COMPANY_DATA = {
    'COMPANY_NAME': "TEST COMPANY 10",
    'COMPANY_ADDRESS': "123 MAIN STREET",
    'COMPANY_LOCATION': "ST CLOUD",
    'COMPANY_REGION': "MN",
    'COMPANY_POSTAL_CODE': "56301",
    'COMPANY_COUNTRY': "US",
    'COMPANY_PHONE': "",
    'COMPANY_FAX': "",
    'COMPANY_TYPE': "F",
    'PERIODS_PER_YEAR': "12",
    'FISCAL_YEAR_ENDING': "12",
    'CLOSING_ACCOUNT': "000000",
    'BASE_CURRENCY': "USD",
    'EXCHANGE_ACCOUNT': "000000"
}

# ------------------------- Utility Functions -------------------------
def check_s3270_installed():
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

# ------------------------- Validation Functions -------------------------
def validate_field(field_name, value):
    """Validate a field against its configuration"""
    if field_name not in FIELD_CONFIG:
        return False, f"Unknown field: {field_name}"
    
    config = FIELD_CONFIG[field_name]
    
    # Check if required field is empty
    if config['required'] and not value:
        return False, f"{field_name} is required but empty"
    
    # If not required and empty, it's valid
    if not config['required'] and not value:
        return True, "Optional field is empty (valid)"
    
    # Check length
    if len(value) > config['max_length']:
        return False, f"{field_name} exceeds maximum length of {config['max_length']} (current: {len(value)})"
    
    # Check type
    if config['type'] == 'digits' and not value.isdigit():
        return False, f"{field_name} must contain only digits"
    
    # Check valid values if specified
    if 'valid_values' in config and value not in config['valid_values']:
        return False, f"{field_name} must be one of {config['valid_values']} (current: {value})"
    
    return True, "Valid"

def validate_all_fields():
    """Validate all company data fields"""
    logger.info("Validating all company data fields...")
    all_valid = True
    
    for field_name, value in COMPANY_DATA.items():
        is_valid, message = validate_field(field_name, value)
        if not is_valid:
            logger.error(f"VALIDATION ERROR - {message}")
            all_valid = False
        else:
            logger.info(f"✓ {field_name}: '{value}' ({len(value)}/{FIELD_CONFIG[field_name]['max_length']} chars)")
    
    return all_valid

def should_auto_tab(field_name, value):
    """Determine if field will auto-tab based on length"""
    if field_name not in FIELD_CONFIG:
        return False
    
    max_length = FIELD_CONFIG[field_name]['max_length']
    return len(value) >= max_length

def send_field_data(client, field_name, value):
    """Send field data and handle tabbing based on field configuration"""
    if not value:  # Empty field
        logger.info(f"Skipping {field_name} (empty)")
        if not should_auto_tab(field_name, ""):  # Empty fields don't auto-tab
            client.sendTab()
        return
    
    client.sendText(value)
    logger.info(f"Entered {field_name}: '{value}' ({len(value)}/{FIELD_CONFIG[field_name]['max_length']} chars)")
    
    # Only send tab if field won't auto-tab
    if not should_auto_tab(field_name, value):
        client.sendTab()
        logger.debug(f"Sent TAB after {field_name} (not at max length)")
    else:
        logger.debug(f"No TAB needed for {field_name} (at max length - will auto-tab)")

def cleanup_connection(client):
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

# ------------------------- Main Flow -------------------------
def main():
    """Main execution flow"""
    global _global_client
    
    # First validate all company data before attempting connection
    if not validate_all_fields():
        logger.error("Company data validation failed. Please fix the errors above before proceeding.")
        return
    
    logger.info("All company data validated successfully!")
    
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
        
        # Set global client reference for cleanup
        _global_client = client
        
        # Connection established - demonstrate basic operations
        logger.info("Connection established. Starting automated sequence...")
        
        # Step 1: Handle Sign On screen
        logger.info("Step 1: Processing Sign On screen...")
        try:
            screen = client.getScreen()
            client.saveScreen(fileName='01_signin.html')
            logger.info("Sign On screen content:")
            logger.info("-" * 50)
            logger.info(screen)
            logger.info("-" * 50)
            
            # Check if we're on the sign-on screen
            if "Sign On" in screen or "User" in screen:
                logger.info("Detected Sign On screen. Entering credentials...")
                
                # Move to User field and enter username
                client.moveToFirstInputField()
                client.sendText(USERNAME)
                logger.info(f"Entered username: {USERNAME}")
                
                # Tab to password field and enter password
                client.sendTab()
                client.sendText(PASSWORD)
                logger.info("Entered password")
                
                # Press Enter to submit
                client.sendEnter()
                logger.info("Submitted credentials")
                time.sleep(3)  # Wait for response
            else:
                logger.info("Not on Sign On screen, continuing...")
                
        except Exception as e:
            logger.error(f"Error during Step 1 (Sign On): {str(e)}")
        
        # Step 2: Handle "Press Enter to continue" screen
        logger.info("Step 2: Processing message screen...")
        try:
            screen = client.getScreen()
            client.saveScreen(fileName='02_message.html')
            logger.info("Message screen content:")
            logger.info("-" * 50)
            logger.info(screen)
            logger.info("-" * 50)
            
            # Check if we need to press Enter to continue
            if "Press Enter to continue" in screen or "Message queue" in screen:
                logger.info("Detected message screen. Pressing Enter to continue...")
                client.sendEnter()
                time.sleep(2)  # Wait for response
            else:
                logger.info("No message screen detected, continuing...")
                
        except Exception as e:
            logger.error(f"Error during Step 2 (Message screen): {str(e)}")
        
        # Step 3: Handle Main Menu and execute CALL PGM command
        logger.info("Step 3: Processing Main Menu and executing CALL PGM command...")
        try:
            screen = client.getScreen()
            client.saveScreen(fileName='03_mainmenu.html')
            logger.info("Main Menu screen content:")
            logger.info("-" * 50)
            logger.info(screen)
            logger.info("-" * 50)
            
            # Check if we're on the main menu
            if "IBM i Main Menu" in screen or "Select one of the following" in screen:
                logger.info("Detected Main Menu. Executing CALL PGM command...")
                
                # Look for the command line at the bottom of the screen
                # The command appears to be: CALL PGM(LOADFBP) PARM(('*ADMIN') ('AdminAEBL'))
                command = "CALL PGM(LOADERP) PARM(('*ADMIN') ('AdminAaBb'))"
                
                # Clear any existing text and enter the command
                client.sendText(command)
                logger.info(f"Entered command: {command}")
                
                # Press Enter to execute
                client.sendEnter()
                logger.info("Executed CALL PGM command")
                time.sleep(3)  # Wait for response
            else:
                logger.info("Not on Main Menu, continuing...")
                
        except Exception as e:
            logger.error(f"Error during Step 3 (Main Menu): {str(e)}")
        
        # Step 4: Handle Administrator Menu and select option 21
        logger.info("Step 4: Processing Administrator Menu and selecting option 21...")
        try:
            screen = client.getScreen()
            client.saveScreen(fileName='04_adminmenu.html')
            logger.info("Administrator Menu screen content:")
            logger.info("-" * 50)
            logger.info(screen)
            logger.info("-" * 50)
            
            # Check if we're on the administrator menu
            if "*ADMINISTRATOR" in screen or "iFgmr.com IAS Administrator Menu" in screen:
                logger.info("Detected Administrator Menu. Selecting option 21...")
                
                # Enter option 21
                client.sendText("21")
                logger.info("Entered option: 21")
                
                # Press Enter to select
                client.sendEnter()
                logger.info("Selected option 21")
                time.sleep(3)  # Wait for response
                
                # Get the final screen
                final_screen = client.getScreen()
                client.saveScreen(fileName='05_final.html')
                logger.info("Final screen after selecting option 21:")
                logger.info("-" * 50)
                logger.info(final_screen)
                logger.info("-" * 50)
            else:
                logger.info("Not on Administrator Menu, continuing...")
                
        except Exception as e:
            logger.error(f"Error during Step 4 (Administrator Menu): {str(e)}")
        
        # Step 5: Handle Company Maintenance screen - Add new company
        logger.info("Step 5: Processing Company Maintenance screen...")
        try:
            screen = client.getScreen()
            client.saveScreen(fileName='05_company_maintenance.html')
            logger.info("Company Maintenance screen content:")
            logger.info("-" * 50)
            logger.info(screen)
            logger.info("-" * 50)
            
            # Check if we're on the Company Maintenance screen
            if "Company Maintenance" in screen and "Option" in screen:
                logger.info("Detected Company Maintenance screen. Adding new company...")
                
                # Enter option "A" for Add
                client.sendText(COMPANY_OPTION)
                logger.info(f"Entered option: {COMPANY_OPTION} (Add)")
                # Tab to Company field and enter company ID
                # client.sendTab()
                client.sendText(NEW_COMPANY_ID)
                logger.info(f"Entered company ID: {NEW_COMPANY_ID}")
                
                # Press Enter to proceed
                client.sendEnter()
                logger.info("Submitted option and company ID")
                time.sleep(3)  # Wait for response
            else:
                logger.info("Not on Company Maintenance screen, continuing...")
                
        except Exception as e:
            logger.error(f"Error during Step 5 (Company Maintenance): {str(e)}")
        
        # Step 6: Handle Company Details form
        logger.info("Step 6: Processing Company Details form...")
        try:
            screen = client.getScreen()
            client.saveScreen(fileName='06_company_details.html')
            logger.info("Company Details form content:")
            logger.info("-" * 50)
            logger.info(screen)
            logger.info("-" * 50)
            
            # Check if we're on the Company Details form
            if "Name" in screen and "Address" in screen and "Company Type" in screen:
                logger.info("Detected Company Details form. Filling in company information...")
                
                # Move to first input field (should be Name)
                client.moveToFirstInputField()
                client.sendText(COMPANY_DATA['COMPANY_NAME'])
                logger.info(f"Entered company name: {COMPANY_DATA['COMPANY_NAME']}")
                
                # Tab to Address field (only if name is not at max 28 chars)
                if not should_auto_tab('COMPANY_NAME', COMPANY_DATA['COMPANY_NAME']):
                    client.sendTab()
                client.sendTab()

                client.sendText(COMPANY_DATA['COMPANY_ADDRESS'])
                logger.info(f"Entered company address: {COMPANY_DATA['COMPANY_ADDRESS']}")
                
                # Tab to Location field (only if address is not at max 60 chars)
                if not should_auto_tab('COMPANY_ADDRESS', COMPANY_DATA['COMPANY_ADDRESS']):
                    # Tab to Location field
                    if len(COMPANY_DATA['COMPANY_ADDRESS']) < 30:
                        client.sendTab()
                    client.sendTab()
                    
                client.sendText(COMPANY_DATA['COMPANY_LOCATION'])
                logger.info(f"Entered company location: {COMPANY_DATA['COMPANY_LOCATION']}")
                
                # Tab to Region field (only if location is not at max 20 chars)
                if not should_auto_tab('COMPANY_LOCATION', COMPANY_DATA['COMPANY_LOCATION']):
                    client.sendTab()
                client.sendText(COMPANY_DATA['COMPANY_REGION'])
                logger.info(f"Entered company region: {COMPANY_DATA['COMPANY_REGION']}")
                
                # Tab to Postal Code field (only if region is not at max 2 chars)
                if not should_auto_tab('COMPANY_REGION', COMPANY_DATA['COMPANY_REGION']):
                    client.sendTab()
                client.sendText(COMPANY_DATA['COMPANY_POSTAL_CODE'])
                logger.info(f"Entered company postal code: {COMPANY_DATA['COMPANY_POSTAL_CODE']}")

                # Tab to Country field (only if postal code is not at max 10 chars)
                if not should_auto_tab('COMPANY_POSTAL_CODE', COMPANY_DATA['COMPANY_POSTAL_CODE']):
                    client.sendTab()
                client.sendText(COMPANY_DATA['COMPANY_COUNTRY'])
                logger.info(f"Entered company country: {COMPANY_DATA['COMPANY_COUNTRY']}")
                
                # Skip Phone Number field (leave empty)
                if not should_auto_tab('COMPANY_COUNTRY', COMPANY_DATA['COMPANY_COUNTRY']):
                    client.sendTab()
                if COMPANY_DATA['COMPANY_PHONE']:
                    client.sendText(COMPANY_DATA['COMPANY_PHONE'])
                    logger.info(f"Entered company phone: {COMPANY_DATA['COMPANY_PHONE']}")
                    # Only tab if phone is not at max 10 digits
                else:
                    client.sendTab()
                    client.sendTab()
                    logger.info("Skipped company phone (empty)")
                
                # Skip Fax Number field (leave empty)
                if not should_auto_tab('COMPANY_PHONE', COMPANY_DATA['COMPANY_PHONE']):
                    client.sendTab()
                if COMPANY_DATA['COMPANY_FAX']:
                    client.sendText(COMPANY_DATA['COMPANY_FAX'])
                    logger.info(f"Entered company fax: {COMPANY_DATA['COMPANY_FAX']}")
                    # Only tab if fax is not at max 10 digits 
                else:
                    client.sendTab()
                    client.sendTab()
                    logger.info("Skipped company fax (empty)")

                if not should_auto_tab('COMPANY_FAX', COMPANY_DATA['COMPANY_FAX']):
                    client.sendTab()
                # Tab to Company Type field
                client.sendText(COMPANY_DATA['COMPANY_TYPE'])
                logger.info(f"Entered company type: {COMPANY_DATA['COMPANY_TYPE']}")
                # Company type is 1 char max, so it will auto-tab
                
                # Tab to Periods Per Year field
                client.sendText(COMPANY_DATA['PERIODS_PER_YEAR'])
                logger.info(f"Entered periods per year: {COMPANY_DATA['PERIODS_PER_YEAR']}")
                # Periods per year is 2 digits max, so it will auto-tab
                
                # Tab to Fiscal Year Ending field
                client.sendText(COMPANY_DATA['FISCAL_YEAR_ENDING'])
                logger.info(f"Entered fiscal year ending: {COMPANY_DATA['FISCAL_YEAR_ENDING']}")
                # Fiscal year ending is 2 digits max, so it will auto-tab
                
                # Tab to Closing Account field
                client.sendTab()
                client.sendText(COMPANY_DATA['CLOSING_ACCOUNT'])
                logger.info(f"Entered closing account: {COMPANY_DATA['CLOSING_ACCOUNT']}")
                # Closing account is 6 digits max, so it will auto-tab
                
                # Tab to Base Currency field
                client.sendText(COMPANY_DATA['BASE_CURRENCY'])
                logger.info(f"Entered base currency: {COMPANY_DATA['BASE_CURRENCY']}")
                # Base currency is 3 chars max, so it will auto-tab
                
                # Tab to Exchange Account field
                client.sendTab()
                client.sendText(COMPANY_DATA['EXCHANGE_ACCOUNT'])
                logger.info(f"Entered exchange account: {COMPANY_DATA['EXCHANGE_ACCOUNT']}")
                # Exchange account is 6 digits max, so it will auto-tab

                # Get the screen before submission
                final_screen = client.getScreen()
                client.saveScreen(fileName='07_before_result.html')
                logger.info("screen before submitting company details:")
                logger.info("-" * 50)
                logger.info(final_screen)
                logger.info("-" * 50)
                
                # Press Enter to submit the form
                client.sendEnter()
                logger.info("Submitted company details form")
                time.sleep(1)  # Wait for response
                
                # Get the final screen after submission
                final_screen = client.getScreen()
                client.saveScreen(fileName='07_final_result.html')
                logger.info("Final screen after submitting company details:")
                logger.info("-" * 50)
                logger.info(final_screen)
                logger.info("-" * 50)
                
                # Check if the company was added successfully or if there was an error
                if f"{NEW_COMPANY_ID} added" in final_screen:
                    logger.info(f"SUCCESS: Company {NEW_COMPANY_ID} was added successfully!")
                elif "Invalid country" in final_screen:
                    logger.error(f"ERROR: Invalid country - {COMPANY_DATA['COMPANY_COUNTRY']}")
                elif "Invalid" in final_screen or "Error" in final_screen:
                    # Check for other validation errors
                    lines = final_screen.split('\n')
                    error_messages = [line.strip() for line in lines if 'Invalid' in line or 'Error' in line]
                    if error_messages:
                        logger.error(f"VALIDATION ERROR: {'; '.join(error_messages)}")
                    else:
                        logger.error("ERROR: Unknown validation error occurred")
                else:
                    logger.warning("UNKNOWN: Could not determine if company was added successfully. Please check the screen manually.")
            else:
                # get the comapny doesnt exist errior here properly
                logger.info("Not on Company Details form, continuing...")
                
        except Exception as e:
            logger.error(f"Error during Step 6 (Company Details form): {str(e)}")
        
        logger.info("Automated sequence completed successfully!")
        
        # Example: If this was a real automation script, here we'd:
        # 1. Process the screen content
        # 2. Determine the current state (login, menu, etc.)
        # 3. Take appropriate actions (enter credentials, select menu options)
        
        # Disconnect
        logger.info("Demonstration complete. Disconnecting...")
        cleanup_connection(client)
        _global_client = None  # Clear global reference
        
    except Exception as e:
        logger.error(f"Unexpected error during execution: {str(e)}")
        # Make sure to try disconnecting even if there was an error
        if 'client' in locals() and client:
            cleanup_connection(client)
        _global_client = None  # Clear global reference

# ------------------------- Script Entry Point -------------------------
if __name__ == "__main__":
    main()
