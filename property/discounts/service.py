from datetime import datetime
from typing import Optional
import pytz
import re
from property.discounts.models import DiscountCode

class DiscountService:
    def __init__(self):
        self.pacific_tz = pytz.timezone('US/Pacific')
        
    EARLY_RISERS_PATTERN = re.compile(
        r"\b(early\s*risers?|early-risers?)\b.*\b(code|promo|promotion|discount)\b"  # "early riser(s)" + promo word
        r"|\b(discount|promo|promotion|code)\b.*\b(early\s*risers?|early-risers?)\b",  # promo word + "early riser(s)"
        re.IGNORECASE
    )
    
    def is_promo_window(self, now_utc: Optional[datetime] = None) -> bool:
        """Check if current time is within the Early Risers promotion window (8-10 AM Pacific)."""
        if now_utc is None:
            now_utc = datetime.now(pytz.UTC)
        
        pacific_time = now_utc.astimezone(self.pacific_tz)
        return 8 <= pacific_time.hour < 10
    
    def is_explicit_request(self, text: str) -> bool:
        """Return True if text clearly asks for Early Risers promo."""
        return bool(self.EARLY_RISERS_PATTERN.search(text))
    
    def generate_code(self) -> DiscountCode:
        """Generate a new discount code."""
        return DiscountCode.generate()
