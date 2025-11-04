"""
Service layer for sales-related business logic
"""
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.conf import settings
import uuid
import logging

from .models import Transaction, TransactionItem, Inventory, AuditLog

logger = logging.getLogger(__name__)


class SalesService:
    """Handle sales transaction logic"""
    
    @staticmethod
    def calculate_vat(subtotal):
        """Calculate VAT amount"""
        vat_rate = getattr(settings, 'VAT_RATE', 16.00)
        return (subtotal * Decimal(str(vat_rate))) / Decimal('100')
    
    @staticmethod
    def calculate_commission(total, commission_rate):
        """Calculate commission amount"""
        return (total * Decimal(str(commission_rate))) / Decimal('100')
    
    @transaction.atomic
    def create_sale(self, user, store, items, ip_address=None):
        """
        Create a new sale transaction
        
        Args:
            user: User making the sale
            store: Store where sale is made
            items: List of dicts with 'product_id', 'quantity', 'price'
            ip_address: IP address of the request
            
        Returns:
            Transaction object or None if failed
        """
        try:
            # Calculate totals
            subtotal = Decimal('0')
            for item in items:
                subtotal += Decimal(str(item['price'])) * Decimal(str(item['quantity']))
            
            vat_amount = self.calculate_vat(subtotal)
            total_amount = subtotal + vat_amount
            commission = self.calculate_commission(total_amount, user.commission_rate)
            
            # Create transaction
            trans = Transaction.objects.create(
                transaction_id=self._generate_transaction_id(),
                user=user,
                store=store,
                transaction_type='sale',
                subtotal=subtotal,
                vat_amount=vat_amount,
                total_amount=total_amount,
                commission=commission
            )
            
            # Create transaction items and update inventory
            for item in items:
                TransactionItem.objects.create(
                    transaction=trans,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    unit_price=item['price'],
                    total_price=Decimal(str(item['price'])) * Decimal(str(item['quantity']))
                )
                
                # Update inventory
                inventory = Inventory.objects.select_for_update().get(
                    product_id=item['product_id'],
                    store=store
                )
                inventory.quantity -= item['quantity']
                inventory.save()
            
            # Update user commission
            user.total_commission += commission
            user.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='sale',
                model_name='Transaction',
                object_id=str(trans.id),
                description=f"Sale transaction {trans.transaction_id} for {total_amount}",
                ip_address=ip_address
            )
            
            logger.info(f"Sale created: {trans.transaction_id} by {user.username}")
            return trans
            
        except Exception as e:
            logger.error(f"Failed to create sale: {e}")
            raise
    
    @staticmethod
    def _generate_transaction_id():
        """Generate unique transaction ID"""
        return f"TXN-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    @transaction.atomic
    def process_return(self, original_transaction, user, items, ip_address=None):
        """
        Process a return transaction
        
        Args:
            original_transaction: Original Transaction object
            user: User processing the return
            items: List of dicts with 'product_id', 'quantity', 'price'
            ip_address: IP address of the request
            
        Returns:
            Transaction object or None if failed
        """
        try:
            # Calculate totals
            subtotal = Decimal('0')
            for item in items:
                subtotal += Decimal(str(item['price'])) * Decimal(str(item['quantity']))
            
            vat_amount = self.calculate_vat(subtotal)
            total_amount = subtotal + vat_amount
            
            # Create return transaction
            trans = Transaction.objects.create(
                transaction_id=self._generate_transaction_id(),
                user=user,
                store=original_transaction.store,
                transaction_type='return',
                subtotal=-subtotal,
                vat_amount=-vat_amount,
                total_amount=-total_amount,
                commission=Decimal('0')
            )
            
            # Create transaction items and update inventory
            for item in items:
                TransactionItem.objects.create(
                    transaction=trans,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    unit_price=item['price'],
                    total_price=Decimal(str(item['price'])) * Decimal(str(item['quantity']))
                )
                
                # Update inventory (add back)
                inventory = Inventory.objects.select_for_update().get(
                    product_id=item['product_id'],
                    store=original_transaction.store
                )
                inventory.quantity += item['quantity']
                inventory.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='sale',
                model_name='Transaction',
                object_id=str(trans.id),
                description=f"Return transaction {trans.transaction_id} for {total_amount}",
                ip_address=ip_address
            )
            
            logger.info(f"Return processed: {trans.transaction_id} by {user.username}")
            return trans
            
        except Exception as e:
            logger.error(f"Failed to process return: {e}")
            raise
