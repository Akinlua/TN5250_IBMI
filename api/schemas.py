"""
Pydantic schemas for TN5250 REST API

This module defines the request/response models for API validation
using Pydantic.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class FieldConfigSchema(BaseModel):
    field_name: str
    max_length: int
    required: bool
    type: str
    valid_values: Optional[List[str]] = None
    tabs_needed: int
    tabs_needed_empty: int
    description: str

class NavigationStepSchema(BaseModel):
    step_order: int
    screen_title_contains: str
    action_type: str
    action_value: str
    wait_time: int
    description: str

class ScreenConfigSchema(BaseModel):
    screen_name: str
    description: str
    option: str  # Only static configuration remains

class CreateScreenConfigRequest(BaseModel):
    screen_config: ScreenConfigSchema
    field_configs: List[FieldConfigSchema]
    navigation_steps: List[NavigationStepSchema]

class ProcessScreenRequest(BaseModel):
    screen_name: str
    screen_data: Dict[str, str]  # field_name -> value mapping for form fields
    screen_inputs: Dict[str, str]  # Dynamic screen inputs (operation, company_id, account, etc.)

class ValidateScreenRequest(BaseModel):
    screen_name: str
    screen_data: Dict[str, str]  # field_name -> value mapping

class ProcessScreenResponse(BaseModel):
    success: bool
    messages: List[str]
    html_files_directory: Optional[str] = None

class ValidateScreenResponse(BaseModel):
    valid: bool
    messages: List[str]

class ScreenConfigResponse(BaseModel):
    screen_config: ScreenConfigSchema
    field_configs: List[FieldConfigSchema]
    navigation_steps: List[NavigationStepSchema]

class ScreenListResponse(BaseModel):
    screens: List[str]
    count: int

class SuccessResponse(BaseModel):
    message: str
    screen_name: str

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str 