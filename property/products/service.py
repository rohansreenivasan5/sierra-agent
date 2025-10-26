import json
import logging
import pickle
import numpy as np
from typing import List, Optional, Dict
from property.products.models import Product
from config import Paths, USE_EMBEDDINGS

logger = logging.getLogger(__name__)

# Import spaCy components if available
if USE_EMBEDDINGS:
    import spacy

class ProductService:
    def __init__(self):
        self._products: List[Product] = []
        self._sku_index: Dict[str, Product] = {}
        self._spacy_nlp = None
        self._use_embeddings = False
        self._load_products()
        self._load_or_compute_embeddings()
    
    def _load_products(self):
        """Load products from JSON file and build index."""
        with open(Paths.PRODUCTS_FILE, 'r') as f:
            data = json.load(f)
        
        for product_data in data:
            product = Product(
                product_name=product_data["ProductName"],
                sku=product_data["SKU"],
                inventory=product_data["Inventory"],
                description=product_data["Description"],
                tags=product_data["Tags"]
            )
            self._products.append(product)
            self._sku_index[product.sku] = product
        
        logger.info(f"Loaded {len(self._products)} products")
    
    def _load_or_compute_embeddings(self):
        """Load spaCy model for neural embeddings."""
        if not USE_EMBEDDINGS:
            logger.info("spaCy embeddings disabled - using keyword search only")
            self._use_embeddings = False
            return
        
        try:
            # Load spaCy model
            self._spacy_nlp = spacy.load('en_core_web_sm')
            logger.info("Loaded spaCy model for neural embeddings")
            self._use_embeddings = True
            
        except Exception as e:
            logger.warning(f"Failed to load spaCy model: {e}, falling back to keyword search")
            self._use_embeddings = False
    
    def search_by_terms(self, query_terms: List[str]) -> List[Product]:
        """Search products using keyword matching."""
        if not query_terms:
            return []
        
        matching_products = []
        for product in self._products:
            if product.matches_search_terms(query_terms):
                matching_products.append(product)
        
        logger.info(f"Found {len(matching_products)} products matching terms: {query_terms}")
        return matching_products
    
    def search_by_similarity(self, query: str, top_k: int = 5, threshold: float = 0.3) -> List[Product]:
        """Search using spaCy neural embeddings if available, otherwise keyword matching."""
        if self._use_embeddings and self._spacy_nlp:
            try:
                # Compute query embedding
                query_doc = self._spacy_nlp(query)
                query_embedding = query_doc.vector
                
                # Compute cosine similarity with all products
                similarities = []
                for product in self._products:
                    product_text = product.get_embedding_text()
                    product_doc = self._spacy_nlp(product_text)
                    product_embedding = product_doc.vector
                    
                    # Compute cosine similarity
                    similarity = np.dot(query_embedding, product_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(product_embedding)
                    )
                    similarities.append((product, similarity))
                
                # Sort by similarity and filter by threshold
                similarities.sort(key=lambda x: x[1], reverse=True)
                results = [product for product, sim in similarities if sim >= threshold][:top_k]
                
                if results:
                    logger.info(f"Found {len(results)} products using spaCy neural embeddings")
                    return results
            except Exception as e:
                logger.warning(f"spaCy search failed: {e}, falling back to keyword search")
        
        # Fallback to keyword matching
        query_terms = query.strip().split()
        matching_products = self.search_by_terms(query_terms)
        return matching_products[:top_k] if matching_products else self._products[:top_k]
    
    def get_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU."""
        return self._sku_index.get(sku)
    
    def get_all(self) -> List[Product]:
        """Get all products."""
        return self._products.copy()
    
    def get_all_items_formatted(self) -> str:
        """Returns a formatted string listing all products and their descriptions."""
        items = []
        for product in self._products:
            items.append(f"- {product.product_name}: {product.description}")
        return "\n".join(items)
