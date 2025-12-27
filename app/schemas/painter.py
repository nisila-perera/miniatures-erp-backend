"""Painter schemas"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from app.schemas.base import BaseSchema, TimestampSchema


class PainterCreate(BaseModel):
    """Schema for creating a painter"""
    name: str = Field(..., max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    is_active: bool = True


class PainterUpdate(BaseModel):
    """Schema for updating a painter"""
    name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class PainterResponse(BaseSchema, TimestampSchema):
    """Schema for painter response"""
    id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    is_active: bool
