"""
Unit tests for models module.
"""

import unittest
import sys
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from project.src.models.user import User
from project.src.models.product import Product
from project.src.models.order import Order
from project.src.models.exceptions import (
    ValidationError,
    NotFoundError,
    DatabaseError
)


class TestUserModel(unittest.TestCase):
    """Test cases for User model."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.valid_user_data = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com',
            'password_hash': 'hashed_password_123',
            'created_at': datetime.now(),
            'is_active': True
        }
        
    def test_user_creation_valid_data(self) -> None:
        """Test user creation with valid data."""
        try:
            user = User(**self.valid_user_data)
            self.assertEqual(user.username, 'testuser')
            self.assertEqual(user.email, 'test@example.com')
            self.assertTrue(user.is_active)
        except Exception as e:
            self.fail(f"User creation failed with valid data: {e}")
    
    def test_user_creation_invalid_email(self) -> None:
        """Test user creation with invalid email."""
        invalid_data = self.valid_user_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        with self.assertRaises(ValidationError):
            User(**invalid_data)
    
    def test_user_creation_missing_required_field(self) -> None:
        """Test user creation with missing required field."""
        incomplete_data = self.valid_user_data.copy()
        del incomplete_data['username']
        
        with self.assertRaises(ValidationError):
            User(**incomplete_data)
    
    def test_user_serialization(self) -> None:
        """Test user serialization to dictionary."""
        user = User(**self.valid_user_data)
        serialized = user.to_dict()
        
        self.assertIsInstance(serialized, dict)
        self.assertEqual(serialized['username'], 'testuser')
        self.assertEqual(serialized['email'], 'test@example.com')
        self.assertIn('id', serialized)
        self.assertIn('created_at', serialized)
    
    def test_user_password_verification(self) -> None:
        """Test password verification."""
        user = User(**self.valid_user_data)
        
        # Test correct password
        self.assertTrue(user.verify_password('hashed_password_123'))
        
        # Test incorrect password
        self.assertFalse(user.verify_password('wrong_password'))
    
    def test_user_deactivation(self) -> None:
        """Test user deactivation."""
        user = User(**self.valid_user_data)
        user.deactivate()
        
        self.assertFalse(user.is_active)
    
    def tearDown(self) -> None:
        """Clean up after tests."""
        pass


class TestProductModel(unittest.TestCase):
    """Test cases for Product model."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.valid_product_data = {
            'id': 100,
            'name': 'Test Product',
            'description': 'A test product description',
            'price': 99.99,
            'stock_quantity': 50,
            'category': 'electronics',
            'created_at': datetime.now(),
            'is_available': True
        }
    
    def test_product_creation_valid_data(self) -> None:
        """Test product creation with valid data."""
        try:
            product = Product(**self.valid_product_data)
            self.assertEqual(product.name, 'Test Product')
            self.assertEqual(product.price, 99.99)
            self.assertEqual(product.stock_quantity, 50)
            self.assertTrue(product.is_available)
        except Exception as e:
            self.fail(f"Product creation failed with valid data: {e}")
    
    def test_product_creation_invalid_price(self) -> None:
        """Test product creation with invalid price."""
        invalid_data = self.valid_product_data.copy()
        invalid_data['price'] = -10.0
        
        with self.assertRaises(ValidationError):
            Product(**invalid_data)
    
    def test_product_creation_invalid_stock(self) -> None:
        """Test product creation with invalid stock quantity."""
        invalid_data = self.valid_product_data.copy()
        invalid_data['stock_quantity'] = -5
        
        with self.assertRaises(ValidationError):
            Product(**invalid_data)
    
    def test_product_update_stock(self) -> None:
        """Test updating product stock."""
        product = Product(**self.valid_product_data)
        
        # Test valid stock update
        product.update_stock(10)
        self.assertEqual(product.stock_quantity, 60)
        
        # Test invalid stock update (negative result)
        with self.assertRaises(ValidationError):
            product.update_stock(-100)
    
    def test_product_mark_unavailable(self) -> None:
        """Test marking product as unavailable."""
        product = Product(**self.valid_product_data)
        product.mark_unavailable()
        
        self.assertFalse(product.is_available)
        self.assertEqual(product.stock_quantity, 0)
    
    def test_product_calculate_discounted_price(self) -> None:
        """Test calculating discounted price."""
        product = Product(**self.valid_product_data)
        
        # Test 20% discount
        discounted_price = product.calculate_discounted_price(20)
        expected_price = 99.99 * 0.8
        self.assertAlmostEqual(discounted_price, expected_price, places=2)
        
        # Test invalid discount percentage
        with self.assertRaises(ValidationError):
            product.calculate_discounted_price(150)
    
    def tearDown(self) -> None:
        """Clean up after tests."""
        pass


