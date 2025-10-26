"""
Tool wrapper functions that expose Sierra Outfitters product search to the LLM via function calling.
"""
import json
import logging
from property.products.service import ProductService

logger = logging.getLogger(__name__)

# Maximum number of products to recommend per request
MAX_PRODUCT_RECOMMENDATIONS = 5

# Singleton service instance - loaded once
_product_service = None

def _get_product_service():
    """Get singleton product service instance."""
    global _product_service
    if _product_service is None:
        _product_service = ProductService()
    return _product_service

def recommend_products(query: str) -> str:
    """
    Search for and recommend products from the catalog based on a free-text query.
    Returns JSON string with up to MAX_PRODUCT_RECOMMENDATIONS product recommendations.
    """
    logger.info(f"recommend_products called with query='{query}'")
    
    try:
        product_service = _get_product_service()
        
        # Search for products using keyword matching
        query_terms = query.strip().split()
        products = product_service.search_by_terms(query_terms) if query_terms else []
        
        # Limit to max recommendations or return all if no matches
        if not products:
            products = product_service.get_all()
        
        products = products[:MAX_PRODUCT_RECOMMENDATIONS]
        
        # Format abbreviated product information for the LLM
        abbreviated_product_list = []
        for product in products:
            abbreviated_product_list.append({
                "name": product.product_name,
                "sku": product.sku,
                "description": product.description
            })
        
        result_json = json.dumps(abbreviated_product_list)
        logger.info(f"recommend_products returning: {result_json}")
        return result_json
        
    except Exception as e:
        logger.error(f"recommend_products error: {e}")
        return json.dumps({"error": f"Failed to search products: {str(e)}"})
