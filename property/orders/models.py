from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Order:
    customer_name: str
    email: str
    order_number: str
    products_ordered: List[str]
    status: str
    tracking_number: Optional[str] = None
    
    def has_tracking(self) -> bool:
        return self.tracking_number is not None
    
    def get_tracking_url(self) -> Optional[str]:
        if not self.tracking_number:
            return None
        return f"https://tools.usps.com/go/TrackConfirmAction?tLabels={self.tracking_number}"
