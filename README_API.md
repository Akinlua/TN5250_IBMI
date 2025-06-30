# TN5250 REST API Documentation

A REST API for automating TN5250 screen interactions using Flask, PostgreSQL, and Prisma.

## Overview

This API allows you to:
- **Store screen configurations** in a PostgreSQL database
- **Send screen data** via API endpoints instead of CSV files
- **Process screens** dynamically based on screen names
- **Manage multiple navigation flows** for different screens

## Architecture

- **Flask**: REST API framework
- **PostgreSQL**: Database for storing configurations
- **Prisma**: ORM for database operations
- **Pydantic**: Data validation and serialization

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Database Setup

1. Install PostgreSQL and create a database:
```sql
CREATE DATABASE tn5250_db;
```

2. Copy environment variables:
```bash
cp .env.example .env
```

3. Update `.env` with your database URL:
```bash
DATABASE_URL="postgresql://username:password@localhost:5432/tn5250_api"
```

### 3. Initialize Prisma

```bash
# Generate Prisma client
prisma generate

# Run database migrations
prisma db push
```

### 4. Start the API

```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### Health Check

```http
GET /health
```

Returns API health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "TN5250 REST API",
  "version": "1.0.0"
}
```

### Screen Management

#### List All Screens

```http
GET /api/screens
```

**Response:**
```json
{
  "screens": ["company_maintenance", "customer_maintenance"],
  "count": 2
}
```

#### Get Screen Configuration

```http
GET /api/screens/{screen_name}
```

**Response:**
```json
{
  "screen_config": {
    "screen_name": "company_maintenance",
    "description": "Company maintenance screen",
    "company_id": "01",
    "option": "A",
    "operation": "ADD"
  },
  "field_configs": [
    {
      "field_name": "company_id",
      "max_length": 10,
      "required": true,
      "type": "text",
      "valid_values": null,
      "tabs_needed": 1,
      "tabs_needed_empty": 1,
      "description": "Company identifier"
    }
  ],
  "navigation_steps": [
    {
      "step_order": 1,
      "screen_title_contains": "SIGN ON",
      "action_type": "credentials",
      "action_value": "QSECOFR,QSECOFR",
      "wait_time": 2,
      "description": "Sign on to system"
    }
  ]
}
```

#### Create Screen Configuration

```http
POST /api/screens
```

**Request Body:**
```json
{
  "screen_config": {
    "screen_name": "company_maintenance",
    "description": "Company maintenance screen",
    "company_id": "01",
    "option": "A",
    "operation": "ADD"
  },
  "field_configs": [
    {
      "field_name": "company_id",
      "max_length": 10,
      "required": true,
      "type": "text",
      "valid_values": null,
      "tabs_needed": 1,
      "tabs_needed_empty": 1,
      "description": "Company identifier"
    },
    {
      "field_name": "company_name",
      "max_length": 50,
      "required": true,
      "type": "text",
      "valid_values": null,
      "tabs_needed": 1,
      "tabs_needed_empty": 1,
      "description": "Company name"
    }
  ],
  "navigation_steps": [
    {
      "step_order": 1,
      "screen_title_contains": "SIGN ON",
      "action_type": "credentials",
      "action_value": "QSECOFR,QSECOFR",
      "wait_time": 2,
      "description": "Sign on to system"
    },
    {
      "step_order": 2,
      "screen_title_contains": "Main Menu",
      "action_type": "command",
      "action_value": "STRSQL",
      "wait_time": 2,
      "description": "Start SQL"
    },
    {
      "step_order": 3,
      "screen_title_contains": "COMPANY MAINTENANCE",
      "action_type": "form_fill",
      "action_value": "",
      "wait_time": 1,
      "description": "Fill company maintenance form"
    }
  ]
}
```

**Response:**
```json
{
  "message": "Screen configuration 'company_maintenance' created successfully",
  "screen_name": "company_maintenance"
}
```

#### Update Screen Configuration

```http
PUT /api/screens/{screen_name}
```

Same request body format as create.

#### Delete Screen Configuration

```http
DELETE /api/screens/{screen_name}
```

**Response:**
```json
{
  "message": "Screen configuration 'company_maintenance' deleted successfully",
  "screen_name": "company_maintenance"
}
```

### Screen Processing

#### Process Screen

```http
POST /api/process
```

