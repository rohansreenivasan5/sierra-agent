from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class DiscountCode:
    code: str
    created_at: datetime
    discount_percent: int = 10
    
    @classmethod
    def generate(cls) -> "DiscountCode":
        random_hex = uuid.uuid4().hex[:8].upper()
        code = f"EARLYRISER-{random_hex[:4]}-{random_hex[4:]}"  # EARLYRISER-XXXX-XXXX format
        return cls(code=code, created_at=datetime.now())
