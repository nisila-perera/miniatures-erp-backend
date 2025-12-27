"""Inventory schemas - Resin and PaintBottle"""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import date
from app.schemas.base import BaseSchema, TimestampSchema


class ResinCreate(BaseModel):
    """Schema for creating a resin entry"""
    color: str = Field(..., max_length=100)
    quantity: Decimal = Field(..., gt=0)
    unit: str = Field(default="kg", max_length=20)
    cost_per_unit: Decimal = Field(..., ge=0)
    purchase_date: date
    purchase_source: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=1000)


class ResinUpdate(BaseModel):
    """Schema for updating a resin entry"""
    color: Optional[str] = Field(None, max_length=100)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit: Optional[str] = Field(None, max_length=20)
    cost_per_unit: Optional[Decimal] = Field(None, ge=0)
    purchase_date: Optional[date] = None
    purchase_source: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=1000)


class ResinResponse(BaseSchema, TimestampSchema):
    """Schema for resin response"""
    id: str
    color: str
    quantity: Decimal
    unit: str
    cost_per_unit: Decimal
    purchase_date: date
    purchase_source: Optional[str]
    notes: Optional[str]


class PaintBottleCreate(BaseModel):
    """Schema for creating a paint bottle entry"""
    color: str = Field(..., max_length=100)
    brand: str = Field(..., max_length=100)
    volume_ml: Decimal = Field(..., gt=0)
    current_volume_ml: Decimal = Field(..., ge=0)
    cost: Decimal = Field(..., ge=0)
    purchase_date: date
    purchase_source: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=1000)


class PaintBottleUpdate(BaseModel):
    """Schema for updating a paint bottle entry"""
    color: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    volume_ml: Optional[Decimal] = Field(None, gt=0)
    current_volume_ml: Optional[Decimal] = Field(None, ge=0)
    cost: Optional[Decimal] = Field(None, ge=0)
    purchase_date: Optional[date] = None
    purchase_source: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=1000)


class PaintBottleResponse(BaseSchema, TimestampSchema):
    """Schema for paint bottle response"""
    id: str
    color: str
    brand: str
    volume_ml: Decimal
    current_volume_ml: Decimal
    cost: Decimal
    purchase_date: date
    purchase_source: Optional[str]
    notes: Optional[str]
