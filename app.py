"""
TN5250 REST API

Flask application providing REST API endpoints for automating TN5250 screen interactions.
Uses SQLAlchemy for database operations and supports CRUD operations for screen configurations.
"""

import os
import logging
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from modules.connection_manager import ConnectionManager
from modules.api_screen_handler import ApiScreenHandler
from api.database import DatabaseService
from api.schemas import (
    CreateScreenConfigRequest, ProcessScreenRequest, ValidateScreenRequest,
    ProcessScreenResponse, ValidateScreenResponse, ScreenConfigResponse,
    ScreenListResponse, SuccessResponse, ErrorResponse, HealthResponse
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database service instance
db_service = None

# TN5250 connection configuration
CONNECTION_CONFIG = {
    'HOST': os.getenv('TN5250_HOST', '10.150.0.59'),
    'PORT': int(os.getenv('TN5250_PORT', 23)),
    'USERNAME': os.getenv('TN5250_USERNAME', 'TESTUSER'),
    'PASSWORD': os.getenv('TN5250_PASSWORD', 'TESTPASS'),
    'USE_SSL': os.getenv('TN5250_SSL', 'False').lower() == 'true',
    'PREFERRED_MODEL': os.getenv('TN5250_MODEL', '3279-2'),
    'CODE_PAGE': os.getenv('TN5250_CODEPAGE', 'cp037'),
    'SCREEN_TIMEOUT': int(os.getenv('TN5250_TIMEOUT', 30))
}

def init_database():
    """Initialize database connection and create tables"""
    global db_service
    database_url = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/tn5250_')
    
    db_service = DatabaseService(database_url)
    if not db_service.connect():
        logger.error("Failed to connect to database")
        return False
    
    if not db_service.create_tables():
        logger.error("Failed to create database tables")
        return False
    
    logger.info("Database initialized successfully")
    return True

def cleanup_database():
    """Cleanup database connections"""
    global db_service
    if db_service:
        db_service.disconnect()
        logger.info("Database connections cleaned up")

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        response = HealthResponse(
            status="healthy",
            service="TN5250 REST API",
            version="1.0.0"
        )
        return jsonify(response.dict()), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        error_response = ErrorResponse(
            error="Health check failed",
            details=str(e)
        )
        return jsonify(error_response.dict()), 500

# Screen management endpoints
@app.route('/api/screens', methods=['GET'])
def list_screens():
    """Get list of all available screen configurations"""
    try:
        screen_names = db_service.list_screen_names()
        response = ScreenListResponse(
            screens=screen_names,
            count=len(screen_names)
        )
        return jsonify(response.dict()), 200
    except Exception as e:
        logger.error(f"Error listing screens: {str(e)}")
        error_response = ErrorResponse(
            error="Failed to list screens",
            details=str(e)
        )
        return jsonify(error_response.dict()), 500

@app.route('/api/screens/<screen_name>', methods=['GET'])
def get_screen_config(screen_name):
    """Get complete screen configuration by name"""
    try:
        result = db_service.get_screen_config(screen_name)
        if not result:
            error_response = ErrorResponse(
                error="Screen not found",
                details=f"Screen configuration '{screen_name}' does not exist"
            )
            return jsonify(error_response.dict()), 404
        
        screen_config, field_configs, navigation_steps = result
        response = ScreenConfigResponse(
            screen_config=screen_config,
            field_configs=field_configs,
            navigation_steps=navigation_steps
        )
        return jsonify(response.dict()), 200
    except Exception as e:
        logger.error(f"Error getting screen config: {str(e)}")
        error_response = ErrorResponse(
            error="Failed to get screen configuration",
            details=str(e)
        )
        return jsonify(error_response.dict()), 500

@app.route('/api/screens', methods=['POST'])
def create_screen_config():
    """Create a new screen configuration"""
    try:
        # Validate request data
        request_data = CreateScreenConfigRequest(**request.json)
        
        # Create screen configuration
        success = db_service.create_screen_config(
            request_data.screen_config,
            request_data.field_configs,
            request_data.navigation_steps
        )
        
        if not success:
            error_response = ErrorResponse(
                error="Failed to create screen configuration",
                details="Screen may already exist or validation failed"
            )
            return jsonify(error_response.dict()), 400
        
        response = SuccessResponse(
            message="Screen configuration created successfully",
            screen_name=request_data.screen_config.screen_name
        )
        return jsonify(response.dict()), 201
        
    except Exception as e:
        logger.error(f"Error creating screen config: {str(e)}")
        error_response = ErrorResponse(
            error="Failed to create screen configuration",
            details=str(e)
        )
        return jsonify(error_response.dict()), 500

@app.route('/api/screens/<screen_name>', methods=['PUT'])
def update_screen_config(screen_name):
    """Update an existing screen configuration"""
    try:
        # Validate request data
        request_data = CreateScreenConfigRequest(**request.json)
        
        # Update screen configuration
        success = db_service.update_screen_config(
            screen_name,
            request_data.screen_config,
            request_data.field_configs,
            request_data.navigation_steps
        )
        
        if not success:
            error_response = ErrorResponse(
                error="Failed to update screen configuration",
                details=f"Screen '{screen_name}' may not exist"
            )
            return jsonify(error_response.dict()), 404
        
        response = SuccessResponse(
            message="Screen configuration updated successfully",
            screen_name=screen_name
        )
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Error updating screen config: {str(e)}")
        error_response = ErrorResponse(
            error="Failed to update screen configuration",
            details=str(e)
        )
        return jsonify(error_response.dict()), 500

@app.route('/api/screens/<screen_name>', methods=['DELETE'])
def delete_screen_config(screen_name):
    """Delete a screen configuration"""
    try:
        success = db_service.delete_screen_config(screen_name)
        
        if not success:
            error_response = ErrorResponse(
                error="Failed to delete screen configuration",
                details=f"Screen '{screen_name}' may not exist"
            )
            return jsonify(error_response.dict()), 404
        
        response = SuccessResponse(
            message="Screen configuration deleted successfully",
            screen_name=screen_name
        )
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Error deleting screen config: {str(e)}")
        error_response = ErrorResponse(
            error="Failed to delete screen configuration",
            details=str(e)
        )
        return jsonify(error_response.dict()), 500

# Screen processing endpoints
@app.route('/api/process', methods=['POST'])
def process_screen():
    """Process a screen with provided data"""
    try:
        # Validate request data
        request_data = ProcessScreenRequest(**request.json)
        
        # Save or update screen data submission
        try:
            saved_submission = db_service.save_screen_data_submission(
                screen_name=request_data.screen_name,
                screen_inputs=request_data.screen_inputs,
                screen_data=request_data.screen_data,
                submission_id=request_data.id  # None for new submissions
            )
            logger.info(f"Saved screen data submission: {saved_submission['id']}")
        except Exception as save_error:
            logger.warning(f"Failed to save screen data submission: {str(save_error)}")
            # Continue with processing even if save fails
        
        # Get screen configuration
        result = db_service.get_screen_config(request_data.screen_name)
        if not result:
            error_response = ErrorResponse(
                error="Screen not found",
                details=f"Screen configuration '{request_data.screen_name}' does not exist"
            )
            return jsonify(error_response.dict()), 404
        
        screen_config, field_configs, navigation_steps = result
        
        # Initialize connection manager
        connection_manager = ConnectionManager(CONNECTION_CONFIG)
        
        # Validate environment
        if not connection_manager.validate_environment():
            error_response = ErrorResponse(
                error="Environment validation failed",
                details="Please check s3270 installation and configuration"
            )
            return jsonify(error_response.dict()), 500
        
        # Initialize API screen handler
        api_handler = ApiScreenHandler(
            screen_config=screen_config.dict(),
            field_configs=[fc.dict() for fc in field_configs],
            navigation_steps=[ns.dict() for ns in navigation_steps],
            screen_data=request_data.screen_data
        )
        
        # Establish connection
        client, connected = connection_manager.connect_to_host()
        if not connected or not client:
            error_response = ErrorResponse(
                error="Connection failed",
                details="Failed to establish connection to TN5250 server"
            )
            return jsonify(error_response.dict()), 500
        
        try:
            # Process the screen
            success, messages = api_handler.process_screen(
                client,
                screen_inputs=request_data.screen_inputs,
                username=CONNECTION_CONFIG['USERNAME'],
                password=CONNECTION_CONFIG['PASSWORD']
            )
            
            response = ProcessScreenResponse(
                success=success,
                messages=messages,
                html_files_directory=api_handler.output_directory,
                submission_id=saved_submission.get('id') if 'saved_submission' in locals() else None
            )
            return jsonify(response.dict()), 200
            
        finally:
            # Always cleanup connection
            connection_manager.cleanup_connection(client)
        
    except Exception as e:
        logger.error(f"Error processing screen: {str(e)}")
        error_response = ErrorResponse(
            error="Failed to process screen",
            details=str(e)
        )
        return jsonify(error_response.dict()), 500

@app.route('/api/submissions', methods=['GET'])
def get_screen_data_submissions():
    """Get all screen data submissions or filter by screen name"""
    try:
        screen_name = request.args.get('screen_name')
        submissions = db_service.get_screen_data_submissions(screen_name=screen_name)
        
        return jsonify({
            "submissions": submissions,
            "count": len(submissions),
            "screen_name": screen_name
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving screen data submissions: {str(e)}")
        error_response = ErrorResponse(
            error="Failed to retrieve screen data submissions",
            details=str(e)
        )
        return jsonify(error_response.dict()), 500

@app.route('/api/submissions/<int:submission_id>', methods=['GET'])
def get_screen_data_submission(submission_id):
    """Get a specific screen data submission by ID"""
    try:
        submission = db_service.get_screen_data_submission_by_id(submission_id)
        
        if not submission:
            error_response = ErrorResponse(
                error="Submission not found",
                details=f"Screen data submission with ID {submission_id} does not exist"
            )
            return jsonify(error_response.dict()), 404
        
        return jsonify(submission), 200
        
    except Exception as e:
        logger.error(f"Error retrieving screen data submission {submission_id}: {str(e)}")
        error_response = ErrorResponse(
            error="Failed to retrieve screen data submission",
            details=str(e)
        )
        return jsonify(error_response.dict()), 500

@app.route('/api/validate', methods=['POST'])
def validate_screen():
    """Validate screen data without processing"""
    try:
        # Validate request data
        request_data = ValidateScreenRequest(**request.json)
        
        # Get screen configuration
        result = db_service.get_screen_config(request_data.screen_name)
        if not result:
            error_response = ErrorResponse(
                error="Screen not found",
                details=f"Screen configuration '{request_data.screen_name}' does not exist"
            )
            return jsonify(error_response.dict()), 404
        
        screen_config, field_configs, navigation_steps = result
        
        # Initialize API screen handler for validation
        api_handler = ApiScreenHandler(
            screen_config=screen_config.dict(),
            field_configs=[fc.dict() for fc in field_configs],
            navigation_steps=[ns.dict() for ns in navigation_steps],
            screen_data=request_data.screen_data
        )
        
        # Validate data
        validation_success, validation_messages = api_handler.validate_all_fields()
        
        response = ValidateScreenResponse(
            valid=validation_success,
            messages=validation_messages
        )
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Error validating screen: {str(e)}")
        error_response = ErrorResponse(
            error="Failed to validate screen",
            details=str(e)
        )
        return jsonify(error_response.dict()), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    error_response = ErrorResponse(
        error="Not found",
        details="The requested resource was not found"
    )
    return jsonify(error_response.dict()), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    error_response = ErrorResponse(
        error="Method not allowed",
        details="The HTTP method is not allowed for this endpoint"
    )
    return jsonify(error_response.dict()), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    error_response = ErrorResponse(
        error="Internal server error",
        details="An unexpected error occurred"
    )
    return jsonify(error_response.dict()), 500

if __name__ == '__main__':
    try:
        # Initialize database
        if not init_database():
            logger.error("Failed to initialize database. Exiting.")
            exit(1)
        
        logger.info("Starting TN5250 REST API server...")
        logger.info(f"TN5250 Server: {CONNECTION_CONFIG['HOST']}:{CONNECTION_CONFIG['PORT']}")
        logger.info(f"Database URL: {os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/tn5250_api')}")
        
        # Start Flask app
        app.run(
            host='0.0.0.0',
            port=int(os.getenv('PORT', 5003)),
            debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        )
        
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
    finally:
        cleanup_database() 