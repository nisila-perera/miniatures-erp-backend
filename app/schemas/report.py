"""Report schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import date
from enum import Enum


class DateRangeFilter(str, Enum):
    """Date range filter options"""
    TODAY = "today"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    CUSTOM = "custom"


class SalesReportRequest(BaseModel):
    """Sales report request parameters"""
    date_range: DateRangeFilter = Field(..., description="Date range filter")
    start_date: Optional[date] = Field(None, description="Start date for custom range")
    end_date: Optional[date] = Field(None, description="End date for custom range")
    group_by_category: bool = Field(False, description="Group results by product category")
    group_by_payment_method: bool = Field(False, description="Group results by payment method")


class CategorySales(BaseModel):
    """Sales data grouped by category"""
    category_id: str
    category_name: str
    total_sales: Decimal
    order_count: int
    average_order_value: Decimal


class PaymentMethodSales(BaseModel):
    """Sales data grouped by payment method"""
    payment_method_id: str
    payment_method_name: str
    total_sales: Decimal
    order_count: int
    average_order_value: Decimal


class SalesReportResponse(BaseModel):
    """Sales report response"""
    total_sales: Decimal = Field(..., description="Total sales amount")
    order_count: int = Field(..., description="Total number of orders")
    average_order_value: Decimal = Field(..., description="Average order value")
    start_date: date
    end_date: date
    by_category: Optional[List[CategorySales]] = None
    by_payment_method: Optional[List[PaymentMethodSales]] = None


class ProfitLossRequest(BaseModel):
    """Profit and loss report request parameters"""
    date_range: DateRangeFilter = Field(..., description="Date range filter")
    start_date: Optional[date] = Field(None, description="Start date for custom range")
    end_date: Optional[date] = Field(None, description="End date for custom range")


class ExpenseBreakdown(BaseModel):
    """Expense breakdown by category"""
    category: str
    amount: Decimal


class ProfitLossResponse(BaseModel):
    """Profit and loss report response"""
    total_revenue: Decimal = Field(..., description="Total revenue from orders")
    total_expenses: Decimal = Field(..., description="Total expenses")
    net_profit: Decimal = Field(..., description="Net profit (revenue - expenses)")
    start_date: date
    end_date: date
    expense_breakdown: List[ExpenseBreakdown] = Field(..., description="Expenses grouped by category")


class MaterialUsageRequest(BaseModel):
    """Material usage report request parameters"""
    date_range: DateRangeFilter = Field(..., description="Date range filter")
    start_date: Optional[date] = Field(None, description="Start date for custom range")
    end_date: Optional[date] = Field(None, description="End date for custom range")


class ResinUsage(BaseModel):
    """Resin usage grouped by color"""
    color: str
    total_quantity: Decimal
    unit: str
    total_cost: Decimal


class PaintBottleUsage(BaseModel):
    """Paint bottle usage by individual bottle"""
    bottle_id: str
    color: str
    brand: str
    volume_ml: Decimal
    cost: Decimal


class MaterialUsageResponse(BaseModel):
    """Material usage report response"""
    start_date: date
    end_date: date
    resin_by_color: List[ResinUsage] = Field(..., description="Resin grouped by color")
    paint_bottles: List[PaintBottleUsage] = Field(..., description="Paint bottles")
    total_material_cost: Decimal = Field(..., description="Total cost of all materials")


class BestSellersRequest(BaseModel):
    """Best-selling products report request parameters"""
    date_range: DateRangeFilter = Field(..., description="Date range filter")
    start_date: Optional[date] = Field(None, description="Start date for custom range")
    end_date: Optional[date] = Field(None, description="End date for custom range")
    category_id: Optional[str] = Field(None, description="Filter by product category")


class BestSellingProduct(BaseModel):
    """Best-selling product data"""
    product_id: Optional[str] = Field(None, description="Product ID (null for custom products)")
    product_name: str
    category_id: str
    category_name: str
    quantity_sold: int
    revenue: Decimal


class BestSellersResponse(BaseModel):
    """Best-selling products report response"""
    start_date: date
    end_date: date
    products: List[BestSellingProduct] = Field(..., description="Products ranked by quantity sold")


class CustomerAnalyticsRequest(BaseModel):
    """Customer analytics report request parameters"""
    date_range: DateRangeFilter = Field(..., description="Date range filter")
    start_date: Optional[date] = Field(None, description="Start date for custom range")
    end_date: Optional[date] = Field(None, description="End date for custom range")


class TopCustomer(BaseModel):
    """Top customer data"""
    customer_id: str
    customer_name: str
    total_spending: Decimal
    order_count: int


class CustomerAnalyticsResponse(BaseModel):
    """Customer analytics report response"""
    start_date: date
    end_date: date
    total_customers: int = Field(..., description="Total number of customers")
    average_order_value_per_customer: Decimal = Field(..., description="Average order value per customer")
    repeat_customer_rate: Decimal = Field(..., description="Percentage of customers with more than one order")
    top_customers: List[TopCustomer] = Field(..., description="Top customers ranked by total spending")
