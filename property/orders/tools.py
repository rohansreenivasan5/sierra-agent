"""
Tool wrapper functions that expose Sierra Outfitters order management to the LLM via function calling.
"""
import json
import logging
from property.orders.service import OrderService
from property.products.service import ProductService

logger = logging.getLogger(__name__)

# Singleton service instances - loaded once
_order_service = None
_product_service = None

def _get_order_service():
    """Get singleton order service instance."""
    global _order_service
    if _order_service is None:
        _order_service = OrderService()
    return _order_service

def _get_product_service():
    """Get singleton product service instance."""
    global _product_service
    if _product_service is None:
        _product_service = ProductService()
    return _product_service

def lookup_order(email: str, order_number: str) -> str:
    """
    Look up customer order status and tracking information using email and order number.
    Returns JSON string with order details or error message.
    """
    logger.info(f"lookup_order called with email='{email}', order_number='{order_number}'")
    
    try:
        order_service = _get_order_service()
        order = order_service.lookup(email, order_number)
        
        if not order:
            logger.info("Order not found")
            return json.dumps({"error": "Order not found"})
        
        # Resolve SKUs to product names
        product_service = _get_product_service()
        resolved_products = []
        missing_products = []
        
        for sku in order.products_ordered:
            product = product_service.get_by_sku(sku)
            if product:
                resolved_products.append({
                    "sku": sku,
                    "name": product.product_name
                })
            else:
                # Track missing products separately
                missing_products.append(sku)
        
        # Add missing products with explicit note
        for sku in missing_products:
            resolved_products.append({
                "sku": sku,
                "name": f"Product {sku} (not found in catalog)"
            })
        
        # Format order information for the LLM
        order_info = {
            "found": True,
            "customer_name": order.customer_name,
            "order_status": order.status,  # Rename to avoid confusion
            "products": resolved_products
        }
        
        # Add tracking URL if available
        if order.has_tracking():
            order_info["tracking_url"] = order.get_tracking_url()
            order_info["tracking_number"] = order.tracking_number
        
        result_json = json.dumps(order_info)
        logger.info(f"lookup_order returning: {result_json}")
        return result_json
        
    except Exception as e:
        logger.error(f"lookup_order error: {e}")
        return json.dumps({"error": f"Failed to lookup order: {str(e)}"})
