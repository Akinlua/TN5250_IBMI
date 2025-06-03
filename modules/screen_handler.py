"""
Screen Handler Module

This module provides a generic screen handler that can process any screen
based on CSV configuration files for data and field configurations.
"""

import csv
import time
import logging
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

class ScreenHandler:
    """Generic screen handler for TN5250 screens"""
    
    def __init__(self, data_file: str, config_file: str, navigation_file: str):
        self.data_file = data_file
        self.config_file = config_file
        self.navigation_file = navigation_file
        self.screen_data = {}
        self.field_config = {}
        self.navigation_steps = []
        
        # Create output directory for HTML files
        self.output_dir = self._create_output_directory()
        
        self.load_configurations()
    
    def _create_output_directory(self) -> str:
        """Create a timestamped output directory for HTML files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"screen_output_{timestamp}"
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
            return output_dir
        except Exception as e:
            logger.warning(f"Could not create output directory {output_dir}: {str(e)}")
            logger.info("HTML files will be saved to current directory")
            return "."
    
    def _get_html_filename(self, base_name: str) -> str:
        """Generate full path for HTML file with timestamp to prevent appending"""
        # Add timestamp to filename to prevent file appending
        timestamp = datetime.now().strftime("%H%M%S")
        name_parts = base_name.split('.')
        if len(name_parts) > 1:
            # Insert timestamp before file extension
            timestamped_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
        else:
            # No extension, just add timestamp
            timestamped_name = f"{base_name}_{timestamp}"
        
        return os.path.join(self.output_dir, timestamped_name)
    
    def load_configurations(self):
        """Load all configuration files"""
        self.load_screen_data()
        self.load_field_config()
        self.load_navigation_steps()
    
    def load_screen_data(self):
        """Load screen data from CSV file"""
        try:
            with open(self.data_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    self.screen_data[row['FIELD_NAME']] = row['VALUE']
            logger.info(f"Loaded {len(self.screen_data)} data fields from {self.data_file}")
        except FileNotFoundError:
            logger.error(f"Data file not found: {self.data_file}")
            raise
        except Exception as e:
            logger.error(f"Error loading data file: {str(e)}")
            raise
    
    def load_field_config(self):
        """Load field configuration from CSV file"""
        try:
            with open(self.config_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    field_name = row['FIELD_NAME']
                    self.field_config[field_name] = {
                        'max_length': int(row['MAX_LENGTH']),
                        'required': row['REQUIRED'].lower() == 'true',
                        'type': row['TYPE'],
                        'valid_values': row['VALID_VALUES'].split(',') if row['VALID_VALUES'] else None,
                        'tabs_needed': int(row['TABS_NEEDED']),
                        'tabs_needed_empty': int(row.get('TABS_NEEDED_EMPTY', row['TABS_NEEDED'])),  # Default to TABS_NEEDED if not specified
                        'description': row['DESCRIPTION']
                    }
            logger.info(f"Loaded {len(self.field_config)} field configurations from {self.config_file}")
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_file}")
            raise
        except Exception as e:
            logger.error(f"Error loading config file: {str(e)}")
            raise
    
    def load_navigation_steps(self):
        """Load navigation steps from CSV file"""
        try:
            with open(self.navigation_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    self.navigation_steps.append({
                        'step_order': int(row['STEP_ORDER']),
                        'screen_title_contains': row['SCREEN_TITLE_CONTAINS'],
                        'action_type': row['ACTION_TYPE'],
                        'action_value': row['ACTION_VALUE'],
                        'wait_time': int(row['WAIT_TIME']),
                        'description': row['DESCRIPTION']
                    })
            # Sort by step order
            self.navigation_steps.sort(key=lambda x: x['step_order'])
            logger.info(f"Loaded {len(self.navigation_steps)} navigation steps from {self.navigation_file}")
        except FileNotFoundError:
            logger.error(f"Navigation file not found: {self.navigation_file}")
            raise
        except Exception as e:
            logger.error(f"Error loading navigation file: {str(e)}")
            raise
    
    def validate_field(self, field_name: str, value: str) -> Tuple[bool, str]:
        """Validate a field against its configuration"""
        if field_name not in self.field_config:
            return False, f"Unknown field: {field_name}"
        
        config = self.field_config[field_name]
        
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
        if config['valid_values'] and value not in config['valid_values']:
            return False, f"{field_name} must be one of {config['valid_values']} (current: {value})"
        
        return True, "Valid"
    
    def validate_all_fields(self) -> bool:
        """Validate all screen data fields"""
        logger.info("Validating all screen data fields...")
        all_valid = True
        
        for field_name, value in self.screen_data.items():
            is_valid, message = self.validate_field(field_name, value)
            if not is_valid:
                logger.error(f"VALIDATION ERROR - {message}")
                all_valid = False
            else:
                config = self.field_config.get(field_name, {})
                max_length = config.get('max_length', 0)
                logger.info(f"✓ {field_name}: '{value}' ({len(value)}/{max_length} chars)")
        
        return all_valid
    
    def should_auto_tab(self, field_name: str, value: str) -> bool:
        """Determine if field will auto-tab based on length"""
        if field_name not in self.field_config:
            return False
        
        max_length = self.field_config[field_name]['max_length']
        return len(value) >= max_length
    
    def send_field_data(self, client, field_name: str, value: str):
        """Send field data and handle tabbing based on field configuration"""
        config = self.field_config.get(field_name, {})
        tabs_needed = config.get('tabs_needed', 1)
        tabs_needed_empty = config.get('tabs_needed_empty', tabs_needed)
        max_length = config.get('max_length', 0)
        
        if not value:  # Empty field
            logger.info(f"Skipping {field_name} (empty)")
            # Send the configured number of tabs for empty fields
            for _ in range(tabs_needed_empty):
                client.sendTab()
            logger.debug(f"Sent {tabs_needed_empty} tabs for empty field {field_name}")
            return
        
        client.sendText(value)
        logger.info(f"Entered {field_name}: '{value}' ({len(value)}/{max_length} chars)")
        
        # Calculate how many tabs to send
        will_auto_tab = self.should_auto_tab(field_name, value)
        
        if will_auto_tab:
            # Field will auto-tab, but we might need additional tabs
            additional_tabs = tabs_needed - 1  # Subtract 1 because auto-tab acts as 1 tab
            if additional_tabs > 0:
                for _ in range(additional_tabs):
                    client.sendTab()
                logger.debug(f"Sent {additional_tabs} additional tabs after auto-tab for {field_name}")
            else:
                logger.debug(f"No additional tabs needed for {field_name} (auto-tab sufficient)")
        else:
            # Field won't auto-tab, send all configured tabs
            for _ in range(tabs_needed):
                client.sendTab()
            logger.debug(f"Sent {tabs_needed} tabs after {field_name} (no auto-tab)")
    
    def execute_navigation_step(self, client, step: Dict[str, Any], screen: str, **kwargs) -> bool:
        """Execute a single navigation step"""
        step_order = step['step_order']
        screen_title_contains = step['screen_title_contains']
        action_type = step['action_type']
        action_value = step['action_value']
        wait_time = step['wait_time']
        description = step['description']
        
        logger.info(f"Step {step_order}: {description}")
        
        # Check if we're on the expected screen
        if screen_title_contains not in screen:
            logger.info(f"Not on expected screen (looking for '{screen_title_contains}'), skipping step...")
            return False
        
        try:
            if action_type == 'credentials':
                # Handle login credentials
                username, password = action_value.split(',')
                client.moveToFirstInputField()
                client.sendText(kwargs.get('username', username))
                client.sendTab()
                client.sendText(kwargs.get('password', password))
                client.sendEnter()
                logger.info("Entered credentials and submitted")
                
            elif action_type == 'enter':
                # Just press enter
                client.sendEnter()
                logger.info("Pressed Enter")
                
            elif action_type == 'command':
                # Send a command
                client.sendText(action_value)
                client.sendEnter()
                logger.info(f"Executed command: {action_value}")
                
            elif action_type == 'option':
                # Select a menu option
                client.sendText(action_value)
                client.sendEnter()
                logger.info(f"Selected option: {action_value}")
                
            elif action_type == 'option_with_id':
                # Select option and enter ID (e.g., "A,{COMPANY_ID}")
                parts = action_value.split(',')
                option = parts[0]
                company_id = kwargs.get('company_id', parts[1].replace('{COMPANY_ID}', ''))
                
                client.sendText(option)
                client.sendText(company_id)
                client.sendEnter()
                logger.info(f"Selected option {option} with ID {company_id}")
                
            elif action_type == 'form_fill':
                # Fill the main form
                self.fill_form(client)
                return True  # Form filling is the final step
            
            # Wait for the specified time
            time.sleep(wait_time)
            return True
            
        except Exception as e:
            logger.error(f"Error executing step {step_order}: {str(e)}")
            return False
    
    def _save_screen_to_html(self, client, filename: str):
        """Get screen content and save it to an HTML file manually"""
        try:
            # Get the screen content
            screen_content = client.getScreen()
            
            # Create proper HTML structure
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>TN5250 Screen Capture</title>
    <style>
        body {{
            font-family: 'Courier New', monospace;
            background-color: #000;
            color: #00ff00;
            white-space: pre;
            margin: 20px;
            line-height: 1.2;
        }}
        .screen-content {{
            border: 1px solid #00ff00;
            padding: 10px;
            background-color: #001100;
        }}
        .timestamp {{
            color: #ffff00;
            font-size: 12px;
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="timestamp">Captured: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
    <div class="screen-content">{screen_content}</div>
</body>
</html>"""
            
            # Get the full file path
            full_path = self._get_html_filename(filename)
            
            # Write to file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Screen manually saved to: {full_path}")
            
        except Exception as e:
            logger.error(f"Error saving screen to HTML: {str(e)}")

    def fill_form(self, client):
        """Fill the main form with data"""
        logger.info("Starting form fill process...")
        
        # Move to first input field
        client.moveToFirstInputField()
        
        # Process each field in order
        for field_name, value in self.screen_data.items():
            if field_name in self.field_config:
                self.send_field_data(client, field_name, value)
            else:
                logger.warning(f"No configuration found for field: {field_name}")
        
        # Get screen before submission
        screen = client.getScreen()
        logger.info("Screen before submission:")
        logger.info("-" * 50)
        logger.info(screen)
        logger.info("-" * 50)
        
        # Save screen manually to HTML file
        self._save_screen_to_html(client, 'before_submission.html')
        
        # Submit the form
        client.sendEnter()
        logger.info("Submitted form")
        time.sleep(1)
        
        # Get final screen
        final_screen = client.getScreen()
        logger.info("Screen after submission:")
        logger.info("-" * 50)
        logger.info(final_screen)
        logger.info("-" * 50)
        
        # Save screen manually to HTML file
        self._save_screen_to_html(client, 'after_submission.html')
        
        return final_screen
    
    def process_screen(self, client, **kwargs) -> bool:
        """Process the entire screen flow"""
        logger.info("Starting screen processing...")
        logger.info(f"HTML files will be saved to directory: {self.output_dir}")
        
        # Validate all fields first
        if not self.validate_all_fields():
            logger.error("Field validation failed. Cannot proceed.")
            return False
        
        step_number = 1
        
        # Execute navigation steps
        for step in self.navigation_steps:
            logger.info(f"Executing navigation step {step_number}...")
            
            try:
                # Get current screen
                screen = client.getScreen()
                logger.info(f"Current screen content:")
                logger.info("-" * 50)
                logger.info(screen)
                logger.info("-" * 50)
                
                # Save screen manually to HTML file
                self._save_screen_to_html(client, f'step_{step_number:02d}_{step["action_type"]}.html')
                
                # Execute the step
                if step['action_type'] == 'form_fill':
                    # Final step - fill the form
                    final_screen = self.fill_form(client)
                    self.check_result(final_screen, kwargs.get('company_id', ''))
                    return True
                else:
                    # Regular navigation step
                    success = self.execute_navigation_step(client, step, screen, **kwargs)
                    if not success:
                        logger.warning(f"Step {step_number} was skipped or failed")
                
                step_number += 1
                
            except Exception as e:
                logger.error(f"Error in step {step_number}: {str(e)}")
                return False
        
        logger.info("Screen processing completed successfully!")
        return True
    
    def check_result(self, final_screen: str, company_id: str):
        """Check the final result of the operation"""
        logger.info("Final screen after submission:")
        logger.info("-" * 50)
        logger.info(final_screen)
        logger.info("-" * 50)
        
        # Split screen into lines for analysis
        lines = final_screen.split('\n')
        
        # Check for success or error messages
        if f"{company_id} added" in final_screen:
            logger.info(f"SUCCESS: Company {company_id} was added successfully!")
        elif "Invalid country" in final_screen:
            logger.error("ERROR: Invalid country code")
        elif "Invalid" in final_screen or "Error" in final_screen:
            # Check for other validation errors
            error_messages = [line.strip() for line in lines if 'Invalid' in line or 'Error' in line]
            if error_messages:
                logger.error(f"VALIDATION ERROR: {'; '.join(error_messages)}")
            else:
                # Look for error message in last line before function keys
                for i, line in enumerate(lines):
                    if 'F3=Exit' in line and i > 0:
                        error_line = lines[i-1].strip()
                        if error_line:
                            logger.error(f"ERROR: {error_line}")
                            break
                else:
                    logger.error("ERROR: Unknown validation error occurred")
        else:
            # Look for error message in last line before function keys
            for i, line in enumerate(lines):
                if 'F3=Exit' in line and i > 0:
                    error_line = lines[i-1].strip()
                    if error_line:
                        logger.error(f"ERROR: {error_line}")
                        break
            else:
                logger.warning("UNKNOWN: Could not determine if operation was successful. Please check the screen manually.")