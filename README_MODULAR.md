# Modular TN5250 Interaction System

This is a modular Python framework for automating interactions with TN5250 servers (IBM i systems). The system is designed to be highly configurable using CSV files for data and screen configurations, making it easy to support multiple screens and different data sets without modifying the core code.

## Features

- **Modular Design**: Separate modules for screen handling and connection management
- **CSV-Driven Configuration**: Data and field configurations stored in CSV files
- **Multiple Screen Support**: Easy to add new screens by creating configuration files
- **Flexible Tab Handling**: Configurable tab behavior for each field, including separate settings for empty fields
- **Field Validation**: Comprehensive validation with type checking and length limits
- **Auto-Tab Detection**: Intelligent handling of fields that auto-tab when filled
- **Screen Capture**: Automatic saving of HTML screens with timestamped directories
- **Error Handling**: Robust error handling and cleanup
- **Environment Validation**: Checks dependencies and connectivity before execution

## Directory Structure

```
.
├── main_modular.py              # Main entry point
├── test_html_saving.py          # HTML saving functionality test
├── config/
│   └── screen_configs.py        # Screen and connection configurations
├── modules/
│   ├── screen_handler.py        # Generic screen processing logic
│   └── connection_manager.py    # Connection management utilities
├── screens/
│   ├── company_maintenance_data.csv     # Company data
│   ├── company_maintenance_config.csv   # Company field configuration
│   ├── customer_maintenance_data.csv    # Customer data (example)
│   ├── customer_maintenance_config.csv  # Customer field configuration (example)
│   └── navigation_config.csv            # Navigation steps
├── screen_output_YYYYMMDD_HHMMSS/       # Timestamped HTML output directories
└── README_MODULAR.md           # This file
```

## Installation

1. Install Python dependencies:
   ```bash
   pip install p5250
   ```

2. Install s3270 utility:
   - **macOS**: `brew install x3270`
   - **Linux**: `apt-get install x3270` or equivalent
   - **Windows**: Download from http://x3270.bgp.nu/download.html

## Usage

### Basic Usage

Run the system with the default screen (company_maintenance):
```bash
python main_modular.py
```

Run with a specific screen:
```bash
python main_modular.py company_maintenance
python main_modular.py customer_maintenance
python main_modular.py vendor_maintenance
```

### Configuration Files

#### 1. Screen Data (CSV)
Example: `screens/company_maintenance_data.csv`
```csv
FIELD_NAME,VALUE
COMPANY_NAME,TEST COMPANY 10
COMPANY_ADDRESS,123 MAIN STREET
COMPANY_LOCATION,ST CLOUD
...
```

#### 2. Field Configuration (CSV)
Example: `screens/company_maintenance_config.csv`
```csv
FIELD_NAME,MAX_LENGTH,REQUIRED,TYPE,VALID_VALUES,TABS_NEEDED,TABS_NEEDED_EMPTY,DESCRIPTION
COMPANY_NAME,28,True,text,,1,1,Company name field
COMPANY_ADDRESS,60,True,text,,2,2,Company address field (spans 2 lines)
COMPANY_PHONE,10,False,digits,,2,1,Company phone number field
COMPANY_TYPE,1,True,text,"F,S",1,1,Company type (F=Full S=Subsidiary)
...
```

**Field Configuration Parameters:**
- `MAX_LENGTH`: Maximum allowed characters
- `REQUIRED`: True/False - whether field is mandatory
- `TYPE`: `text` or `digits` - data type validation
- `VALID_VALUES`: Comma-separated list of allowed values (optional)
- `TABS_NEEDED`: Number of tabs to send after entering data when field has content
- `TABS_NEEDED_EMPTY`: Number of tabs to send when field is empty (skipped)
- `DESCRIPTION`: Human-readable description

#### 3. Navigation Configuration (CSV)
Example: `screens/navigation_config.csv`
```csv
SCREEN_NAME,STEP_ORDER,SCREEN_TITLE_CONTAINS,ACTION_TYPE,ACTION_VALUE,WAIT_TIME,DESCRIPTION
company_maintenance,1,Sign On,credentials,"USERNAME,PASSWORD",3,Enter login credentials
company_maintenance,2,Press Enter to continue,enter,,2,Press enter to continue
company_maintenance,3,IBM i Main Menu,command,CALL PGM(LOADERP) PARM(('*ADMIN') ('AdminAaBb')),3,Execute program
company_maintenance,4,*ADMINISTRATOR,option,21,3,Select company maintenance option
...
```

**Navigation Actions:**
- `credentials`: Enter username and password
- `enter`: Press Enter key
- `command`: Send a command string
- `option`: Select a menu option
- `option_with_id`: Select option and enter ID
- `form_fill`: Fill the main data entry form

#### 4. Screen Configuration (Python)
Example: `config/screen_configs.py`
```python
SCREEN_CONFIGS = {
    'company_maintenance': {
        'option': '21',
        'company_id': '689',
        'operation': 'A',  # A=Add, C=Change, D=Delete
        'data_file': 'screens/company_maintenance_data.csv',
        'config_file': 'screens/company_maintenance_config.csv',
        'navigation_file': 'screens/navigation_config.csv',
        'description': 'Company Maintenance Screen - Add new company'
    }
}
```

## Tab Behavior

The system handles tabbing intelligently based on field configuration:

