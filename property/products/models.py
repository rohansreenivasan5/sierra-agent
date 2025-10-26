from dataclasses import dataclass
from typing import List, Optional
import numpy as np

@dataclass
class Product:
    product_name: str
    sku: str
    inventory: int
    description: str
    tags: List[str]
    embedding: Optional[np.ndarray] = None
    
    def has_inventory(self) -> bool:
        return self.inventory > 0
    
    def get_search_text(self) -> str:
        """Combine name, description, and tags for keyword search."""
        return f"{self.product_name} {self.description} {' '.join(self.tags)}"
    
    def get_embedding_text(self) -> str:
        """Get text for embedding computation."""
        return f"{self.product_name}. {self.description}. {' '.join(self.tags)}"
    
    def matches_search_terms(self, terms: List[str]) -> bool:
        """Check if product matches any of the search terms (case-insensitive)."""
        if not terms:
            return False
        
        search_text = self.get_search_text().lower()
        return any(term.lower() in search_text for term in terms)
