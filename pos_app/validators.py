"""
Validators for input data
"""
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError


def validate_positive_decimal(value, field_name="Value"):
    """Validate that a value is a positive decimal"""
    try:
        decimal_value = Decimal(str(value))
        if decimal_value <= 0:
            raise ValidationError(f"{field_name} must be positive")
        return decimal_value
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid number")


def validate_positive_integer(value, field_name="Value"):
    """Validate that a value is a positive integer"""
    try:
        int_value = int(value)
        if int_value <= 0:
            raise ValidationError(f"{field_name} must be positive")
        return int_value
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid integer")


def validate_phone_number(phone):
    """Validate Kenyan phone number format"""
    if not phone:
        raise ValidationError("Phone number is required")
    
    # Remove common prefixes and spaces
    phone = phone.replace('+', '').replace(' ', '').replace('-', '')
    
    # Kenyan numbers: 254XXXXXXXXX or 07XXXXXXXX or 7XXXXXXXX
    if phone.startswith('254'):
        if len(phone) != 12:
            raise ValidationError("Invalid phone number format. Expected: 254XXXXXXXXX")
    elif phone.startswith('0'):
        if len(phone) != 10:
            raise ValidationError("Invalid phone number format. Expected: 07XXXXXXXX")
        phone = '254' + phone[1:]
    elif phone.startswith('7'):
        if len(phone) != 9:
            raise ValidationError("Invalid phone number format. Expected: 7XXXXXXXX")
        phone = '254' + phone
    else:
        raise ValidationError("Invalid phone number format")
    
    if not phone.isdigit():
        raise ValidationError("Phone number must contain only digits")
    
    return phone


def validate_sale_items(items):
    """Validate sale items data structure"""
    if not items or not isinstance(items, list):
        raise ValidationError("Items must be a non-empty list")
    
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValidationError(f"Item {idx} must be a dictionary")
        
        required_fields = ['product_id', 'quantity', 'price']
        for field in required_fields:
            if field not in item:
                raise ValidationError(f"Item {idx} missing required field: {field}")
        
        # Validate types
        validate_positive_integer(item['product_id'], f"Item {idx} product_id")
        validate_positive_integer(item['quantity'], f"Item {idx} quantity")
        validate_positive_decimal(item['price'], f"Item {idx} price")
    
    return items


def validate_email_list(emails):
    """Validate a comma-separated list of emails"""
    from django.core.validators import validate_email
    
    if not emails:
        return []
    
    email_list = [email.strip() for email in emails.split(',')]
    for email in email_list:
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError(f"Invalid email address: {email}")
    
    return email_list
