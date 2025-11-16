from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class User(AbstractUser):
    USER_ROLE_CHOICES = [
        ('director', 'Director'),
        ('admin', 'System Admin'),
        ('manager', 'Store Manager'),
        ('staff', 'Shop Attendant'),
        ('technician', 'Technician'),
    ]
    
    role = models.CharField(max_length=20, choices=USER_ROLE_CHOICES, default='staff')
    store = models.ForeignKey('Store', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('5.00'))  # 5% default commission
    total_commission = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Store(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    tax_id = models.CharField(max_length=50, blank=True, null=True, help_text="VAT/TIN number")
    website = models.URLField(blank=True, null=True)
    return_policy_days = models.IntegerField(default=7, help_text="Number of days for returns")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="Stock Keeping Unit")
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    photo = models.ImageField(upload_to='product_photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_items')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'store')
        indexes = [
            models.Index(fields=['store', 'quantity']),
            models.Index(fields=['product', 'store']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.store.name}"
    
    def is_low_stock(self):
        """Check if inventory is below reorder level"""
        return self.quantity <= self.reorder_level


class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('sale', 'Sale'),
        ('return', 'Return'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('mobile', 'Mobile Payment'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    transaction_id = models.CharField(max_length=50, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES, default='sale')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    card_last_four = models.CharField(max_length=4, blank=True, null=True, help_text="Last 4 digits of card")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['-created_at', 'store']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.transaction_id} - {self.total_amount}"


class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"


class InventoryTransfer(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    from_store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='transfers_out')
    to_store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='transfers_in')
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transfers_requested')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers_approved')
    request_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Transfer {self.product.name} from {self.from_store.name} to {self.to_store.name}"


class AuditLog(models.Model):
    """Model to track important system actions"""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('sale', 'Sale'),
        ('transfer', 'Inventory Transfer'),
        ('approval', 'Approval'),
        ('rejection', 'Rejection'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'user']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"


class Repair(models.Model):
    """Model for tracking phone and device repairs"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    REPAIR_TYPE_CHOICES = [
        ('screen', 'Screen Replacement'),
        ('battery', 'Battery Replacement'),
        ('motherboard', 'Motherboard Repair'),
        ('charging_port', 'Charging Port'),
        ('camera', 'Camera Repair'),
        ('speaker', 'Speaker Repair'),
        ('water_damage', 'Water Damage'),
        ('software', 'Software Issue'),
        ('other', 'Other'),
    ]
    
    repair_id = models.CharField(max_length=50, unique=True, db_index=True)
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=20)
    device_type = models.CharField(max_length=100)  # e.g., "iPhone 12", "Samsung Galaxy S21"
    device_imei = models.CharField(max_length=50, blank=True)
    repair_type = models.CharField(max_length=50, choices=REPAIR_TYPE_CHOICES)
    issue_description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Financial fields
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    labour_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Tracking fields
    technician = models.ForeignKey(User, on_delete=models.CASCADE, related_name='repairs')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='repairs')
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Additional notes
    technician_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at', 'store']),
            models.Index(fields=['technician', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.repair_id} - {self.customer_name} - {self.device_type}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate total cost
        self.total_cost = self.parts_cost + self.labour_charge
        super().save(*args, **kwargs)


class RepairItem(models.Model):
    """Model for parts/products used in repairs"""
    repair = models.ForeignKey(Repair, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name} for {self.repair.repair_id}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate total price
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)