class TestOrderModel(unittest.TestCase):
    """Test cases for Order model."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.user = User(
            id=1,
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password',
            created_at=datetime.now(),
            is_active=True
        )
        
        self.product = Product(
            id=100,
            name='Test Product',
            description='Test description',
            price=99.99,
            stock_quantity=50,
            category='electronics',
            created_at=datetime.now(),
            is_available=True
        )
        
        self.valid_order_data = {
            'id': 1000,
            'user_id': self.user.id,
            'order_date': datetime.now(),
            'status': 'pending',
            'total_amount': 199.98,
            'shipping_address': '123 Test St, Test City',
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 2,
                    'price_per_unit': self.product.price
                }
            ]
        }
    
    def test_order_creation_valid_data(self) -> None:
        """Test order creation with valid data."""
        try:
            order = Order(**self.valid_order_data)
            self.assertEqual(order.user_id, self.user.id)
            self.assertEqual(order.status, 'pending')
            self.assertEqual(order.total_amount, 199.98)
            self.assertEqual(len(order.items), 1)
        except Exception as e:
            self.fail(f"Order creation failed with valid data: {e}")
    
    def test_order_creation_invalid_status(self) -> None:
        """Test order creation with invalid status."""
        invalid_data = self.valid_order_data.copy()
        invalid_data['status'] = 'invalid_status'
        
        with self.assertRaises(ValidationError):
            Order(**invalid_data)
    
    def test_order_creation_negative_total(self) -> None:
        """Test order creation with negative total amount."""
        invalid_data = self.valid_order_data.copy()
        invalid_data['total_amount'] = -50.0
        
        with self.assertRaises(ValidationError):
            Order(**invalid_data)
    
    def test_order_update_status(self) -> None:
        """Test updating order status."""
        order = Order(**self.valid_order_data)
        
        # Test valid status update
        order.update_status('shipped')
        self.assertEqual(order.status, 'shipped')
        
        # Test invalid status update
        with self.assertRaises(ValidationError):
            order.update_status('invalid_status')
    
    def test_order_add_item(self) -> None:
        """Test adding item to order."""
        order = Order(**self.valid_order_data)
        
        new_item = {
            'product_id': 200,
            'quantity': 1,
            'price_per_unit': 49.99
        }
        
        order.add_item(new_item)
        self.assertEqual(len(order.items), 2)
        self.assertEqual(order.items[1]['product_id'], 200)
    
    def test_order_calculate_total(self) -> None:
        """Test calculating order total."""
        order = Order(**self.valid_order_data)
        
        # Add another item
        new_item = {
            'product_id': 200,
            'quantity': 1,
            'price_per_unit': 49.99
        }
        order.add_item(new_item)
        
        # Recalculate total
        order.calculate_total()
        expected_total = (2 * 99.99) + 49.99
        self.assertAlmostEqual(order.total_amount, expected_total, places=2)
    
    def test_order_cancel(self) -> None:
        """Test cancelling an order."""
        order = Order(**self.valid_order_data)
        order.cancel()
        
        self.assertEqual(order.status, 'cancelled')
    
    def test_order_cancel_already_shipped(self) -> None:
        """Test cancelling an already shipped order."""
        order = Order(**self.valid_order_data)
        order.update_status('shipped')
        
        with self.assertRaises(ValidationError):
            order.cancel()
    
    def tearDown(self) -> None:
        """Clean up after tests."""
        pass


class TestModelIntegration(unittest.TestCase):
    """Integration tests for models."""
    
    def test_user_product_order_integration(self) -> None:
        """Test integration between User, Product, and Order models."""
        try:
            # Create user
            user = User(
                id=1,
                username='integration_user',
                email='integration@example.com',
                password_hash='hashed_pass',
                created_at=datetime.now(),
                is_active=True
            )
            
            # Create product
            product = Product(
                id=500,
                name='Integration Product',
                description='Integration test product',
                price=75.50,
                stock_quantity=100,
                category='books',
                created_at=datetime.now(),
                is_available=True
            )
            
            # Create order
            order = Order(
                id=2000,
                user_id=user.id,
                order_date=datetime.now(),
                status='pending',
                total_amount=151.00,
                shipping_address='456 Integration Ave',
                items=[
                    {
                        'product_id': product.id,
                        'quantity': 2,
                        'price_per_unit': product.price
                    }
                ]
            )
            
            # Verify relationships
            self.assertEqual(order.user_id, user.id)
            self.assertEqual(order.items[0]['product_id'], product.id)
            
            # Update product stock based on order
            product.update_stock(-order.items[0]['quantity'])
            self.assertEqual(product.stock_quantity, 98)
            
            # Update order status
            order.update_status('processing')
            self.assertEqual(order.status, 'processing')
            
        except Exception as e:
            self.fail(f"Integration test failed: {e}")
    
    def test_error_handling_integration(self) -> None:
        """Test error handling across models."""
        # Test database error simulation
        with self.assertRaises(DatabaseError):
            # Simulate database operation failure
            raise DatabaseError("Connection to database failed")
        
        # Test not found error
        with self.assertRaises(NotFoundError):
            raise NotFoundError("User not found")
        
        # Test validation error chain
        try:
            invalid_product = Product(
                id=999,
                name='',
                description='',
                price=-10.0,
                stock_quantity=-5,
                category='',
                created_at=datetime.now(),
                is_available=True
            )
        except ValidationError as e:
            self.assertIsInstance(e, ValidationError)
            self.assertIn('validation', str(e).lower())


def run_tests() -> None:
    """Run all tests."""
    try:
        # Create test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add test classes
        suite.addTests(loader.loadTestsFromTestCase(TestUserModel))
        suite.addTests(loader.loadTestsFromTestCase(TestProductModel))
        suite.addTests(loader.loadTestsFromTestCase(TestOrderModel))
        suite.addTests(loader.loadTestsFromTestCase(TestModelIntegration))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Exit with appropriate code
        sys.exit(0 if result.wasSuccessful() else 1)
        
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)


if __name__ == '__main__':
    run_tests()