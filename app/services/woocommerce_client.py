"""WooCommerce API client"""
from typing import List, Dict, Any, Optional
import requests
from requests.auth import HTTPBasicAuth
from app.core.config import settings


class WooCommerceClient:
    """Client for interacting with WooCommerce REST API"""
    
    def __init__(self):
        self.base_url = settings.WOOCOMMERCE_URL.rstrip('/')
        self.consumer_key = settings.WOOCOMMERCE_CONSUMER_KEY
        self.consumer_secret = settings.WOOCOMMERCE_CONSUMER_SECRET
        self.api_version = "wc/v3"
        
        if not self.base_url or not self.consumer_key or not self.consumer_secret:
            raise ValueError("WooCommerce credentials not configured")
    
    def _get_url(self, endpoint: str) -> str:
        """Construct full API URL"""
        return f"{self.base_url}/wp-json/{self.api_version}/{endpoint}"
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to WooCommerce API"""
        url = self._get_url(endpoint)
        auth = HTTPBasicAuth(self.consumer_key, self.consumer_secret)
        
        try:
            response = requests.request(method, url, auth=auth, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"WooCommerce API error: {str(e)}")
    
    def get_orders(self, per_page: int = 100, page: int = 1) -> List[Dict[str, Any]]:
        """Fetch orders from WooCommerce"""
        params = {"per_page": per_page, "page": page}
        return self._make_request("GET", "orders", params=params)
    
    def get_order(self, order_id: int) -> Dict[str, Any]:
        """Fetch a single order from WooCommerce"""
        return self._make_request("GET", f"orders/{order_id}")
    
    def update_order_status(self, order_id: int, status: str) -> Dict[str, Any]:
        """Update order status in WooCommerce"""
        data = {"status": status}
        return self._make_request("PUT", f"orders/{order_id}", json=data)
    
    def get_customers(self, per_page: int = 100, page: int = 1) -> List[Dict[str, Any]]:
        """Fetch customers from WooCommerce"""
        params = {"per_page": per_page, "page": page}
        return self._make_request("GET", "customers", params=params)
    
    def get_customer(self, customer_id: int) -> Dict[str, Any]:
        """Fetch a single customer from WooCommerce"""
        return self._make_request("GET", f"customers/{customer_id}")
    
    def get_products(self, per_page: int = 100, page: int = 1) -> List[Dict[str, Any]]:
        """Fetch products from WooCommerce"""
        params = {"per_page": per_page, "page": page}
        return self._make_request("GET", "products", params=params)
    
    def get_product(self, product_id: int) -> Dict[str, Any]:
        """Fetch a single product from WooCommerce"""
        return self._make_request("GET", f"products/{product_id}")
