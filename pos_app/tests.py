from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client
from decimal import Decimal
from .models import Store, Category, Product, Inventory, Transaction, TransactionItem, InventoryTransfer

User = get_user_model()


class PosSystemTestCase(TestCase):
    def setUp(self):
        # Create test stores
        self.store1 = Store.objects.create(
            name='Test Store 1',
            address='123 Test Street',
            phone='+1234567890',
            email='test1@store.com'
        )
        
        self.store2 = Store.objects.create(
            name='Test Store 2',
            address='456 Test Avenue',
            phone='+1987654321',
            email='test2@store.com'
        )
        
        # Create test categories
        self.category1 = Category.objects.create(name='Electronics', description='Electronic devices')
        self.category2 = Category.objects.create(name='Clothing', description='Clothing items')
        
        # Create test products
        self.product1 = Product.objects.create(
            name='Test Smartphone',
            description='Test smartphone product',
            category=self.category1,
            price=Decimal('599.99')
        )
        
        self.product2 = Product.objects.create(
            name='Test T-Shirt',
            description='Test t-shirt product',
            category=self.category2,
            price=Decimal('19.99')
        )
        
        # Create test users
        self.director = User.objects.create_user(
            username='test_director',
            password='testpass123',
            role='director'
        )
        
        self.admin = User.objects.create_user(
            username='test_admin',
            password='testpass123',
            role='admin'
        )
        
        self.manager = User.objects.create_user(
            username='test_manager',
            password='testpass123',
            role='manager',
            store=self.store1
        )
        
        self.staff = User.objects.create_user(
            username='test_staff',
            password='testpass123',
            role='staff',
            store=self.store1
        )
        
        # Create initial inventory
        self.inventory1 = Inventory.objects.create(
            product=self.product1,
            store=self.store1,
            quantity=10,
            reorder_level=5
        )
        
        self.inventory2 = Inventory.objects.create(
            product=self.product2,
            store=self.store1,
            quantity=50,
            reorder_level=10
        )
        
        # Create a test client
        self.client = Client()

    def test_user_creation(self):
        """Test that users are created with correct roles and attributes"""
        self.assertEqual(self.director.role, 'director')
        self.assertEqual(self.admin.role, 'admin')
        self.assertEqual(self.manager.role, 'manager')
        self.assertEqual(self.staff.role, 'staff')
        self.assertEqual(self.manager.store, self.store1)

    def test_product_creation(self):
        """Test that products are created correctly"""
        self.assertEqual(self.product1.name, 'Test Smartphone')
        self.assertEqual(self.product1.category, self.category1)
        self.assertEqual(self.product1.price, Decimal('599.99'))

    def test_store_creation(self):
        """Test that stores are created correctly"""
        self.assertEqual(self.store1.name, 'Test Store 1')
        self.assertEqual(self.store1.email, 'test1@store.com')

    def test_inventory_creation(self):
        """Test that inventory items are created correctly"""
        self.assertEqual(self.inventory1.product, self.product1)
        self.assertEqual(self.inventory1.store, self.store1)
        self.assertEqual(self.inventory1.quantity, 10)

    def test_director_login(self):
        """Test director can log in"""
        login_successful = self.client.login(username='test_director', password='testpass123')
        self.assertTrue(login_successful)

    def test_manager_login(self):
        """Test manager can log in"""
        login_successful = self.client.login(username='test_manager', password='testpass123')
        self.assertTrue(login_successful)

    def test_staff_login(self):
        """Test staff can log in"""
        login_successful = self.client.login(username='test_staff', password='testpass123')
        self.assertTrue(login_successful)

    def test_inventory_transfer_creation(self):
        """Test creating an inventory transfer"""
        transfer = InventoryTransfer.objects.create(
            product=self.product1,
            from_store=self.store1,
            to_store=self.store2,
            quantity=5,
            requested_by=self.manager
        )
        
        self.assertEqual(transfer.product, self.product1)
        self.assertEqual(transfer.from_store, self.store1)
        self.assertEqual(transfer.to_store, self.store2)
        self.assertEqual(transfer.quantity, 5)
        self.assertEqual(transfer.requested_by, self.manager)
        self.assertEqual(transfer.status, 'pending')

    def test_transaction_creation(self):
        """Test creating a transaction"""
        transaction = Transaction.objects.create(
            transaction_id='TEST001',
            user=self.staff,
            store=self.store1,
            total_amount=Decimal('599.99'),
            commission=Decimal('29.99')
        )
        
        self.assertEqual(transaction.transaction_id, 'TEST001')
        self.assertEqual(transaction.user, self.staff)
        self.assertEqual(transaction.store, self.store1)
        self.assertEqual(transaction.total_amount, Decimal('599.99'))
        self.assertEqual(transaction.commission, Decimal('29.99'))

    def test_transaction_item_creation(self):
        """Test creating a transaction item"""
        transaction = Transaction.objects.create(
            transaction_id='TEST002',
            user=self.staff,
            store=self.store1,
            total_amount=Decimal('19.99'),
            commission=Decimal('0.99')
        )
        
        item = TransactionItem.objects.create(
            transaction=transaction,
            product=self.product2,
            quantity=1,
            unit_price=Decimal('19.99'),
            total_price=Decimal('19.99')
        )
        
        self.assertEqual(item.transaction, transaction)
        self.assertEqual(item.product, self.product2)
        self.assertEqual(item.quantity, 1)
        self.assertEqual(item.total_price, Decimal('19.99'))

    def test_inventory_levels(self):
        """Test inventory level thresholds"""
        # Initially, inventory1 has 10 items with reorder level of 5 (not low)
        self.assertLess(self.inventory1.reorder_level, self.inventory1.quantity)
        
        # Update inventory to be low
        self.inventory1.quantity = 3
        self.inventory1.save()
        
        # Now it should be below reorder level
        self.assertLess(self.inventory1.quantity, self.inventory1.reorder_level)


class ViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create a test store
        self.store = Store.objects.create(
            name='Test Store',
            address='123 Test Street',
            phone='+1234567890',
            email='test@store.com'
        )
        
        # Create a test manager
        self.manager = User.objects.create_user(
            username='test_manager',
            password='testpass123',
            role='manager',
            store=self.store
        )
        
        # Create test category and product
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            description='Test product description',
            category=self.category,
            price=Decimal('19.99')
        )
        
        # Create inventory for the product
        Inventory.objects.create(
            product=self.product,
            store=self.store,
            quantity=10,
            reorder_level=5
        )

    def test_login_view_get(self):
        """Test that login page loads"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')

    def test_dashboard_access(self):
        """Test that authenticated users can access dashboard"""
        self.client.login(username='test_manager', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_inventory_access(self):
        """Test that manager can access inventory page"""
        self.client.login(username='test_manager', password='testpass123')
        response = self.client.get(reverse('inventory'))
        self.assertEqual(response.status_code, 200)

    def test_pos_access(self):
        """Test that staff can access POS page"""
        staff = User.objects.create_user(
            username='test_staff',
            password='testpass123',
            role='staff',
            store=self.store
        )
        
        self.client.login(username='test_staff', password='testpass123')
        response = self.client.get(reverse('pos'))
        self.assertEqual(response.status_code, 200)

    def test_sales_report_access(self):
        """Test that manager can access sales report"""
        self.client.login(username='test_manager', password='testpass123')
        response = self.client.get(reverse('sales_report'))
        self.assertEqual(response.status_code, 200)