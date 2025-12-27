"""Base Pydantic schemas"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(BaseModel):
    """Schema with timestamp fields"""
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
