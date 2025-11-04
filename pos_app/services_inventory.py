"""
Service layer for inventory-related business logic
"""
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import logging

from .models import Inventory, InventoryTransfer, Product, Store, AuditLog

logger = logging.getLogger(__name__)


class InventoryService:
    """Handle inventory-related operations"""
    
    @transaction.atomic
    def adjust_inventory(self, product, store, quantity_change, user, reason="", ip_address=None):
        """
        Adjust inventory quantity
        
        Args:
            product: Product object
            store: Store object
            quantity_change: Positive or negative integer
            user: User making the adjustment
            reason: Reason for adjustment
            ip_address: IP address of the request
        """
        try:
            inventory, created = Inventory.objects.select_for_update().get_or_create(
                product=product,
                store=store,
                defaults={'quantity': 0}
            )
            
            old_quantity = inventory.quantity
            inventory.quantity += quantity_change
            
            if inventory.quantity < 0:
                raise ValueError("Inventory quantity cannot be negative")
            
            inventory.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='update',
                model_name='Inventory',
                object_id=str(inventory.id),
                description=f"Inventory adjusted from {old_quantity} to {inventory.quantity}. Reason: {reason}",
                ip_address=ip_address
            )
            
            # Check if low stock
            if inventory.is_low_stock():
                self._send_low_stock_alert(inventory)
            
            logger.info(f"Inventory adjusted: {product.name} at {store.name} by {quantity_change}")
            return inventory
            
        except Exception as e:
            logger.error(f"Failed to adjust inventory: {e}")
            raise
    
    @transaction.atomic
    def request_transfer(self, product, from_store, to_store, quantity, user, ip_address=None):
        """
        Request an inventory transfer between stores
        
        Args:
            product: Product object
            from_store: Source Store object
            to_store: Destination Store object
            quantity: Quantity to transfer
            user: User requesting the transfer
            ip_address: IP address of the request
            
        Returns:
            InventoryTransfer object
        """
        try:
            # Check if source has enough inventory
            inventory = Inventory.objects.get(product=product, store=from_store)
            if inventory.quantity < quantity:
                raise ValueError(f"Insufficient inventory. Available: {inventory.quantity}")
            
            # Create transfer request
            transfer = InventoryTransfer.objects.create(
                product=product,
                from_store=from_store,
                to_store=to_store,
                quantity=quantity,
                status='pending',
                requested_by=user
            )
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='transfer',
                model_name='InventoryTransfer',
                object_id=str(transfer.id),
                description=f"Transfer requested: {quantity} {product.name} from {from_store.name} to {to_store.name}",
                ip_address=ip_address
            )
            
            # Notify directors/admins
            self._notify_transfer_request(transfer)
            
            logger.info(f"Transfer requested: {transfer.id} by {user.username}")
            return transfer
            
        except Exception as e:
            logger.error(f"Failed to request transfer: {e}")
            raise
    
    @transaction.atomic
    def approve_transfer(self, transfer, user, ip_address=None):
        """
        Approve and execute an inventory transfer
        
        Args:
            transfer: InventoryTransfer object
            user: User approving the transfer
            ip_address: IP address of the request
        """
        try:
            if transfer.status != 'pending':
                raise ValueError("Transfer is not pending")
            
            # Update inventories
            from_inventory = Inventory.objects.select_for_update().get(
                product=transfer.product,
                store=transfer.from_store
            )
            
            if from_inventory.quantity < transfer.quantity:
                raise ValueError("Insufficient inventory at source store")
            
            from_inventory.quantity -= transfer.quantity
            from_inventory.save()
            
            to_inventory, created = Inventory.objects.select_for_update().get_or_create(
                product=transfer.product,
                store=transfer.to_store,
                defaults={'quantity': 0}
            )
            to_inventory.quantity += transfer.quantity
            to_inventory.save()
            
            # Update transfer
            transfer.status = 'approved'
            transfer.approved_by = user
            transfer.approval_date = timezone.now()
            transfer.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='approval',
                model_name='InventoryTransfer',
                object_id=str(transfer.id),
                description=f"Transfer approved: {transfer.quantity} {transfer.product.name} from {transfer.from_store.name} to {transfer.to_store.name}",
                ip_address=ip_address
            )
            
            logger.info(f"Transfer approved: {transfer.id} by {user.username}")
            
        except Exception as e:
            logger.error(f"Failed to approve transfer: {e}")
            raise
    
    @transaction.atomic
    def reject_transfer(self, transfer, user, reason="", ip_address=None):
        """
        Reject an inventory transfer request
        
        Args:
            transfer: InventoryTransfer object
            user: User rejecting the transfer
            reason: Reason for rejection
            ip_address: IP address of the request
        """
        try:
            if transfer.status != 'pending':
                raise ValueError("Transfer is not pending")
            
            transfer.status = 'rejected'
            transfer.approved_by = user
            transfer.approval_date = timezone.now()
            transfer.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='rejection',
                model_name='InventoryTransfer',
                object_id=str(transfer.id),
                description=f"Transfer rejected: {transfer.quantity} {transfer.product.name}. Reason: {reason}",
                ip_address=ip_address
            )
            
            logger.info(f"Transfer rejected: {transfer.id} by {user.username}")
            
        except Exception as e:
            logger.error(f"Failed to reject transfer: {e}")
            raise
    
    def get_low_stock_items(self, store=None):
        """Get all low stock items"""
        queryset = Inventory.objects.select_related('product', 'store').filter(
            quantity__lte=models.F('reorder_level')
        )
        
        if store:
            queryset = queryset.filter(store=store)
        
        return queryset
    
    @staticmethod
    def _send_low_stock_alert(inventory):
        """Send low stock alert email"""
        try:
            subject = f"Low Stock Alert: {inventory.product.name}"
            message = f"""
            Product: {inventory.product.name}
            Store: {inventory.store.name}
            Current Quantity: {inventory.quantity}
            Reorder Level: {inventory.reorder_level}
            
            Please restock this item soon.
            """
            
            admin_email = getattr(settings, 'ADMIN_EMAIL', None)
            if admin_email:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [admin_email],
                    fail_silently=True
                )
        except Exception as e:
            logger.error(f"Failed to send low stock alert: {e}")
    
    @staticmethod
    def _notify_transfer_request(transfer):
        """Notify directors/admins of transfer request"""
        try:
            from .models import User
            
            subject = f"Inventory Transfer Request: {transfer.product.name}"
            message = f"""
            A new inventory transfer has been requested:
            
            Product: {transfer.product.name}
            From: {transfer.from_store.name}
            To: {transfer.to_store.name}
            Quantity: {transfer.quantity}
            Requested by: {transfer.requested_by.username}
            
            Please review and approve/reject this request.
            """
            
            # Get director and admin emails
            recipients = User.objects.filter(
                role__in=['director', 'admin']
            ).values_list('email', flat=True)
            
            recipients = [email for email in recipients if email]
            
            if recipients:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    recipients,
                    fail_silently=True
                )
        except Exception as e:
            logger.error(f"Failed to send transfer notification: {e}")
