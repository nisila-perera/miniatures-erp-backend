"""Order service for business logic"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.order import OrderRepository
from app.models.order import Order, OrderPainter
from app.models.enums import OrderSource, OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate, OrderPainterCreate


class OrderService:
    """Service for order business logic"""
    
    def __init__(self, db: Session):
        self.repository = OrderRepository(db)
    
    def create_order(self, order_data: OrderCreate) -> Order:
        """Create a new order"""
        return self.repository.create(order_data)
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order by ID"""
        return self.repository.get_by_id(order_id)
    
    def get_orders(
        self,
        source: Optional[OrderSource] = None,
        status: Optional[OrderStatus] = None
    ) -> List[Order]:
        """Get all orders with optional filtering"""
        return self.repository.get_all(source=source, status=status)
    
    def update_order(self, order_id: str, order_data: OrderUpdate) -> Optional[Order]:
        """Update an order"""
        return self.repository.update(order_id, order_data)
    
    def delete_order(self, order_id: str) -> bool:
        """Delete an order"""
        return self.repository.delete(order_id)
    
    def assign_painter(self, order_id: str, painter_data: OrderPainterCreate) -> Optional[OrderPainter]:
        """Assign a painter to an order"""
        return self.repository.assign_painter(order_id, painter_data)
    
    def get_order_painters(self, order_id: str) -> List[OrderPainter]:
        """Get all painter assignments for an order"""
        return self.repository.get_order_painters(order_id)
    
    def add_order_item(self, order_id: str, item_data) -> Optional[object]:
        """Add an item to an order"""
        return self.repository.add_order_item(order_id, item_data)