1. **Auto-Tab Fields**: Fields that reach maximum length will auto-tab
2. **Additional Tabs**: If `TABS_NEEDED > 1`, additional tabs are sent after auto-tab
3. **Manual Tabs**: For fields not at max length, all configured tabs are sent
4. **Empty Fields**: Skip field and send `TABS_NEEDED_EMPTY` number of tabs

### Examples:
- Field with `TABS_NEEDED=1`, `TABS_NEEDED_EMPTY=1`, length=5, max=10: Sends 1 tab (normal)
- Field with `TABS_NEEDED=2`, `TABS_NEEDED_EMPTY=1`, length=10, max=10: Auto-tabs + 1 additional tab
- Field with `TABS_NEEDED=2`, `TABS_NEEDED_EMPTY=1`, length=5, max=10: Sends 2 tabs
- Field with `TABS_NEEDED=2`, `TABS_NEEDED_EMPTY=1`, empty field: Sends 1 tab (using empty setting)

### Use Cases for Different Tab Settings:
- **Phone/Fax fields**: May need 2 tabs when filled but only 1 when empty
- **Address fields**: May span multiple lines requiring different tab behavior
- **Required vs Optional fields**: Different navigation patterns based on field importance

## Adding New Screens

To add a new screen (e.g., "inventory_maintenance"):

1. **Create data file**: `screens/inventory_maintenance_data.csv`
2. **Create config file**: `screens/inventory_maintenance_config.csv`
3. **Update navigation**: Add steps to `screens/navigation_config.csv`
4. **Add screen config**: Update `config/screen_configs.py`

Example screen config:
```python
'inventory_maintenance': {
    'option': '25',
    'company_id': '689',
    'operation': 'A',
    'data_file': 'screens/inventory_maintenance_data.csv',
    'config_file': 'screens/inventory_maintenance_config.csv',
    'navigation_file': 'screens/navigation_config.csv',
    'description': 'Inventory Maintenance Screen'
}
```

## Screen Capture and HTML Files

The system automatically captures and saves HTML versions of each screen during processing:

### Output Directory Structure
- Each run creates a timestamped directory: `screen_output_YYYYMMDD_HHMMSS/`
- Example: `screen_output_20241203_143022/`
- This prevents HTML files from being overwritten between runs

### Saved HTML Files
During execution, the following HTML files are saved:

1. **Navigation Steps**: `step_01_credentials.html`, `step_02_enter.html`, etc.
2. **Form Processing**: `before_submission.html`, `after_submission.html`
3. **Each Screen**: Captured at every navigation step for debugging

### Testing HTML Functionality
Run the HTML saving test to verify functionality:
```bash
python3 test_html_saving.py
```

This test:
- Creates a timestamped output directory
- Verifies directory permissions
- Tests filename generation
- Does not require TN5250 connection

### Viewing HTML Files
After running the system, you can view the captured screens:
```bash
# List all output directories
ls -la screen_output_*

# View HTML files from latest run
ls -la screen_output_*/

# Open an HTML file in browser (macOS)
open screen_output_20241203_143022/step_01_credentials.html

# View HTML content in terminal
cat screen_output_20241203_143022/before_submission.html
```

## Error Handling

The system provides comprehensive error handling:

- **Environment Validation**: Checks s3270 installation and host connectivity
- **File Validation**: Ensures all required CSV files exist
- **Data Validation**: Validates all field data against configuration rules
- **Connection Management**: Handles connection failures and cleanup
- **Screen Validation**: Checks for expected screen content

## Logging

All operations are logged with different levels:
- `INFO`: Normal operation flow
- `ERROR`: Validation failures and errors
- `WARNING`: Non-critical issues
- `DEBUG`: Detailed tab and field information

## Troubleshooting

### Common Issues:

1. **s3270 not found**: Install x3270 package for your OS
2. **Host unreachable**: Check HOST/PORT in `config/screen_configs.py`
3. **File not found**: Ensure all CSV files exist in the screens directory
4. **Validation errors**: Check data against field configuration rules
5. **Screen mismatch**: Verify navigation steps match actual screens
6. **HTML files not saved**: Check permissions and verify output directory creation

### Debug Tips:

1. **Check HTML files**: Review saved HTML files in timestamped directories for screen content
2. **Review log output**: Check for validation details and error messages
3. **Verify CSV formatting**: Ensure no extra spaces, proper quotes in CSV files
4. **Test connectivity**: Use simple telnet to test: `telnet HOST PORT`
5. **Test HTML saving**: Run `python3 test_html_saving.py` to verify file saving works
6. **Check timestamps**: Each run creates a new directory, so check the latest one

### HTML File Locations:
- **Current run**: Look for `screen_output_YYYYMMDD_HHMMSS/` directories
- **Multiple runs**: Each creates a separate timestamped directory
- **File naming**: Files are named by step order and action type
- **Before/After**: Form submissions save both before and after states

## Examples

### Company Maintenance
```bash
python main_modular.py company_maintenance
```

### Customer Maintenance (when configured)
```bash
python main_modular.py customer_maintenance
```

## Architecture

The modular system consists of:

1. **Main Controller** (`main_modular.py`): Orchestrates the entire process
2. **Screen Handler** (`modules/screen_handler.py`): Generic screen processing
3. **Connection Manager** (`modules/connection_manager.py`): TN5250 connection handling
4. **Configuration System**: CSV files and Python config for flexibility

This design allows for easy extension and maintenance while keeping the core logic reusable across different screen types. 