**Request Body:**
```json
{
  "screen_name": "company_maintenance",
  "screen_data": {
    "company_id": "TEST01",
    "company_name": "Test Company",
    "address_line_1": "123 Main St",
    "city": "Test City",
    "state": "CA",
    "country": "US",
    "postal_code": "12345",
    "phone_number": "555-1234",
    "email": "test@company.com"
  }
}
```

**Response:**
```json
{
  "success": true,
  "messages": [
    "✓ company_id: 'TEST01' (6/10 chars)",
    "✓ company_name: 'Test Company' (12/50 chars)",
    "Step 1 completed successfully",
    "Step 2 completed successfully",
    "SUCCESS: Company TEST01 was added successfully!"
  ],
  "html_files_directory": "screen_output_20241203_143022"
}
```

#### Validate Screen Data

```http
POST /api/validate
```

**Request Body:**
```json
{
  "screen_name": "company_maintenance",
  "screen_data": {
    "company_id": "TEST01",
    "company_name": "Test Company"
  }
}
```

**Response:**
```json
{
  "valid": true,
  "messages": [
    "✓ company_id: 'TEST01' (6/10 chars)",
    "✓ company_name: 'Test Company' (12/50 chars)"
  ],
  "screen_name": "company_maintenance"
}
```

## Field Configuration Options

### Field Types
- `text`: General text field
- `digits`: Numeric field (digits only)
- `email`: Email address field
- `phone`: Phone number field

### Validation Rules
- `max_length`: Maximum character length
- `required`: Whether field is mandatory
- `valid_values`: List of acceptable values (optional)

### Tab Behavior
- `tabs_needed`: Tabs to send when field has content
- `tabs_needed_empty`: Tabs to send when field is empty

## Navigation Action Types

- `credentials`: Send username and password
- `enter`: Press Enter key
- `command`: Send a command and press Enter
- `option`: Select a menu option
- `option_with_id`: Select option with ID parameter
- `form_fill`: Fill the main form (final step)

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `201`: Created
- `400`: Bad Request (validation error)
- `404`: Not Found
- `405`: Method Not Allowed
- `500`: Internal Server Error

Error responses follow this format:
```json
{
  "error": "Error description",
  "details": "Additional error details"
}
```

## Usage Examples

### 1. Creating a Complete Screen Configuration

```bash
curl -X POST http://localhost:5000/api/screens \
  -H "Content-Type: application/json" \
  -d @company_maintenance_config.json
```

### 2. Processing a Screen

```bash
curl -X POST http://localhost:5000/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "screen_name": "company_maintenance",
    "screen_data": {
      "company_id": "TEST01",
      "company_name": "Test Company",
      "city": "Test City"
    }
  }'
```

### 3. Listing Available Screens

```bash
curl http://localhost:5000/api/screens
```

## Database Schema

The API uses three main tables:

### screen_configs
- `id`: Primary key
- `screenName`: Unique screen identifier
- `description`: Screen description
- `companyId`: Default company ID
- `option`: Screen option
- `operation`: Screen operation

### field_configs
- `id`: Primary key
- `screenName`: Foreign key to screen_configs
- `fieldName`: Field identifier
- `maxLength`: Maximum field length
- `required`: Required field flag
- `type`: Field type
- `validValues`: JSON array of valid values
- `tabsNeeded`: Tabs for filled fields
- `tabsNeededEmpty`: Tabs for empty fields
- `description`: Field description

### navigation_steps
- `id`: Primary key
- `screenName`: Foreign key to screen_configs
- `stepOrder`: Step sequence number
- `screenTitleContains`: Screen title to match
- `actionType`: Type of action to perform
- `actionValue`: Action parameter
- `waitTime`: Wait time after action
- `description`: Step description

## HTML File Output

When processing screens, HTML files are automatically saved to timestamped directories:
- Format: `screen_output_YYYYMMDD_HHMMSS/`
- Files include: step captures, before/after submission screens
- Files are saved with terminal-style formatting for easy viewing

## Security Considerations

- Database credentials should be stored in environment variables
- Consider implementing authentication for production use
- Validate all input data thoroughly
- Use HTTPS in production environments

## Development

To extend the API:

1. Add new Pydantic models in `api/models.py`
2. Extend database operations in `api/database.py`
3. Add new endpoints in `app.py`
4. Update the Prisma schema if needed

## Troubleshooting

### Common Issues

1. **Database Connection Error**: Check DATABASE_URL in .env
2. **Prisma Client Error**: Run `prisma generate`
3. **s3270 Not Found**: Install x3270 package
4. **Connection Timeout**: Check TN5250 server connectivity

### Logs

The API logs all operations. Check console output for detailed error messages. 