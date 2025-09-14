"""
Screen Configuration Module

This module contains configuration for different screens and their specific settings.
Each screen can have different navigation options and company IDs.
"""

SCREEN_CONFIGS = {
    'company_maintenance': {
        'option': '21',
        'company_id': '694',
        'operation': 'A',  # A=Add, C=Change, D=Delete
        'data_file': 'screens/company_maintenance_data.csv',
        'config_file': 'screens/company_maintenance_config.csv',
        'navigation_file': 'screens/navigation_config.csv',
        'description': 'Company Maintenance Screen - Add new company'
    },
    'customer_maintenance': {
        'option': '22',  # Example for another screen
        'company_id': '689',
        'operation': 'A',
        'data_file': 'screens/customer_maintenance_data.csv',
        'config_file': 'screens/customer_maintenance_config.csv',
        'navigation_file': 'screens/navigation_config.csv',
        'description': 'Customer Maintenance Screen - Add new customer'
    },
    'vendor_maintenance': {
        'option': '23',  # Example for another screen
        'company_id': '689',
        'operation': 'A',
        'data_file': 'screens/vendor_maintenance_data.csv',
        'config_file': 'screens/vendor_maintenance_config.csv',
        'navigation_file': 'screens/navigation_config.csv',
        'description': 'Vendor Maintenance Screen - Add new vendor'
    }
}

# Connection settings
CONNECTION_CONFIG = {
    'HOST': "10.150.0.59",
    'PORT': 992,
    'USE_SSL': True,
    'USERNAME': "QPGMR",
    'PASSWORD': "AUMTQPgm",
    'PREFERRED_MODEL': "3279-2",
    'CODE_PAGE': "cp037",
    'SCREEN_TIMEOUT': 30
} 