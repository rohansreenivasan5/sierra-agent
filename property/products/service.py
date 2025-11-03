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
                # Skip empty queries to avoid spaCy errors
                if not query or not query.strip():
                    logger.warning("Empty query, falling back to keyword search")
                    query_terms = []
                    matching_products = self.search_by_terms(query_terms)
                    return matching_products[:top_k] if matching_products else self._products[:top_k]
                
                # Compute query embedding
                query_doc = self._spacy_nlp(query)
                query_embedding = query_doc.vector
                
                # Check if query embedding is valid (non-zero)
                if np.linalg.norm(query_embedding) == 0:
                    logger.warning("Zero query embedding, falling back to keyword search")
                    query_terms = query.strip().split()
                    matching_products = self.search_by_terms(query_terms)
                    return matching_products[:top_k] if matching_products else self._products[:top_k]
                
                # Compute cosine similarity with all products
                similarities = []
                for product in self._products:
                    product_text = product.get_embedding_text()
                    product_doc = self._spacy_nlp(product_text)
                    product_embedding = product_doc.vector
                    
                    # Compute cosine similarity
                    product_norm = np.linalg.norm(product_embedding)
                    if product_norm == 0:
                        continue  # Skip products with zero embeddings
                    
                    similarity = np.dot(query_embedding, product_embedding) / (
                        np.linalg.norm(query_embedding) * product_norm
                    )
                    similarities.append((product, similarity))
                
                # Sort by similarity (descending)
                similarities.sort(key=lambda x: x[1], reverse=True)
                
                # Filter by threshold and take top_k
                filtered_results = [product for product, sim in similarities if sim >= threshold]
                
                # If threshold filtering removes all results, return top results anyway (embeddings are working)
                if not filtered_results and similarities:
                    logger.info(f"No products above threshold {threshold}, returning top {top_k} results by similarity")
                    results = [product for product, sim in similarities[:top_k]]
                else:
                    results = filtered_results[:top_k]
                
                if results:
                    logger.info(f"Found {len(results)} products using spaCy neural embeddings (threshold: {threshold})")
                    return results
                    
            except Exception as e:
                logger.warning(f"spaCy search failed: {e}, falling back to keyword search")
        
        # Fallback to keyword matching (only if embeddings not available or failed)
        query_terms = query.strip().split() if query else []
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
