"""
API Screen Handler Module

This module provides a screen handler that works with database data
instead of CSV files, designed for REST API usage.
"""

import time
import logging
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

class ApiScreenHandler:
    """API-compatible screen handler for TN5250 screens"""
    
    def __init__(self, 
                 screen_config: Dict[str, Any],
                 field_configs: List[Dict[str, Any]],
                 navigation_steps: List[Dict[str, Any]],
                 screen_data: Dict[str, str]):
        self.screen_config = screen_config
        self.field_configs = field_configs
        self.navigation_steps = navigation_steps
        self.screen_data = screen_data
        
        # Convert to internal format for compatibility
        self.field_config = {}
        for field_config in field_configs:
            self.field_config[field_config['field_name']] = {
                'max_length': field_config['max_length'],
                'required': field_config['required'],
                'type': field_config['type'],
                'valid_values': field_config['valid_values'],
                'tabs_needed': field_config['tabs_needed'],
                'tabs_needed_empty': field_config['tabs_needed_empty'],
                'description': field_config['description']
            }
        
        # Convert navigation steps to internal format
        self.navigation_steps_dict = []
        for nav_step in sorted(navigation_steps, key=lambda x: x['step_order']):
            self.navigation_steps_dict.append({
                'step_order': nav_step['step_order'],
                'screen_title_contains': nav_step['screen_title_contains'],
                'action_type': nav_step['action_type'],
                'action_value': nav_step['action_value'],
                'wait_time': nav_step['wait_time'],
                'description': nav_step['description']
            })
        
        # Create output directory for HTML files
        self.output_directory = self._create_output_directory()
    
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
        
        return os.path.join(self.output_directory, timestamped_name)
    
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
    
    def validate_all_fields(self) -> Tuple[bool, List[str]]:
        """Validate all screen data fields and return status with messages"""
        logger.info("Validating all screen data fields...")
        all_valid = True
        messages = []
        
        for field_name, value in self.screen_data.items():
            is_valid, message = self.validate_field(field_name, value)
            if not is_valid:
                error_msg = f"VALIDATION ERROR - {message}"
                logger.error(error_msg)
                messages.append(error_msg)
                all_valid = False
            else:
                config = self.field_config.get(field_name, {})
                max_length = config.get('max_length', 0)
                success_msg = f"✓ {field_name}: '{value}' ({len(value)}/{max_length} chars)"
                logger.info(success_msg)
                messages.append(success_msg)
        
        return all_valid, messages
    
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
    
    def check_for_screen_errors(self, screen: str) -> Tuple[bool, str]:
        """Check screen content for error messages or invalid states"""
        lines = screen.split('\n')
        
        # Common error patterns to check for
        error_patterns = [
            "Invalid",
            "Error", 
            "already exists",
            "not found",
            "unauthorized",
            "access denied",
            "invalid option",
            "invalid command",
            "invalid entry",
            "duplicate",
            "cannot",
            "unable to",
            "failed"
        ]
        
        # Look for error messages in screen content
        for line in lines:
            line_lower = line.lower().strip()
            for pattern in error_patterns:
                if pattern.lower() in line_lower and line_lower:
                    return True, f"Error detected: {line.strip()}"
        
        # Check for specific success patterns
        success_patterns = [
            "added successfully",
            "updated successfully", 
            "completed successfully",
            "successful",
            "added",
            "updated",
            "completed"
        ]
        
        for line in lines:
            line_lower = line.lower().strip()
            for pattern in success_patterns:
                if pattern.lower() in line_lower and line_lower:
                    return False, f"Success: {line.strip()}"
        
        return False, "No errors detected"

    def execute_navigation_step(self, client, step: Dict[str, Any], screen: str, **kwargs) -> Tuple[bool, str]:
        """Execute a single navigation step and return result with message"""
        step_order = step['step_order']
        screen_title_contains = step['screen_title_contains']
        action_type = step['action_type']
        action_value = step['action_value']
        wait_time = step['wait_time']
        description = step['description']
        
        logger.info(f"Step {step_order}: {description}")
        
        # Check if we're on the expected screen
        if screen_title_contains not in screen:
            msg = f"Not on expected screen (looking for '{screen_title_contains}'), skipping step..."
            logger.info(msg)
            return False, msg
        
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
                # Select option and enter ID (e.g., "A,{COMPANY_ID}" or "{OPERATION},{COMPANY_ID}")
                parts = action_value.split(',')
                
                # Handle placeholders
                processed_parts = []
                for part in parts:
                    if part == '{COMPANY_ID}':
                        processed_parts.append(kwargs.get('company_id', ''))
                    elif part == '{OPERATION}':
                        processed_parts.append(kwargs.get('operation', ''))
                    else:
                        processed_parts.append(part)
                
                # Send each part
                for part in processed_parts:
                    client.sendText(part)
                
                client.sendEnter()
                logger.info(f"Selected option with values: {', '.join(processed_parts)}")
                
            elif action_type == 'form_fill':
                # Fill the main form
                final_screen, result_msg = self.fill_form(client, kwargs.get('company_id'))
                return True, result_msg  # Form filling is the final step
            
            # Wait for the specified time
            time.sleep(wait_time)
            
            # Check the screen after action for errors
            post_action_screen = client.getScreen()
            has_error, error_msg = self.check_for_screen_errors(post_action_screen)
            
            if has_error:
                logger.error(f"Error detected after step {step_order}: {error_msg}")
                return False, error_msg
            
            success_msg = f"Step {step_order} completed successfully"
            logger.info(success_msg)
            return True, success_msg
            
        except Exception as e:
            error_msg = f"Error executing step {step_order}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
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

    def fill_form(self, client, company_id: str = None) -> Tuple[str, str]:
        """Fill the main form with data and return final screen with result message"""
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
        
        # Check result and return message
        effective_company_id = company_id or self.screen_data.get('company_id', '')
        result_msg = self.check_result(final_screen, effective_company_id)
        
        return final_screen, result_msg
    
    def process_screen(self, client, company_id: str = None, operation: str = None, **kwargs) -> Tuple[bool, List[str]]:
        """Process the entire screen flow and return result with messages
        
        Args:
            client: The TN5250 client
            company_id: The company ID to use for this operation (overrides screen_data)
            operation: The operation type (A=Add, C=Change, D=Delete, etc.)
            **kwargs: Additional parameters like username, password, etc.
        """
        logger.info("Starting screen processing...")
        logger.info(f"HTML files will be saved to directory: {self.output_directory}")
        
        # Use provided company_id and operation, or fall back to screen_data/config
        effective_company_id = company_id or self.screen_data.get('company_id') or self.screen_config.get('company_id')
        effective_operation = operation or self.screen_data.get('operation') or self.screen_config.get('operation')
        
        if not effective_company_id:
            error_msg = "No company_id provided in parameters, screen_data, or configuration"
            logger.error(error_msg)
            return False, [error_msg]
        
        if not effective_operation:
            error_msg = "No operation provided in parameters, screen_data, or configuration"
            logger.error(error_msg)
            return False, [error_msg]
        
        logger.info(f"Using company_id: {effective_company_id}, operation: {effective_operation}")
        
        # Add effective values to kwargs for navigation steps
        kwargs['company_id'] = effective_company_id
        kwargs['operation'] = effective_operation
        
        messages = []
        
        # Validate all fields first
        validation_success, validation_messages = self.validate_all_fields()
        messages.extend(validation_messages)
        
        if not validation_success:
            error_msg = "Field validation failed. Cannot proceed."
            logger.error(error_msg)
            messages.append(error_msg)
            return False, messages
        
        step_number = 1
        
        # Execute navigation steps
        for step in self.navigation_steps_dict:
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
                
                # Check screen for errors before executing step
                has_error, error_msg = self.check_for_screen_errors(screen)
                if has_error:
                    logger.error(f"Error detected on screen before step {step_number}: {error_msg}")
                    messages.append(f"Pre-step error: {error_msg}")
                    return False, messages
                
                # Execute the step
                if step['action_type'] == 'form_fill':
                    # Final step - fill the form
                    final_screen, result_msg = self.fill_form(client, effective_company_id)
                    messages.append(result_msg)
                    # Check if result indicates success or failure
                    success = "SUCCESS" in result_msg or "added successfully" in result_msg.lower()
                    return success, messages
                else:
                    # Regular navigation step
                    success, step_msg = self.execute_navigation_step(client, step, screen, **kwargs)
                    messages.append(step_msg)
                    
                    if not success:
                        logger.error(f"Step {step_number} failed: {step_msg}")
                        return False, messages
                
                step_number += 1
                
            except Exception as e:
                error_msg = f"Error in step {step_number}: {str(e)}"
                logger.error(error_msg)
                messages.append(error_msg)
                return False, messages
        
        success_msg = "Screen processing completed successfully!"
        logger.info(success_msg)
        messages.append(success_msg)
        return True, messages
    
    def check_result(self, final_screen: str, company_id: str) -> str:
        """Check the final result of the operation and return result message"""
        logger.info("Final screen after submission:")
        logger.info("-" * 50)
        logger.info(final_screen)
        logger.info("-" * 50)
        
        # Split screen into lines for analysis
        lines = final_screen.split('\n')
        
        # Check for success or error messages
        if f"{company_id} added" in final_screen:
            result_msg = f"SUCCESS: Company {company_id} was added successfully!"
            logger.info(result_msg)
            return result_msg
        elif "Invalid country" in final_screen:
            result_msg = "ERROR: Invalid country code"
            logger.error(result_msg)
            return result_msg
        elif "already exists" in final_screen.lower():
            result_msg = f"ERROR: Company {company_id} already exists"
            logger.error(result_msg)
            return result_msg
        elif "Invalid" in final_screen or "Error" in final_screen:
            # Check for other validation errors
            error_messages = [line.strip() for line in lines if 'Invalid' in line or 'Error' in line]
            if error_messages:
                result_msg = f"VALIDATION ERROR: {'; '.join(error_messages)}"
                logger.error(result_msg)
                return result_msg
            else:
                # Look for error message in last line before function keys
                for i, line in enumerate(lines):
                    if 'F3=Exit' in line and i > 0:
                        error_line = lines[i-1].strip()
                        if error_line:
                            result_msg = f"ERROR: {error_line}"
                            logger.error(result_msg)
                            return result_msg
                else:
                    result_msg = "ERROR: Unknown validation error occurred"
                    logger.error(result_msg)
                    return result_msg
        else:
            # Look for error message in last line before function keys
            for i, line in enumerate(lines):
                if 'F3=Exit' in line and i > 0:
                    error_line = lines[i-1].strip()
                    if error_line:
                        result_msg = f"ERROR: {error_line}"
                        logger.error(result_msg)
                        return result_msg
            else:
                result_msg = "UNKNOWN: Could not determine if operation was successful. Please check the screen manually."
                logger.warning(result_msg)
                return result_msg 