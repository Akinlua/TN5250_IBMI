"""
Database service layer for TN5250 REST API

This module provides database operations using SQLAlchemy ORM for managing
screen configurations, field configurations, and navigation steps.
"""

import logging
import json
import uuid
from typing import List, Dict, Optional, Tuple
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .models import Base, ScreenConfig, FieldConfig, NavigationStep
from .schemas import ScreenConfigSchema, FieldConfigSchema, NavigationStepSchema

logger = logging.getLogger(__name__)

class DatabaseService:
    """Database service for handling all database operations"""
    
    def __init__(self, database_url: str):
        """Initialize database service with connection URL"""
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        
    def connect(self):
        """Connect to the database"""
        try:
            self.engine = create_engine(self.database_url)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("Database connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from the database"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            return False
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    def create_screen_config(self, screen_config: ScreenConfigSchema, 
                           field_configs: List[FieldConfigSchema],
                           navigation_steps: List[NavigationStepSchema]) -> bool:
        """Create a complete screen configuration"""
        session = self.get_session()
        try:
            # Check if screen already exists
            existing = session.query(ScreenConfig).filter(
                ScreenConfig.screen_name == screen_config.screen_name
            ).first()
            
            if existing:
                logger.error(f"Screen configuration '{screen_config.screen_name}' already exists")
                return False
            
            # Create screen configuration
            db_screen = ScreenConfig(
                screen_name=screen_config.screen_name,
                description=screen_config.description,
                option=screen_config.option
            )
            session.add(db_screen)
            session.flush()  # Get the ID for foreign keys
            
            # Create field configurations
            for field_config in field_configs:
                db_field = FieldConfig(
                    screen_name=screen_config.screen_name,
                    field_name=field_config.field_name,
                    max_length=field_config.max_length,
                    required=field_config.required,
                    type=field_config.type,
                    valid_values=json.dumps(field_config.valid_values) if field_config.valid_values else None,
                    tabs_needed=field_config.tabs_needed,
                    tabs_needed_empty=field_config.tabs_needed_empty,
                    description=field_config.description
                )
                session.add(db_field)
            
            # Create navigation steps
            for nav_step in navigation_steps:
                db_nav = NavigationStep(
                    screen_name=screen_config.screen_name,
                    step_order=nav_step.step_order,
                    screen_title_contains=nav_step.screen_title_contains,
                    action_type=nav_step.action_type,
                    action_value=nav_step.action_value,
                    wait_time=nav_step.wait_time,
                    description=nav_step.description
                )
                session.add(db_nav)
            
            session.commit()
            logger.info(f"Screen configuration '{screen_config.screen_name}' created successfully")
            return True
            
        except IntegrityError as e:
            session.rollback()
            logger.error(f"Integrity error creating screen configuration: {str(e)}")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating screen configuration: {str(e)}")
            return False
        finally:
            session.close()
    
    def get_screen_config(self, screen_name: str) -> Optional[Tuple[ScreenConfigSchema, List[FieldConfigSchema], List[NavigationStepSchema]]]:
        """Retrieve a complete screen configuration"""
        session = self.get_session()
        try:
            # Get screen configuration with relationships
            db_screen = session.query(ScreenConfig).filter(
                ScreenConfig.screen_name == screen_name
            ).first()
            
            if not db_screen:
                logger.warning(f"Screen configuration '{screen_name}' not found")
                return None
            
            # Convert to schemas
            screen_schema = ScreenConfigSchema(
                screen_name=db_screen.screen_name,
                description=db_screen.description,
                option=db_screen.option
            )
            
            field_schemas = []
            for field in db_screen.field_configs:
                valid_values = json.loads(field.valid_values) if field.valid_values else None
                field_schemas.append(FieldConfigSchema(
                    field_name=field.field_name,
                    max_length=field.max_length,
                    required=field.required,
                    type=field.type,
                    valid_values=valid_values,
                    tabs_needed=field.tabs_needed,
                    tabs_needed_empty=field.tabs_needed_empty,
                    description=field.description
                ))
            
            nav_schemas = []
            for nav in sorted(db_screen.navigation_steps, key=lambda x: x.step_order):
                nav_schemas.append(NavigationStepSchema(
                    step_order=nav.step_order,
                    screen_title_contains=nav.screen_title_contains,
                    action_type=nav.action_type,
                    action_value=nav.action_value,
                    wait_time=nav.wait_time,
                    description=nav.description
                ))
            
            logger.info(f"Screen configuration '{screen_name}' retrieved successfully")
            return screen_schema, field_schemas, nav_schemas
            
        except Exception as e:
            logger.error(f"Error retrieving screen configuration: {str(e)}")
            return None
        finally:
            session.close()
    
    def list_screen_names(self) -> List[str]:
        """Get a list of all available screen names"""
        session = self.get_session()
        try:
            screens = session.query(ScreenConfig.screen_name).all()
            screen_names = [screen[0] for screen in screens]
            logger.info(f"Retrieved {len(screen_names)} screen names")
            return screen_names
        except Exception as e:
            logger.error(f"Error retrieving screen names: {str(e)}")
            return []
        finally:
            session.close()
    
    def update_screen_config(self, screen_name: str, screen_config: ScreenConfigSchema,
                           field_configs: List[FieldConfigSchema],
                           navigation_steps: List[NavigationStepSchema]) -> bool:
        """Update an existing screen configuration"""
        session = self.get_session()
        try:
            # Check if screen exists
            db_screen = session.query(ScreenConfig).filter(
                ScreenConfig.screen_name == screen_name
            ).first()
            
            if not db_screen:
                logger.error(f"Screen configuration '{screen_name}' not found")
                return False
            
            # Update screen configuration
            db_screen.description = screen_config.description
            db_screen.option = screen_config.option
            
            # Delete existing field configs and navigation steps
            session.query(FieldConfig).filter(FieldConfig.screen_name == screen_name).delete()
            session.query(NavigationStep).filter(NavigationStep.screen_name == screen_name).delete()
            
            # Create new field configurations
            for field_config in field_configs:
                db_field = FieldConfig(
                    screen_name=screen_name,
                    field_name=field_config.field_name,
                    max_length=field_config.max_length,
                    required=field_config.required,
                    type=field_config.type,
                    valid_values=json.dumps(field_config.valid_values) if field_config.valid_values else None,
                    tabs_needed=field_config.tabs_needed,
                    tabs_needed_empty=field_config.tabs_needed_empty,
                    description=field_config.description
                )
                session.add(db_field)
            
            # Create new navigation steps
            for nav_step in navigation_steps:
                db_nav = NavigationStep(
                    screen_name=screen_name,
                    step_order=nav_step.step_order,
                    screen_title_contains=nav_step.screen_title_contains,
                    action_type=nav_step.action_type,
                    action_value=nav_step.action_value,
                    wait_time=nav_step.wait_time,
                    description=nav_step.description
                )
                session.add(db_nav)
            
            session.commit()
            logger.info(f"Screen configuration '{screen_name}' updated successfully")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating screen configuration: {str(e)}")
            return False
        finally:
            session.close()
    
    def delete_screen_config(self, screen_name: str) -> bool:
        """Delete a screen configuration and all related data"""
        session = self.get_session()
        try:
            # Get screen configuration
            db_screen = session.query(ScreenConfig).filter(
                ScreenConfig.screen_name == screen_name
            ).first()
            
            if not db_screen:
                logger.error(f"Screen configuration '{screen_name}' not found")
                return False
            
            # Delete screen configuration (cascade will handle related records)
            session.delete(db_screen)
            session.commit()
            
            logger.info(f"Screen configuration '{screen_name}' deleted successfully")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting screen configuration: {str(e)}")
            return False
        finally:
            session.close() 