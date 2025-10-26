"""
Tool wrapper functions that expose Sierra Outfitters discount management to the LLM via function calling.
"""
import json
import logging
from property.discounts.service import DiscountService

logger = logging.getLogger(__name__)

# Singleton service instance - loaded once
_discount_service = None

def _get_discount_service():
    """Get singleton discount service instance."""
    global _discount_service
    if _discount_service is None:
        _discount_service = DiscountService()
    return _discount_service

def check_promotional_discount(request_text: str) -> str:
    """
    Check for promotional discount eligibility based on customer request and timing constraints.
    Returns JSON string with eligibility status and discount code if applicable.
    """
    logger.info(f"check_promotional_discount called with request_text='{request_text}'")
    
    try:
        discount_service = _get_discount_service()
        
        # Check if this is an explicit request for Early Risers promotion
        if not discount_service.is_explicit_request(request_text):
            logger.info("Not an explicit Early Risers request")
            return json.dumps({
                "eligible": False,
                "message": "I don't see a specific promotional request in your message. If you're looking for a discount code, please be more specific about which promotion you'd like."
            })
        
        # Check if we're in the valid time window (8-10 AM Pacific)
        if not discount_service.is_promo_window():
            logger.info("Not in Early Risers time window")
            return json.dumps({
                "eligible": False,
                "message": "The Early Risers promotion is not currently available. If you have any other questions or need help with something else, just let me know!"
            })
        
        # Generate discount code
        discount_code = discount_service.generate_code()
        
        result = {
            "eligible": True,
            "code": discount_code.code,
            "discount_percent": discount_code.discount_percent,
            "message": f"Congratulations! Your Early Risers discount code is {discount_code.code} for {discount_code.discount_percent}% off!"
        }
        
        result_json = json.dumps(result)
        logger.info(f"check_promotional_discount returning: {result_json}")
        return result_json
        
    except Exception as e:
        logger.error(f"check_promotional_discount error: {e}")
        return json.dumps({"error": f"Failed to check promotional discount: {str(e)}"})
