"""Enumeration types for database models"""
from enum import Enum


class OrderSource(str, Enum):
    """Order source categories"""
    WEBSITE = "website"
    CUSTOM = "custom"
    OTHER = "other"


class OrderStatus(str, Enum):
    """Order status values"""
    PENDING = "pending"
    PRINTING = "printing"
    IN_PRODUCTION = "in_production"
    PAINTING = "painting"
    FINAL_CHECKS = "final_checks"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class ProductSource(str, Enum):
    """Product source categories"""
    ERP = "erp"
    WOOCOMMERCE = "woocommerce"


class CustomerSource(str, Enum):
    """Customer source categories"""
    ERP = "erp"
    WOOCOMMERCE = "woocommerce"


class DiscountType(str, Enum):
    """Discount type categories"""
    FIXED = "fixed"
    PERCENTAGE = "percentage"


class CommissionType(str, Enum):
    """Commission type categories"""
    FIXED = "fixed"
    PERCENTAGE = "percentage"


class ExpenseCategory(str, Enum):
    """Expense category types"""
    MATERIALS = "materials"
    UTILITIES = "utilities"
    EQUIPMENT = "equipment"
    MARKETING = "marketing"
    SHIPPING = "shipping"
    OTHER = "other"
