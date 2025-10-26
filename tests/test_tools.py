"""
Test tool implementations for Sierra Agent.
"""
import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch
from freezegun import freeze_time
from datetime import datetime
import pytz

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from property.orders.tools import lookup_order
from property.products.tools import recommend_products, MAX_PRODUCT_RECOMMENDATIONS
from property.discounts.tools import check_promotional_discount


class TestOrderTools:
    """Test order lookup tool functionality."""
    
    def test_lookup_order_success(self):
        """Test successful order lookup."""
        result = lookup_order("john.doe@example.com", "#W001")
        data = json.loads(result)
        
        assert "customer_name" in data
        assert data["order_status"] == "delivered"
        assert "tracking_url" in data
        assert "TRK123456789" in data["tracking_url"]
        # Check that products are now objects with sku and name
        assert len(data["products"]) > 0
        assert "sku" in data["products"][0]
        assert "name" in data["products"][0]
    
    def test_lookup_order_not_found(self):
        """Test order lookup when order doesn't exist."""
        result = lookup_order("nonexistent@example.com", "#W999")
        data = json.loads(result)
        
        assert "error" in data
        assert data["error"] == "Order not found"
    
    def test_lookup_order_case_insensitive(self):
        """Test order lookup with case insensitive email."""
        result = lookup_order("JOHN.DOE@EXAMPLE.COM", "w001")
        data = json.loads(result)
        
        assert "customer_name" in data
        assert data["order_status"] == "delivered"


class TestProductTools:
    """Test product recommendation tool functionality."""
    
    def test_recommend_products_with_query(self):
        """Test product recommendation with search query."""
        result = recommend_products("backpack")
        data = json.loads(result)
        
        assert isinstance(data, list)
        assert len(data) > 0
        assert any("backpack" in product["name"].lower() for product in data)
    
    def test_recommend_products_empty_query(self):
        """Test product recommendation with empty query."""
        result = recommend_products("")
        data = json.loads(result)
        
        assert isinstance(data, list)
        assert len(data) <= MAX_PRODUCT_RECOMMENDATIONS
    
    def test_recommend_products_no_matches(self):
        """Test product recommendation with no matches."""
        result = recommend_products("nonexistent product")
        data = json.loads(result)
        
        assert isinstance(data, list)
        # Should return all products when no matches found
        assert len(data) > 0
    
    def test_recommend_products_max_limit(self):
        """Test that recommendations are limited to MAX_PRODUCT_RECOMMENDATIONS."""
        result = recommend_products("adventure")
        data = json.loads(result)
        
        assert len(data) <= MAX_PRODUCT_RECOMMENDATIONS


class TestDiscountTools:
    """Test discount promotion tool functionality."""
    
    def test_check_promotional_discount_explicit_request_valid_time(self):
        """Test discount check with explicit request during valid time window."""
        with freeze_time("2024-01-15 17:00:00"):  # 9 AM Pacific (17:00 UTC)
            result = check_promotional_discount("Can I get the Early Risers promo code?")
            data = json.loads(result)
            
            assert data["eligible"] is True
            assert "code" in data
            assert data["code"].startswith("EARLYRISER-")
            assert data["discount_percent"] == 10
    
    def test_check_promotional_discount_explicit_request_invalid_time(self):
        """Test discount check with explicit request outside valid time window."""
        with freeze_time("2024-01-15 22:00:00"):  # 2 PM Pacific (22:00 UTC)
            result = check_promotional_discount("Can I get the Early Risers promo code?")
            data = json.loads(result)
            
            assert data["eligible"] is False
            assert "not currently available" in data["message"]
    
    def test_check_promotional_discount_implicit_request(self):
        """Test discount check with implicit request."""
        result = check_promotional_discount("Any deals right now?")
        data = json.loads(result)
        
        assert data["eligible"] is False
        assert "specific promotional request" in data["message"]
    
    def test_check_promotional_discount_edge_cases(self):
        """Test discount check with various edge cases."""
        # Test early risers with different wording
        with freeze_time("2024-01-15 17:00:00"):  # 9 AM Pacific (17:00 UTC)
            result = check_promotional_discount("I'd like the early risers promotion please")
            data = json.loads(result)
            assert data["eligible"] is True
        
        # Test case insensitive
        with freeze_time("2024-01-15 17:00:00"):  # 9 AM Pacific (17:00 UTC)
            result = check_promotional_discount("EARLY RISERS CODE PLEASE")
            data = json.loads(result)
            assert data["eligible"] is True
    
    def test_check_promotional_discount_time_boundaries(self):
        """Test discount check at time boundaries."""
        # Test at 8:00 AM Pacific (16:00 UTC)
        with freeze_time("2024-01-15 16:00:00"):
            result = check_promotional_discount("Early risers code please")
            data = json.loads(result)
            assert data["eligible"] is True
        
        # Test at 10:00 AM Pacific (18:00 UTC)
        with freeze_time("2024-01-15 18:00:00"):
            result = check_promotional_discount("Early risers code please")
            data = json.loads(result)
            assert data["eligible"] is False


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])
