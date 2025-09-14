"""
SQLAlchemy models for TN5250 REST API

This module defines the database models for storing screen configurations,
field configurations, and navigation steps using SQLAlchemy ORM.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import json

Base = declarative_base()

class ScreenConfig(Base):
    """Screen configuration model"""
    __tablename__ = 'screen_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    screen_name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200), nullable=False)
    option = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    field_configs = relationship("FieldConfig", back_populates="screen_config", cascade="all, delete-orphan")
    navigation_steps = relationship("NavigationStep", back_populates="screen_config", cascade="all, delete-orphan")
    
    def dict(self):
        return {
            'id': self.id,
            'screen_name': self.screen_name,
            'description': self.description,
            'option': self.option,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class FieldConfig(Base):
    """Field configuration model"""
    __tablename__ = 'field_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    screen_name = Column(String(50), ForeignKey('screen_configs.screen_name'), nullable=False)
    field_name = Column(String(50), nullable=False)
    max_length = Column(Integer, nullable=False)
    required = Column(Boolean, nullable=False, default=False)
    type = Column(String(20), nullable=False, default='text')
    valid_values = Column(Text)  # JSON string for list of valid values
    tabs_needed = Column(Integer, nullable=False, default=1)
    tabs_needed_empty = Column(Integer, nullable=False, default=1)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    screen_config = relationship("ScreenConfig", back_populates="field_configs")
    
    def dict(self):
        valid_values_list = json.loads(self.valid_values) if self.valid_values else None
        return {
            'id': self.id,
            'screen_name': self.screen_name,
            'field_name': self.field_name,
            'max_length': self.max_length,
            'required': self.required,
            'type': self.type,
            'valid_values': valid_values_list,
            'tabs_needed': self.tabs_needed,
            'tabs_needed_empty': self.tabs_needed_empty,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class NavigationStep(Base):
    """Navigation step model"""
    __tablename__ = 'navigation_steps'
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    screen_name = Column(String(50), ForeignKey('screen_configs.screen_name'), nullable=False)
    step_order = Column(Integer, nullable=False)
    screen_title_contains = Column(String(100), nullable=False)
    action_type = Column(String(20), nullable=False)
    action_value = Column(String(100), nullable=False)
    wait_time = Column(Integer, nullable=False, default=1)
    description = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    screen_config = relationship("ScreenConfig", back_populates="navigation_steps")
    
    def dict(self):
        return {
            'id': self.id,
            'screen_name': self.screen_name,
            'step_order': self.step_order,
            'screen_title_contains': self.screen_title_contains,
            'action_type': self.action_type,
            'action_value': self.action_value,
            'wait_time': self.wait_time,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 

class ScreenDataSubmission(Base):
    """Model for storing screen data submissions"""
    __tablename__ = 'screen_data_submissions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    screen_name = Column(String(50), nullable=False, index=True)
    screen_inputs = Column(JSON, nullable=True)  # Dynamic inputs like operation, company_id, etc.
    screen_data = Column(JSON, nullable=False)   # Form data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def dict(self):
        """Return dictionary representation of the model"""
        return {
            'id': self.id,
            'screen_name': self.screen_name,
            'screen_inputs': self.screen_inputs,
            'screen_data': self.screen_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 