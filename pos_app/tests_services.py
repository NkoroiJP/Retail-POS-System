"""
Additional comprehensive tests for services, validators, and utilities
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.core.exceptions import ValidationError

from .models import Store, Category, Product, Inventory, AuditLog
from .services_sales import SalesService
from .services_inventory import InventoryService
from .validators import (
    validate_phone_number,
    validate_positive_decimal,
    validate_positive_integer,
    validate_sale_items
)
from .helpers import (
    get_date_range,
    calculate_percentage_change,
    format_currency,
    get_client_ip
)

User = get_user_model()


class SalesServiceTestCase(TestCase):
    """Comprehensive tests for SalesService"""
    
    def setUp(self):
        self.store = Store.objects.create(
            name="Test Store",
            address="123 Test St",
            phone="0712345678",
            email="test@store.com"
        )
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            role="staff",
            store=self.store,
            commission_rate=Decimal('5.00')
        )
        self.category = Category.objects.create(name="Test Category")
        self.product1 = Product.objects.create(
            name="Product 1",
            category=self.category,
            price=Decimal('100.00')
        )
        self.product2 = Product.objects.create(
            name="Product 2",
            category=self.category,
            price=Decimal('50.00')
        )
        Inventory.objects.create(
            product=self.product1,
            store=self.store,
            quantity=100
        )
        Inventory.objects.create(
            product=self.product2,
            store=self.store,
            quantity=50
        )
        self.service = SalesService()
    
    def test_vat_calculation(self):
        """Test VAT calculation is accurate"""
        subtotal = Decimal('1000.00')
        vat = self.service.calculate_vat(subtotal)
        self.assertEqual(vat, Decimal('160.00'))
    
    def test_commission_calculation(self):
        """Test commission calculation"""
        total = Decimal('1160.00')
        commission = self.service.calculate_commission(total, Decimal('5.00'))
        self.assertEqual(commission, Decimal('58.00'))
    
    def test_create_sale_single_item(self):
        """Test creating sale with single item"""
        items = [
            {'product_id': self.product1.id, 'quantity': 2, 'price': '100.00'}
        ]
        
        transaction = self.service.create_sale(
            user=self.user,
            store=self.store,
            items=items,
            ip_address='127.0.0.1'
        )
        
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.subtotal, Decimal('200.00'))
        self.assertEqual(transaction.vat_amount, Decimal('32.00'))
        self.assertEqual(transaction.total_amount, Decimal('232.00'))
        self.assertEqual(transaction.items.count(), 1)
        
        # Verify inventory decreased
        inventory = Inventory.objects.get(product=self.product1, store=self.store)
        self.assertEqual(inventory.quantity, 98)
        
        # Verify audit log created
        audit_logs = AuditLog.objects.filter(action='sale', user=self.user)
        self.assertEqual(audit_logs.count(), 1)
    
    def test_create_sale_multiple_items(self):
        """Test creating sale with multiple items"""
        items = [
            {'product_id': self.product1.id, 'quantity': 3, 'price': '100.00'},
            {'product_id': self.product2.id, 'quantity': 5, 'price': '50.00'}
        ]
        
        transaction = self.service.create_sale(
            user=self.user,
            store=self.store,
            items=items
        )
        
        self.assertEqual(transaction.subtotal, Decimal('550.00'))
        self.assertEqual(transaction.items.count(), 2)
        
        # Verify both inventories decreased
        inv1 = Inventory.objects.get(product=self.product1, store=self.store)
        inv2 = Inventory.objects.get(product=self.product2, store=self.store)
        self.assertEqual(inv1.quantity, 97)
        self.assertEqual(inv2.quantity, 45)
    
    def test_create_sale_updates_commission(self):
        """Test that sale updates user commission"""
        initial_commission = self.user.total_commission
        
        items = [
            {'product_id': self.product1.id, 'quantity': 1, 'price': '100.00'}
        ]
        
        self.service.create_sale(
            user=self.user,
            store=self.store,
            items=items
        )
        
        self.user.refresh_from_db()
        self.assertGreater(self.user.total_commission, initial_commission)


class InventoryServiceTestCase(TestCase):
    """Comprehensive tests for InventoryService"""
    
    def setUp(self):
        self.store1 = Store.objects.create(
            name="Store 1",
            address="123 Test St",
            phone="0712345678",
            email="store1@test.com"
        )
        self.store2 = Store.objects.create(
            name="Store 2",
            address="456 Test Ave",
            phone="0723456789",
            email="store2@test.com"
        )
        self.manager = User.objects.create_user(
            username="manager",
            password="testpass123",
            role="manager",
            store=self.store1
        )
        self.director = User.objects.create_user(
            username="director",
            password="testpass123",
            role="director"
        )
        self.category = Category.objects.create(name="Test Category")
        self.product = Product.objects.create(
            name="Test Product",
            category=self.category,
            price=Decimal('100.00')
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            store=self.store1,
            quantity=100,
            reorder_level=20
        )
        self.service = InventoryService()
    
    def test_adjust_inventory_increase(self):
        """Test increasing inventory"""
        self.service.adjust_inventory(
            product=self.product,
            store=self.store1,
            quantity_change=50,
            user=self.manager,
            reason="Restock"
        )
        
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 150)
    
    def test_adjust_inventory_decrease(self):
        """Test decreasing inventory"""
        self.service.adjust_inventory(
            product=self.product,
            store=self.store1,
            quantity_change=-30,
            user=self.manager,
            reason="Damage"
        )
        
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 70)
    
    def test_adjust_inventory_negative_error(self):
        """Test that inventory cannot go negative"""
        with self.assertRaises(ValueError):
            self.service.adjust_inventory(
                product=self.product,
                store=self.store1,
                quantity_change=-150,
                user=self.manager
            )
    
    def test_request_transfer_creates_pending(self):
        """Test transfer request creates pending transfer"""
        transfer = self.service.request_transfer(
            product=self.product,
            from_store=self.store1,
            to_store=self.store2,
            quantity=30,
            user=self.manager
        )
        
        self.assertEqual(transfer.status, 'pending')
        self.assertEqual(transfer.quantity, 30)
        self.assertEqual(transfer.requested_by, self.manager)
    
    def test_request_transfer_insufficient_inventory(self):
        """Test transfer fails with insufficient inventory"""
        with self.assertRaises(ValueError):
            self.service.request_transfer(
                product=self.product,
                from_store=self.store1,
                to_store=self.store2,
                quantity=200,
                user=self.manager
            )
    
    def test_approve_transfer_updates_inventories(self):
        """Test approving transfer updates both stores"""
        from .models import InventoryTransfer
        
        transfer = InventoryTransfer.objects.create(
            product=self.product,
            from_store=self.store1,
            to_store=self.store2,
            quantity=40,
            status='pending',
            requested_by=self.manager
        )
        
        self.service.approve_transfer(transfer, self.director)
        
        # Check source inventory decreased
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 60)
        
        # Check destination inventory increased
        inv2 = Inventory.objects.get(product=self.product, store=self.store2)
        self.assertEqual(inv2.quantity, 40)
        
        # Check transfer status
        transfer.refresh_from_db()
        self.assertEqual(transfer.status, 'approved')


class ValidatorTestCase(TestCase):
    """Test input validators"""
    
    def test_validate_phone_number_formats(self):
        """Test various phone number formats"""
        # Valid formats
        self.assertEqual(validate_phone_number('254712345678'), '254712345678')
        self.assertEqual(validate_phone_number('0712345678'), '254712345678')
        self.assertEqual(validate_phone_number('712345678'), '254712345678')
        self.assertEqual(validate_phone_number('+254 712 345 678'), '254712345678')
    
    def test_validate_phone_number_invalid(self):
        """Test invalid phone numbers"""
        invalid_numbers = ['123', '999999999999', 'abcd', '']
        
        for number in invalid_numbers:
            with self.assertRaises(ValidationError):
                validate_phone_number(number)
    
    def test_validate_positive_decimal(self):
        """Test positive decimal validation"""
        self.assertEqual(validate_positive_decimal('10.50'), Decimal('10.50'))
        self.assertEqual(validate_positive_decimal(100), Decimal('100'))
        self.assertEqual(validate_positive_decimal('0.01'), Decimal('0.01'))
    
    def test_validate_positive_decimal_invalid(self):
        """Test invalid positive decimals"""
        invalid_values = ['-10', '0', '-0.01', 'abc']
        
        for value in invalid_values:
            with self.assertRaises(ValidationError):
                validate_positive_decimal(value)
    
    def test_validate_positive_integer(self):
        """Test positive integer validation"""
        self.assertEqual(validate_positive_integer('10'), 10)
        self.assertEqual(validate_positive_integer(100), 100)
    
    def test_validate_positive_integer_invalid(self):
        """Test invalid positive integers"""
        invalid_values = ['-10', '0', 'abc', '10.5']
        
        for value in invalid_values:
            with self.assertRaises(ValidationError):
                validate_positive_integer(value)
    
    def test_validate_sale_items(self):
        """Test sale items validation"""
        valid_items = [
            {'product_id': 1, 'quantity': 5, 'price': '10.00'},
            {'product_id': 2, 'quantity': 3, 'price': '20.00'}
        ]
        
        result = validate_sale_items(valid_items)
        self.assertEqual(len(result), 2)
    
    def test_validate_sale_items_invalid(self):
        """Test invalid sale items"""
        # Empty list
        with self.assertRaises(ValidationError):
            validate_sale_items([])
        
        # Missing fields
        with self.assertRaises(ValidationError):
            validate_sale_items([{'product_id': 1}])
        
        # Invalid quantity
        with self.assertRaises(ValidationError):
            validate_sale_items([
                {'product_id': 1, 'quantity': -5, 'price': '10.00'}
            ])


class HelperTestCase(TestCase):
    """Test helper utilities"""
    
    def test_calculate_percentage_change(self):
        """Test percentage change calculation"""
        # Increase
        self.assertEqual(calculate_percentage_change(150, 100), 50.0)
        
        # Decrease
        self.assertEqual(calculate_percentage_change(80, 100), -20.0)
        
        # No change
        self.assertEqual(calculate_percentage_change(100, 100), 0.0)
        
        # From zero
        self.assertEqual(calculate_percentage_change(100, 0), 100)
    
    def test_format_currency(self):
        """Test currency formatting"""
        self.assertEqual(format_currency(1000), 'KES 1,000.00')
        self.assertEqual(format_currency(1000.50), 'KES 1,000.50')
        self.assertEqual(format_currency('1234.567'), 'KES 1,234.57')
    
    def test_get_date_range(self):
        """Test date range generation"""
        from django.utils import timezone
        
        # Today
        start, end = get_date_range('today')
        self.assertEqual(start.hour, 0)
        self.assertEqual(start.minute, 0)
        self.assertLessEqual(start, end)
        
        # Week
        start, end = get_date_range('week')
        self.assertEqual(start.weekday(), 0)  # Monday
        
        # Month
        start, end = get_date_range('month')
        self.assertEqual(start.day, 1)


class AuditLogTestCase(TestCase):
    """Test audit logging"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            role="staff"
        )
    
    def test_create_audit_log(self):
        """Test creating audit log entry"""
        log = AuditLog.objects.create(
            user=self.user,
            action='login',
            description="User logged in",
            ip_address='127.0.0.1'
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'login')
        self.assertIsNotNone(log.timestamp)
    
    def test_audit_log_ordering(self):
        """Test audit logs are ordered by timestamp"""
        log1 = AuditLog.objects.create(
            user=self.user,
            action='login',
            description="Login 1"
        )
        log2 = AuditLog.objects.create(
            user=self.user,
            action='sale',
            description="Sale 1"
        )
        
        logs = AuditLog.objects.all()
        self.assertEqual(logs[0], log2)  # Most recent first
        self.assertEqual(logs[1], log1)
