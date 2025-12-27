"""Order repository for database operations"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.order import Order, OrderItem, OrderPainter
from app.models.enums import OrderSource, OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate, OrderItemCreate, OrderPainterCreate
from decimal import Decimal


class OrderRepository:
    """Repository for order database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, order_data: OrderCreate) -> Order:
        """Create a new order with items"""
        # Extract items from order data
        items_data = order_data.items
        order_dict = order_data.model_dump(exclude={'items'})
        
        # Validate order-level discount reason
        if order_dict.get('discount_amount') and order_dict['discount_amount'] > 0:
            if not order_dict.get('discount_reason') or not order_dict['discount_reason'].strip():
                raise ValueError("Discount reason is required when applying a discount")
        
        # Create order
        order = Order(**order_dict)
        # Set default status if not provided
        if not order.status:
            order.status = OrderStatus.PENDING
        
        # Calculate totals
        subtotal = Decimal('0')
        for item_data in items_data:
            item_dict = item_data.model_dump()
            
            # Validate item-level discount reason
            if item_dict.get('discount_amount') and item_dict['discount_amount'] > 0:
                if not item_dict.get('discount_reason') or not item_dict['discount_reason'].strip():
                    raise ValueError("Discount reason is required when applying a discount")
            
            # Calculate item total
            unit_price = Decimal(str(item_dict['unit_price']))
            quantity = item_dict['quantity']
            item_total = unit_price * quantity
            
            # Apply item-level discount
            if item_dict.get('discount_amount'):
                discount_amount = Decimal(str(item_dict['discount_amount']))
                if item_dict.get('discount_type') == 'percentage':
                    item_total -= item_total * (discount_amount / 100)
                else:  # fixed
                    item_total -= discount_amount
            
            item_dict['total_price'] = item_total
            subtotal += item_total
            
            # Create order item
            order_item = OrderItem(**item_dict)
            order.items.append(order_item)
        
        order.subtotal = subtotal
        
        # Apply order-level discount
        total = subtotal
        if order.discount_amount:
            if order.discount_type == 'percentage':
                total -= subtotal * (order.discount_amount / 100)
            else:  # fixed
                total -= order.discount_amount
        
        order.total_amount = total
        order.balance = total
        
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order
    
    def get_by_id(self, order_id: str) -> Optional[Order]:
        """Get an order by ID"""
        return self.db.query(Order).filter(Order.id == order_id).first()
    
    def get_all(
        self,
        source: Optional[OrderSource] = None,
        status: Optional[OrderStatus] = None
    ) -> List[Order]:
        """Get all orders with optional filtering"""
        query = self.db.query(Order)
        
        if source:
            query = query.filter(Order.source == source)
        
        if status:
            query = query.filter(Order.status == status)
        
        return query.all()
    
    def update(self, order_id: str, order_data: OrderUpdate) -> Optional[Order]:
        """Update an order"""
        order = self.get_by_id(order_id)
        if not order:
            return None
        
        update_data = order_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)
        
        self.db.commit()
        self.db.refresh(order)
        return order
    
    def delete(self, order_id: str) -> bool:
        """Delete an order"""
        order = self.get_by_id(order_id)
        if not order:
            return False
        
        self.db.delete(order)
        self.db.commit()
        return True
    
    def assign_painter(self, order_id: str, painter_data: OrderPainterCreate) -> Optional[OrderPainter]:
        """Assign a painter to an order"""
        order = self.get_by_id(order_id)
        if not order:
            return None
        
        painter_assignment = OrderPainter(
            order_id=order_id,
            **painter_data.model_dump()
        )
        
        self.db.add(painter_assignment)
        self.db.commit()
        self.db.refresh(painter_assignment)
        return painter_assignment
    
    def get_order_painters(self, order_id: str) -> List[OrderPainter]:
        """Get all painter assignments for an order"""
        return self.db.query(OrderPainter).filter(OrderPainter.order_id == order_id).all()
    
    def add_order_item(self, order_id: str, item_data: OrderItemCreate) -> Optional[OrderItem]:
        """Add an item to an order and recalculate totals"""
        order = self.get_by_id(order_id)
        if not order:
            return None
        
        # Validate discount reason if discount is applied
        if item_data.discount_amount and item_data.discount_amount > 0:
            if not item_data.discount_reason or not item_data.discount_reason.strip():
                raise ValueError("Discount reason is required when applying a discount")
        
        # Calculate item total price
        item_dict = item_data.model_dump()
        unit_price = Decimal(str(item_dict['unit_price']))
        quantity = item_dict['quantity']
        discount_amount = Decimal(str(item_dict.get('discount_amount', 0)))
        
        # Calculate base price
        item_total = unit_price * quantity
        
        # Apply item-level discount
        if discount_amount > 0:
            if item_dict.get('discount_type') == 'percentage':
                item_total -= item_total * (discount_amount / 100)
            else:  # fixed
                item_total -= discount_amount
        
        item_dict['total_price'] = item_total
        
        # Create order item
        order_item = OrderItem(order_id=order_id, **item_dict)
        self.db.add(order_item)
        
        # Recalculate order totals
        self._recalculate_order_totals(order)
        
        self.db.commit()
        self.db.refresh(order_item)
        return order_item
    
    def _recalculate_order_totals(self, order: Order) -> None:
        """Recalculate order subtotal and total amount"""
        # Calculate subtotal from all items
        subtotal = Decimal('0')
        for item in order.items:
            subtotal += item.total_price
        
        order.subtotal = subtotal
        
        # Apply order-level discount
        total = subtotal
        if order.discount_amount:
            if order.discount_type == 'percentage':
                total -= subtotal * (order.discount_amount / 100)
            else:  # fixed
                total -= order.discount_amount
        
        order.total_amount = total
        
        # Recalculate balance
        order.balance = total - order.paid_amount
        order.is_fully_paid = order.balance <= 0
    
    def get_by_woocommerce_id(self, woocommerce_id: int) -> Optional[Order]:
        """Get an order by WooCommerce ID"""
        return self.db.query(Order).filter(Order.woocommerce_id == woocommerce_id).first()
