"""Report service for generating business reports"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List
from app.models.order import Order, OrderItem
from app.models.payment import Payment, PaymentMethod
from app.models.product import ProductCategory
from app.models.expense import Expense
from app.models.enums import ExpenseCategory
from app.models.inventory import Resin, PaintBottle
from app.models.customer import Customer
from app.schemas.report import (
    SalesReportRequest,
    SalesReportResponse,
    CategorySales,
    PaymentMethodSales,
    DateRangeFilter,
    ProfitLossRequest,
    ProfitLossResponse,
    ExpenseBreakdown,
    MaterialUsageRequest,
    MaterialUsageResponse,
    ResinUsage,
    PaintBottleUsage,
    BestSellersRequest,
    BestSellersResponse,
    BestSellingProduct,
    CustomerAnalyticsRequest,
    CustomerAnalyticsResponse,
    TopCustomer
)


class ReportService:
    """Service for generating business reports"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _get_date_range(self, date_range: DateRangeFilter, start_date: Optional[date], end_date: Optional[date]) -> tuple[date, date]:
        """Calculate start and end dates based on filter"""
        today = date.today()
        
        if date_range == DateRangeFilter.TODAY:
            return today, today
        elif date_range == DateRangeFilter.THIS_WEEK:
            # Start of week (Monday)
            start = today - timedelta(days=today.weekday())
            return start, today
        elif date_range == DateRangeFilter.THIS_MONTH:
            # Start of month
            start = today.replace(day=1)
            return start, today
        elif date_range == DateRangeFilter.CUSTOM:
            if not start_date or not end_date:
                raise ValueError("start_date and end_date are required for custom date range")
            return start_date, end_date
        else:
            raise ValueError(f"Invalid date range filter: {date_range}")
    
    def generate_sales_report(self, request: SalesReportRequest) -> SalesReportResponse:
        """Generate sales report based on request parameters"""
        start_date, end_date = self._get_date_range(
            request.date_range,
            request.start_date,
            request.end_date
        )
        
        # Convert dates to datetime for comparison
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Base query for orders in date range
        base_query = self.db.query(Order).filter(
            Order.order_date >= start_datetime,
            Order.order_date <= end_datetime
        )
        
        # Calculate total sales and order count
        orders = base_query.all()
        total_sales = sum(order.total_amount for order in orders)
        order_count = len(orders)
        average_order_value = total_sales / order_count if order_count > 0 else Decimal(0)
        
        # Initialize response
        response = SalesReportResponse(
            total_sales=total_sales,
            order_count=order_count,
            average_order_value=average_order_value,
            start_date=start_date,
            end_date=end_date
        )
        
        # Group by category if requested
        if request.group_by_category:
            response.by_category = self._group_by_category(start_datetime, end_datetime)
        
        # Group by payment method if requested
        if request.group_by_payment_method:
            response.by_payment_method = self._group_by_payment_method(start_datetime, end_datetime)
        
        return response
    
    def _group_by_category(self, start_datetime: datetime, end_datetime: datetime) -> List[CategorySales]:
        """Group sales by product category"""
        # Query to get sales by category
        results = self.db.query(
            ProductCategory.id,
            ProductCategory.name,
            func.sum(OrderItem.total_price).label('total_sales'),
            func.count(func.distinct(Order.id)).label('order_count')
        ).join(
            OrderItem, OrderItem.product_category_id == ProductCategory.id
        ).join(
            Order, Order.id == OrderItem.order_id
        ).filter(
            Order.order_date >= start_datetime,
            Order.order_date <= end_datetime
        ).group_by(
            ProductCategory.id,
            ProductCategory.name
        ).all()
        
        category_sales = []
        for result in results:
            total_sales = result.total_sales or Decimal(0)
            order_count = result.order_count or 0
            avg_order_value = total_sales / order_count if order_count > 0 else Decimal(0)
            
            category_sales.append(CategorySales(
                category_id=str(result.id),
                category_name=result.name,
                total_sales=total_sales,
                order_count=order_count,
                average_order_value=avg_order_value
            ))
        
        return category_sales
    
    def _group_by_payment_method(self, start_datetime: datetime, end_datetime: datetime) -> List[PaymentMethodSales]:
        """Group sales by payment method"""
        # Query to get sales by payment method
        results = self.db.query(
            PaymentMethod.id,
            PaymentMethod.name,
            func.sum(Payment.amount).label('total_sales'),
            func.count(func.distinct(Order.id)).label('order_count')
        ).join(
            Payment, Payment.payment_method_id == PaymentMethod.id
        ).join(
            Order, Order.id == Payment.order_id
        ).filter(
            Order.order_date >= start_datetime,
            Order.order_date <= end_datetime
        ).group_by(
            PaymentMethod.id,
            PaymentMethod.name
        ).all()
        
        payment_method_sales = []
        for result in results:
            total_sales = result.total_sales or Decimal(0)
            order_count = result.order_count or 0
            avg_order_value = total_sales / order_count if order_count > 0 else Decimal(0)
            
            payment_method_sales.append(PaymentMethodSales(
                payment_method_id=str(result.id),
                payment_method_name=result.name,
                total_sales=total_sales,
                order_count=order_count,
                average_order_value=avg_order_value
            ))
        
        return payment_method_sales
    
    def generate_profit_loss_report(self, request: ProfitLossRequest) -> ProfitLossResponse:
        """Generate profit and loss report based on request parameters"""
        start_date, end_date = self._get_date_range(
            request.date_range,
            request.start_date,
            request.end_date
        )
        
        # Convert dates to datetime for comparison
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Calculate total revenue from orders
        orders = self.db.query(Order).filter(
            Order.order_date >= start_datetime,
            Order.order_date <= end_datetime
        ).all()
        total_revenue = sum(order.total_amount for order in orders)
        
        # Calculate total expenses
        expenses = self.db.query(Expense).filter(
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date
        ).all()
        total_expenses = sum(expense.amount for expense in expenses)
        
        # Calculate net profit
        net_profit = total_revenue - total_expenses
        
        # Generate expense breakdown by category
        expense_breakdown = self._get_expense_breakdown(start_date, end_date)
        
        return ProfitLossResponse(
            total_revenue=total_revenue,
            total_expenses=total_expenses,
            net_profit=net_profit,
            start_date=start_date,
            end_date=end_date,
            expense_breakdown=expense_breakdown
        )
    
    def _get_expense_breakdown(self, start_date: date, end_date: date) -> List[ExpenseBreakdown]:
        """Get expense breakdown by category"""
        results = self.db.query(
            Expense.category,
            func.sum(Expense.amount).label('total_amount')
        ).filter(
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date
        ).group_by(
            Expense.category
        ).all()
        
        breakdown = []
        for result in results:
            breakdown.append(ExpenseBreakdown(
                category=result.category.value,
                amount=result.total_amount or Decimal(0)
            ))
        
        return breakdown
    
    def generate_material_usage_report(self, request: MaterialUsageRequest) -> MaterialUsageResponse:
        """Generate material usage report based on request parameters"""
        start_date, end_date = self._get_date_range(
            request.date_range,
            request.start_date,
            request.end_date
        )
        
        # Get resin usage grouped by color
        resin_results = self.db.query(
            Resin.color,
            Resin.unit,
            func.sum(Resin.quantity).label('total_quantity'),
            func.sum(Resin.quantity * Resin.cost_per_unit).label('total_cost')
        ).filter(
            Resin.purchase_date >= start_date,
            Resin.purchase_date <= end_date
        ).group_by(
            Resin.color,
            Resin.unit
        ).all()
        
        resin_by_color = []
        for result in resin_results:
            resin_by_color.append(ResinUsage(
                color=result.color,
                total_quantity=result.total_quantity or Decimal(0),
                unit=result.unit,
                total_cost=result.total_cost or Decimal(0)
            ))
        
        # Get paint bottles
        paint_results = self.db.query(PaintBottle).filter(
            PaintBottle.purchase_date >= start_date,
            PaintBottle.purchase_date <= end_date
        ).all()
        
        paint_bottles = []
        for paint in paint_results:
            paint_bottles.append(PaintBottleUsage(
                bottle_id=str(paint.id),
                color=paint.color,
                brand=paint.brand,
                volume_ml=paint.volume_ml,
                cost=paint.cost
            ))
        
        # Calculate total material cost
        resin_cost = sum(r.total_cost for r in resin_by_color)
        paint_cost = sum(p.cost for p in paint_bottles)
        total_material_cost = resin_cost + paint_cost
        
        return MaterialUsageResponse(
            start_date=start_date,
            end_date=end_date,
            resin_by_color=resin_by_color,
            paint_bottles=paint_bottles,
            total_material_cost=total_material_cost
        )
    
    def generate_best_sellers_report(self, request) -> 'BestSellersResponse':
        """Generate best-selling products report based on request parameters"""
        from app.schemas.report import BestSellersResponse, BestSellingProduct
        
        start_date, end_date = self._get_date_range(
            request.date_range,
            request.start_date,
            request.end_date
        )
        
        # Convert dates to datetime for comparison
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Base query for order items in date range
        query = self.db.query(
            OrderItem.product_id,
            OrderItem.product_name,
            OrderItem.product_category_id,
            ProductCategory.name.label('category_name'),
            func.sum(OrderItem.quantity).label('quantity_sold'),
            func.sum(OrderItem.total_price).label('revenue')
        ).join(
            Order, Order.id == OrderItem.order_id
        ).join(
            ProductCategory, ProductCategory.id == OrderItem.product_category_id
        ).filter(
            Order.order_date >= start_datetime,
            Order.order_date <= end_datetime
        )
        
        # Apply category filter if provided
        if request.category_id:
            query = query.filter(OrderItem.product_category_id == request.category_id)
        
        # Group by product and category
        query = query.group_by(
            OrderItem.product_id,
            OrderItem.product_name,
            OrderItem.product_category_id,
            ProductCategory.name
        )
        
        # Order by quantity sold descending
        query = query.order_by(func.sum(OrderItem.quantity).desc())
        
        results = query.all()
        
        # Build response
        products = []
        for result in results:
            products.append(BestSellingProduct(
                product_id=str(result.product_id) if result.product_id else None,
                product_name=result.product_name,
                category_id=str(result.product_category_id),
                category_name=result.category_name,
                quantity_sold=result.quantity_sold or 0,
                revenue=result.revenue or Decimal(0)
            ))
        
        return BestSellersResponse(
            start_date=start_date,
            end_date=end_date,
            products=products
        )
    
    def generate_customer_analytics_report(self, request: CustomerAnalyticsRequest) -> CustomerAnalyticsResponse:
        """Generate customer analytics report based on request parameters"""
        start_date, end_date = self._get_date_range(
            request.date_range,
            request.start_date,
            request.end_date
        )
        
        # Convert dates to datetime for comparison
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Get all customers (not filtered by date - total count)
        total_customers = self.db.query(Customer).count()
        
        # Get customers with orders in the date range
        customers_with_orders = self.db.query(
            Customer.id,
            Customer.name,
            func.count(Order.id).label('order_count'),
            func.sum(Order.total_amount).label('total_spending')
        ).join(
            Order, Order.customer_id == Customer.id
        ).filter(
            Order.order_date >= start_datetime,
            Order.order_date <= end_datetime
        ).group_by(
            Customer.id,
            Customer.name
        ).all()
        
        # Calculate average order value per customer
        total_revenue = sum(c.total_spending for c in customers_with_orders if c.total_spending)
        customers_with_orders_count = len(customers_with_orders)
        average_order_value_per_customer = (
            total_revenue / customers_with_orders_count 
            if customers_with_orders_count > 0 
            else Decimal(0)
        )
        
        # Calculate repeat customer rate
        repeat_customers = sum(1 for c in customers_with_orders if c.order_count > 1)
        repeat_customer_rate = (
            Decimal(repeat_customers) / Decimal(total_customers) * Decimal(100)
            if total_customers > 0
            else Decimal(0)
        )
        
        # Get top customers ranked by total spending
        top_customers_data = sorted(
            customers_with_orders,
            key=lambda c: c.total_spending or Decimal(0),
            reverse=True
        )[:10]  # Top 10 customers
        
        top_customers = []
        for customer in top_customers_data:
            top_customers.append(TopCustomer(
                customer_id=str(customer.id),
                customer_name=customer.name,
                total_spending=customer.total_spending or Decimal(0),
                order_count=customer.order_count
            ))
        
        return CustomerAnalyticsResponse(
            start_date=start_date,
            end_date=end_date,
            total_customers=total_customers,
            average_order_value_per_customer=average_order_value_per_customer,
            repeat_customer_rate=repeat_customer_rate,
            top_customers=top_customers
        )
