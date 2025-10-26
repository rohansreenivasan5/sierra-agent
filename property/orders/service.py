import json
from typing import Optional, Dict, Tuple
from property.orders.models import Order
from config import Paths

class OrderService:
    def __init__(self):
        self._orders: Dict[Tuple[str, str], Order] = {}
        self._load_orders()
    
    def _load_orders(self):
        with open(Paths.ORDERS_FILE, 'r') as f:
            data = json.load(f)
        
        for order_data in data:
            order = Order(
                customer_name=order_data["CustomerName"],
                email=order_data["Email"],
                order_number=order_data["OrderNumber"],
                products_ordered=order_data["ProductsOrdered"],
                status=order_data["Status"],
                tracking_number=order_data.get("TrackingNumber")
            )
            # Normalize email to lowercase and order_number to uppercase with # prefix
            normalized_email = order.email.lower()
            normalized_order_number = order.order_number.upper()
            if not normalized_order_number.startswith('#'):
                normalized_order_number = '#' + normalized_order_number
            
            key = (normalized_email, normalized_order_number)
            self._orders[key] = order
    
    def lookup(self, email: str, order_number: str) -> Optional[Order]:
        # Normalize inputs for lookup
        normalized_email = email.lower()
        normalized_order_number = order_number.upper()
        if not normalized_order_number.startswith('#'):
            normalized_order_number = '#' + normalized_order_number
            
        key = (normalized_email, normalized_order_number)
        return self._orders.get(key)
