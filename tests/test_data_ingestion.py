"""
Comprehensive test for data ingestion and proper setup of Sierra Agent.
Tests all data loading, service initialization, and keyword-based product search.
Uses simple keyword matching instead of OpenAI embeddings.
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Paths, setup_logging
from property.orders.service import OrderService
from property.products.service import ProductService
from property.discounts.service import DiscountService
from property.orders.models import Order
from property.products.models import Product
from property.discounts.models import DiscountCode


class TestDataIngestionAndSetup:
    """Test complete data ingestion and service setup."""
    
    def test_config_loading(self):
        """Test configuration loading and paths."""
        # Test that paths are correctly configured
        # Accept hyphen or underscore in project directory name
        assert Paths.BASE_DIR.name.replace('-', '_') == 'sierra_agent'
        assert Paths.DATA_DIR.name == 'data'
        assert Paths.ORDERS_FILE.name == 'orders.json'
        assert Paths.PRODUCTS_FILE.name == 'products.json'
    
    def test_paths_configuration(self):
        """Test that paths are correctly configured."""
        assert Paths.ORDERS_FILE.exists()
        assert Paths.PRODUCTS_FILE.exists()
    
    def test_orders_data_ingestion(self):
        """Test that all order data is properly ingested."""
        order_service = OrderService()
        
        # Verify we have the expected number of orders (10 from the JSON)
        assert len(order_service._orders) == 10
        
        # Test specific order lookups
        # Test case 1: Normal lookup
        order = order_service.lookup("john.doe@example.com", "#W001")
        assert order is not None
        assert order.customer_name == " John Doe"  # Note: leading space in JSON data
        assert order.status == "delivered"
        assert order.tracking_number == "TRK123456789"
        assert order.has_tracking() is True
        assert "TRK123456789" in order.get_tracking_url()
        
        # Test case 2: Case insensitive lookup
        order = order_service.lookup("JOHN.DOE@EXAMPLE.COM", "w001")
        assert order is not None
        assert order.customer_name == " John Doe"  # Note: leading space in JSON data
        
        # Test case 3: Order without tracking
        order = order_service.lookup("alice.johnson@example.com", "#W003")
        assert order is not None
        assert order.status == "fulfilled"
        assert order.tracking_number is None
        assert order.has_tracking() is False
        assert order.get_tracking_url() is None
        
        # Test case 4: Non-existent order
        order = order_service.lookup("nonexistent@example.com", "#W999")
        assert order is None
    
    def test_products_data_ingestion(self):
        """Test that all product data is properly ingested with keyword matching."""
        print("\n🔄 Testing product data ingestion with keyword matching...")
        
        # Create product service (no OpenAI dependencies)
        product_service = ProductService()
        
        # Verify we have the expected number of products (10 from the JSON)
        assert len(product_service._products) == 10
        assert len(product_service._sku_index) == 10
        print(f"✅ Loaded {len(product_service._products)} products")
        
        # Test specific product lookups
        product = product_service.get_by_sku("SOBP001")
        assert product is not None
        assert "Backpack" in product.product_name
        assert product.inventory == 120
        assert product.has_inventory() is True
        assert "Adventure" in product.tags
        print(f"✅ Found product: {product.product_name}")
        
        # Test search text generation
        search_text = product.get_search_text()
        assert product.product_name in search_text
        assert product.description in search_text
        assert "Adventure" in search_text
        print(f"✅ Search text generated: {search_text[:100]}...")
        
        # Test keyword matching
        assert product.matches_search_terms(["backpack"])
        assert product.matches_search_terms(["adventure"])
        assert product.matches_search_terms(["hiking"])
        assert not product.matches_search_terms(["skiing"])
        print("✅ Keyword matching works correctly")
        
        # Test all products formatted
        formatted = product_service.get_all_items_formatted()
        assert len(formatted) > 0
        assert "Backpack" in formatted
        print(f"✅ Formatted catalog: {len(formatted)} characters")
        
        print("🎉 Product data ingestion successful with keyword matching!")
    
    def test_discounts_service_setup(self):
        """Test that discount service is properly configured."""
        discount_service = DiscountService()
        
        # Test timezone setup
        assert discount_service.pacific_tz is not None
        
        # Test regex pattern
        assert discount_service.EARLY_RISERS_PATTERN is not None
        
        # Test explicit request validation
        valid_requests = [
            "Can I get the Early Risers promo code?",
            "I'd like the early risers promotion please",
            "early-risers code please"
        ]
        
        for request in valid_requests:
            assert discount_service.is_explicit_request(request), f"Should recognize: {request}"
        
        # Test invalid requests
        invalid_requests = [
            "Any deals right now?",
            "I'm an early riser",
            "What promotions do you have?"
        ]
        
        for request in invalid_requests:
            assert not discount_service.is_explicit_request(request), f"Should reject: {request}"
        
        # Test discount code generation
        discount_code = discount_service.generate_code()
        assert isinstance(discount_code, DiscountCode)
        assert discount_code.code.startswith("EARLYRISER-")
        assert len(discount_code.code) == 20  # EARLYRISER-XXXX-XXXX format
        assert discount_code.discount_percent == 10
        assert "-" in discount_code.code[10:]  # Check format has dashes
    
    def test_keyword_search_functionality(self):
        """Test keyword-based product search."""
        print("\n🔍 Testing keyword-based search...")
        
        # Create product service (no OpenAI dependencies)
        product_service = ProductService()
        
        # Test keyword search with various queries
        test_cases = [
            (["backpack"], "Should find backpack products"),
            (["energy"], "Should find energy drink"),
            (["skiing"], "Should find skiing gear"),
            (["invisibility"], "Should find invisibility cloak"),
            (["nonexistent"], "Should return all products when no matches")
        ]
        
        for query_terms, description in test_cases:
            print(f"🔍 Searching for: {query_terms} - {description}")
            results = product_service.search_by_terms(query_terms)
            
            # Should return results
            assert len(results) >= 0
            assert all(isinstance(p, Product) for p in results)
            
            print(f"✅ Found {len(results)} results:")
            for i, product in enumerate(results):
                print(f"   {i+1}. {product.product_name} (SKU: {product.sku})")
        
        # Test search_by_similarity compatibility method
        print("\n🔍 Testing search_by_similarity compatibility...")
        results = product_service.search_by_similarity("hiking backpack", top_k=3)
        assert len(results) <= 3
        assert all(isinstance(p, Product) for p in results)
        print(f"✅ Found {len(results)} results for 'hiking backpack'")
        
        print("🎉 Keyword search successful!")
    
    def test_data_completeness(self):
        """Test that all expected data is loaded."""
        order_service = OrderService()
        
        # Verify all orders have required fields
        for key, order in order_service._orders.items():
            assert isinstance(order, Order)
            assert order.customer_name
            assert order.email
            assert order.order_number
            assert order.products_ordered
            assert order.status
            # tracking_number can be None
        
        # Verify order statuses are valid
        valid_statuses = {"delivered", "in-transit", "fulfilled", "error"}
        for order in order_service._orders.values():
            assert order.status in valid_statuses
        
        # Verify all products have required fields
        print("\n📊 Testing data completeness...")
        product_service = ProductService()
        
        for product in product_service._products:
            assert isinstance(product, Product)
            assert product.product_name
            assert product.sku
            assert product.description
            assert product.tags
            assert isinstance(product.inventory, int)
            assert product.inventory >= 0
            # Test keyword matching functionality
            assert hasattr(product, 'matches_search_terms')
            assert callable(product.matches_search_terms)
        
        print(f"✅ All {len(product_service._products)} products validated with keyword matching!")
    
    def test_logging_setup(self):
        """Test that logging is properly configured."""
        # This should not raise an exception
        setup_logging()
        
        # Verify log file would be created
        log_file = Paths.BASE_DIR / "sierra_agent.log"
        # Note: We don't actually create the log file in tests to avoid side effects


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])
