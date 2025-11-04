"""
Helper utilities for common operations
"""
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal


def get_date_range(period='today'):
    """
    Get start and end datetime for a given period
    
    Args:
        period: 'today', 'yesterday', 'week', 'month', 'year', or custom
        
    Returns:
        tuple: (start_datetime, end_datetime)
    """
    now = timezone.now()
    
    if period == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == 'yesterday':
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif period == 'week':
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == 'month':
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == 'year':
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    else:
        # Default to today
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    
    return start, end


def calculate_percentage_change(current, previous):
    """Calculate percentage change between two values"""
    if previous == 0:
        return 100 if current > 0 else 0
    
    return ((current - previous) / previous) * 100


def format_currency(amount, currency='KES'):
    """Format amount as currency"""
    try:
        amount = Decimal(str(amount))
        return f"{currency} {amount:,.2f}"
    except:
        return f"{currency} 0.00"


def paginate_queryset(queryset, page_number, per_page=20):
    """
    Paginate a queryset
    
    Args:
        queryset: Django queryset
        page_number: Current page number (1-indexed)
        per_page: Items per page
        
    Returns:
        dict with 'items', 'page', 'pages', 'total'
    """
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    paginator = Paginator(queryset, per_page)
    
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    
    return {
        'items': page.object_list,
        'page': page.number,
        'pages': paginator.num_pages,
        'total': paginator.count,
        'has_next': page.has_next(),
        'has_previous': page.has_previous(),
    }


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def export_to_csv(queryset, fields, filename='export.csv'):
    """
    Export queryset to CSV
    
    Args:
        queryset: Django queryset
        fields: List of field names to include
        filename: Name of CSV file
        
    Returns:
        HttpResponse with CSV data
    """
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow(fields)
    
    # Write data rows
    for obj in queryset:
        row = []
        for field in fields:
            # Handle nested attributes (e.g., 'store.name')
            value = obj
            for attr in field.split('.'):
                value = getattr(value, attr, '')
                if value is None:
                    value = ''
            row.append(value)
        writer.writerow(row)
    
    return response


def generate_report_data(transactions, group_by='day'):
    """
    Generate aggregated report data from transactions
    
    Args:
        transactions: Transaction queryset
        group_by: 'day', 'week', 'month'
        
    Returns:
        List of dicts with aggregated data
    """
    if group_by == 'day':
        trunc = 'day'
    elif group_by == 'week':
        trunc = 'week'
    elif group_by == 'month':
        trunc = 'month'
    else:
        trunc = 'day'
    
    from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
    
    trunc_class = {
        'day': TruncDay,
        'week': TruncWeek,
        'month': TruncMonth,
    }[trunc]
    
    data = transactions.annotate(
        period=trunc_class('created_at')
    ).values('period').annotate(
        total_sales=Sum('total_amount'),
        transaction_count=Count('id')
    ).order_by('period')
    
    return list(data)


class cached_property:
    """Decorator for cached property (for older Django versions)"""
    def __init__(self, func):
        self.func = func
        
    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = self.func(instance)
        setattr(instance, self.func.__name__, value)
        return value
