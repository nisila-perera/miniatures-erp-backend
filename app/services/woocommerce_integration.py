"""WooCommerce integration service"""
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
from app.services.woocommerce_client import WooCommerceClient
from app.repositories.customer import CustomerRepository
from app.repositories.product import ProductRepository
from app.repositories.product_category import ProductCategoryRepository
from app.repositories.order import OrderRepository
from app.models.enums import CustomerSource, ProductSource, OrderSource, OrderStatus
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.order import OrderCreate, OrderItemCreate


class WooCommerceIntegrationService:
    """Service for WooCommerce data synchronization"""
    
    def __init__(self, db: Session):
        self.db = db
        self.client = WooCommerceClient()
        self.customer_repo = CustomerRepository(db)
        self.product_repo = ProductRepository(db)
        self.category_repo = ProductCategoryRepository(db)
        self.order_repo = OrderRepository(db)
    
    def _map_wc_status_to_erp(self, wc_status: str) -> OrderStatus:
        """Map WooCommerce order status to ERP status"""
        status_mapping = {
            "pending": OrderStatus.PENDING,
            "processing": OrderStatus.IN_PRODUCTION,
            "on-hold": OrderStatus.PENDING,
            "completed": OrderStatus.DELIVERED,
            "cancelled": OrderStatus.CANCELLED,
            "refunded": OrderStatus.RETURNED,
            "failed": OrderStatus.CANCELLED,
        }
        return status_mapping.get(wc_status, OrderStatus.PENDING)
    
    def _map_erp_status_to_wc(self, erp_status: OrderStatus) -> str:
        """Map ERP order status to WooCommerce status"""
        status_mapping = {
            OrderStatus.PENDING: "pending",
            OrderStatus.PRINTING: "processing",
            OrderStatus.IN_PRODUCTION: "processing",
            OrderStatus.PAINTING: "processing",
            OrderStatus.FINAL_CHECKS: "processing",
            OrderStatus.SHIPPED: "completed",
            OrderStatus.DELIVERED: "completed",
            OrderStatus.CANCELLED: "cancelled",
            OrderStatus.RETURNED: "refunded",
        }
        return status_mapping.get(erp_status, "processing")
    
    def sync_customers(self) -> Tuple[int, int]:
        """
        Sync customers from WooCommerce
        Returns: (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0
        
        try:
            # Fetch all customers from WooCommerce
            page = 1
            while True:
                wc_customers = self.client.get_customers(per_page=100, page=page)
                if not wc_customers:
                    break
                
                for wc_customer in wc_customers:
                    # Check if customer already exists by woocommerce_id
                    existing_customer = self.customer_repo.get_by_woocommerce_id(wc_customer["id"])
                    
                    customer_data = {
                        "name": f"{wc_customer.get('first_name', '')} {wc_customer.get('last_name', '')}".strip() or "Unknown",
                        "email": wc_customer.get("email", ""),
                        "phone": wc_customer.get("billing", {}).get("phone", ""),
                        "address": wc_customer.get("billing", {}).get("address_1", ""),
                        "city": wc_customer.get("billing", {}).get("city", ""),
                        "postal_code": wc_customer.get("billing", {}).get("postcode", ""),
                        "source": CustomerSource.WOOCOMMERCE,
                        "woocommerce_id": wc_customer["id"]
                    }
                    
                    if existing_customer:
                        # Update existing customer
                        self.customer_repo.update(str(existing_customer.id), CustomerUpdate(**customer_data))
                        updated_count += 1
                    else:
                        # Create new customer
                        self.customer_repo.create(CustomerCreate(**customer_data))
                        created_count += 1
                
                page += 1
        
        except Exception as e:
            raise Exception(f"Failed to sync customers: {str(e)}")
        
        return created_count, updated_count
    
    def sync_products(self) -> Tuple[int, int]:
        """
        Sync products from WooCommerce
        Returns: (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0
        
        try:
            # Ensure we have a default category for WooCommerce products
            default_category = self.category_repo.get_by_name("WooCommerce Products")
            if not default_category:
                from app.schemas.product import ProductCategoryCreate
                default_category = self.category_repo.create(
                    ProductCategoryCreate(
                        name="WooCommerce Products",
                        description="Products imported from WooCommerce"
                    )
                )
            
            # Fetch all products from WooCommerce
            page = 1
            while True:
                wc_products = self.client.get_products(per_page=100, page=page)
                if not wc_products:
                    break
                
                for wc_product in wc_products:
                    # Check if product already exists by woocommerce_id
                    existing_product = self.product_repo.get_by_woocommerce_id(wc_product["id"])
                    
                    # Ensure price is properly formatted as Decimal with 2 decimal places
                    price_str = str(wc_product.get("price", "0") or "0")
                    base_price = Decimal(price_str).quantize(Decimal("0.01"))
                    
                    product_data = {
                        "name": wc_product.get("name", "Unknown Product"),
                        "description": wc_product.get("description", ""),
                        "category_id": str(default_category.id),
                        "base_price": base_price,
                        "is_colored": False,  # Default, can be customized
                        "source": ProductSource.WOOCOMMERCE,
                        "woocommerce_id": wc_product["id"],
                        "is_active": wc_product.get("status") == "publish"
                    }
                    
                    if existing_product:
                        # Update existing product
                        self.product_repo.update(str(existing_product.id), ProductUpdate(**product_data))
                        updated_count += 1
                    else:
                        # Create new product
                        self.product_repo.create(ProductCreate(**product_data))
                        created_count += 1
                
                page += 1
        
        except Exception as e:
            raise Exception(f"Failed to sync products: {str(e)}")
        
        return created_count, updated_count
    
    def sync_orders(self) -> Tuple[int, int]:
        """
        Sync orders from WooCommerce
        Returns: (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0
        
        try:
            # Fetch all orders from WooCommerce
            page = 1
            while True:
                wc_orders = self.client.get_orders(per_page=100, page=page)
                if not wc_orders:
                    break
                
                for wc_order in wc_orders:
                    # Check if order already exists by woocommerce_id
                    existing_order = self.order_repo.get_by_woocommerce_id(wc_order["id"])
                    
                    # Get or create customer
                    wc_customer_id = wc_order.get("customer_id")
                    if wc_customer_id:
                        customer = self.customer_repo.get_by_woocommerce_id(wc_customer_id)
                        if not customer:
                            # Create customer from order billing info
                            billing = wc_order.get("billing", {})
                            customer_data = CustomerCreate(
                                name=f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip() or "Unknown",
                                email=billing.get("email", ""),
                                phone=billing.get("phone", ""),
                                address=billing.get("address_1", ""),
                                city=billing.get("city", ""),
                                postal_code=billing.get("postcode", ""),
                                source=CustomerSource.WOOCOMMERCE,
                                woocommerce_id=wc_customer_id
                            )
                            customer = self.customer_repo.create(customer_data)
                    else:
                        # Create guest customer
                        billing = wc_order.get("billing", {})
                        customer_data = CustomerCreate(
                            name=f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip() or "Guest",
                            email=billing.get("email", ""),
                            phone=billing.get("phone", ""),
                            address=billing.get("address_1", ""),
                            city=billing.get("city", ""),
                            postal_code=billing.get("postcode", ""),
                            source=CustomerSource.WOOCOMMERCE
                        )
                        customer = self.customer_repo.create(customer_data)
                    
                    # Prepare order data
                    order_date = datetime.fromisoformat(wc_order["date_created"].replace("Z", "+00:00"))
                    status = self._map_wc_status_to_erp(wc_order["status"])
                    
                    # Get default category for order items
                    default_category = self.category_repo.get_by_name("WooCommerce Products")
                    
                    # Prepare order items
                    items = []
                    for line_item in wc_order.get("line_items", []):
                        # Try to find product by woocommerce_id
                        product = None
                        if line_item.get("product_id"):
                            product = self.product_repo.get_by_woocommerce_id(line_item["product_id"])
                        
                        # Ensure prices are properly formatted as Decimal with 2 decimal places
                        unit_price = Decimal(str(line_item.get("price", "0"))).quantize(Decimal("0.01"))
                        total_price = Decimal(str(line_item.get("total", "0"))).quantize(Decimal("0.01"))
                        
                        item_data = OrderItemCreate(
                            product_id=str(product.id) if product else None,
                            product_name=line_item.get("name", "Unknown"),
                            product_category_id=str(default_category.id),
                            quantity=line_item.get("quantity", 1),
                            unit_price=unit_price,
                            total_price=total_price,
                            is_colored=False
                        )
                        items.append(item_data)
                    
                    if existing_order:
                        # Update existing order status
                        from app.schemas.order import OrderUpdate
                        self.order_repo.update(
                            str(existing_order.id),
                            OrderUpdate(status=status)
                        )
                        updated_count += 1
                    else:
                        # Calculate subtotal from line items with proper decimal formatting
                        subtotal = sum(Decimal(str(item.get("total", "0"))).quantize(Decimal("0.01")) 
                                     for item in wc_order.get("line_items", []))
                        total_amount = Decimal(str(wc_order.get("total", "0"))).quantize(Decimal("0.01"))
                        
                        # Create new order
                        order_data = OrderCreate(
                            order_number=f"WC-{wc_order['id']}",
                            source=OrderSource.WEBSITE,
                            status=status,
                            customer_id=str(customer.id),
                            order_date=order_date,
                            subtotal=subtotal,
                            total_amount=total_amount,
                            notes=wc_order.get("customer_note", ""),
                            woocommerce_id=wc_order["id"],
                            items=items
                        )
                        self.order_repo.create(order_data)
                        created_count += 1
                
                page += 1
        
        except Exception as e:
            raise Exception(f"Failed to sync orders: {str(e)}")
        
        return created_count, updated_count
    
    def sync_order_status_to_woocommerce(self, order_id: str) -> bool:
        """
        Sync order status from ERP to WooCommerce
        Only syncs if order source is WEBSITE
        """
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        # Only sync website orders
        if order.source != OrderSource.WEBSITE:
            return False
        
        if not order.woocommerce_id:
            raise ValueError(f"Order {order_id} has no WooCommerce ID")
        
        try:
            wc_status = self._map_erp_status_to_wc(order.status)
            self.client.update_order_status(order.woocommerce_id, wc_status)
            return True
        except Exception as e:
            raise Exception(f"Failed to sync order status to WooCommerce: {str(e)}")
