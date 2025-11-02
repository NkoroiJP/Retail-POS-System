from django.core.exceptions import PermissionDenied
from .models import User


def check_permission(user, required_role=None, required_roles=None, same_store=True):
    """
    Check if user has the required permissions
    
    Args:
        user: The user to check permissions for
        required_role: A single role that is required (e.g. 'manager')
        required_roles: A list of roles, user must have one of them
        same_store: Whether the user must have the same store as the target
    """
    if not user.is_authenticated:
        raise PermissionDenied("User not authenticated")
    
    user_role = user.role
    
    # Check if user has required role/roles
    if required_role and user_role != required_role:
        raise PermissionDenied(f"User must be {required_role}")
    
    if required_roles and user_role not in required_roles:
        raise PermissionDenied(f"User must be one of: {', '.join(required_roles)}")
    
    # Additional checks can be added here
    
    return True


def can_access_store(user, target_store):
    """
    Check if user can access a specific store
    """
    if user.role in ['director', 'admin']:
        return True  # Directors and admins can access all stores
    elif user.role == 'manager':
        return user.store == target_store  # Managers can only access their store
    elif user.role == 'staff':
        return user.store == target_store  # Staff can only access their store
    return False


def can_manage_inventory(user, store=None):
    """
    Check if user can manage inventory
    """
    if user.role in ['director', 'admin']:
        return True
    elif user.role == 'manager':
        # Managers can manage inventory only for their store
        if store:
            return user.store == store
        return user.store is not None
    return False


def can_view_reports(user, store=None):
    """
    Check if user can view reports
    """
    if user.role in ['director', 'admin']:
        return True  # Can view all reports
    elif user.role == 'manager':
        # Managers can view reports for their store
        if store:
            return user.store == store
        return user.store is not None
    return False


def can_process_sales(user, store=None):
    """
    Check if user can process sales
    """
    if user.role in ['director', 'admin', 'manager']:
        return True
    elif user.role == 'staff':
        # Staff can process sales for their store
        if store:
            return user.store == store
        return user.store is not None
    return False


def can_transfer_inventory(user, from_store, to_store):
    """
    Check if user can initiate inventory transfer
    """
    if user.role in ['director', 'admin']:
        return True
    elif user.role == 'manager':
        # Managers can only transfer from their store
        return user.store == from_store
    return False


def can_approve_transfers(user):
    """
    Check if user can approve transfers
    """
    return user.role in ['director', 'admin']