from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LogoutView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from .models import User, Store, Category, Product, Inventory, Transaction, TransactionItem, InventoryTransfer
from .utils import (can_manage_inventory, can_view_reports, can_process_sales, 
                   can_transfer_inventory, can_approve_transfers)
import uuid


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    
    return render(request, 'pos_app/login.html')


class CustomLogoutView(LogoutView):
    next_page = 'login'


@login_required
def dashboard(request):
    user = request.user
    
    # For Director/Admin - show overall stats
    if user.role in ['director', 'admin']:
        total_stores = Store.objects.count()
        total_products = Product.objects.count()
        total_transactions = Transaction.objects.count()
        total_sales = Transaction.objects.filter(transaction_type='sale').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # Sales by store
        sales_by_store = Transaction.objects.filter(
            transaction_type='sale'
        ).values('store__name').annotate(
            total_sales=Sum('total_amount'),
            transaction_count=Count('id')
        )
        
        context = {
            'user': user,
            'total_stores': total_stores,
            'total_products': total_products,
            'total_transactions': total_transactions,
            'total_sales': total_sales,
            'sales_by_store': sales_by_store,
        }
        return render(request, 'pos_app/admin_dashboard.html', context)
    
    # For Manager - show stats for their store
    elif user.role == 'manager' and user.store:
        store = user.store
        total_products = Inventory.objects.filter(store=store).count()
        total_transactions = Transaction.objects.filter(store=store).count()
        total_sales = Transaction.objects.filter(
            store=store, 
            transaction_type='sale'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Recent transactions for the store
        recent_transactions = Transaction.objects.filter(
            store=store
        ).order_by('-created_at')[:10]
        
        context = {
            'user': user,
            'store': store,
            'total_products': total_products,
            'total_transactions': total_transactions,
            'total_sales': total_sales,
            'recent_transactions': recent_transactions,
        }
        return render(request, 'pos_app/manager_dashboard.html', context)
    
    # For Staff - redirect to POS
    elif user.role == 'staff':
        return redirect('pos')
    
    # Default fallback
    return render(request, 'pos_app/dashboard.html', {'user': user})


@login_required
def pos_view(request):
    if not can_process_sales(request.user):
        messages.error(request, 'You do not have permission to access the POS.')
        return redirect('dashboard')
    
    products = Product.objects.all()
    categories = Product.objects.values_list('category__name', flat=True).distinct()
    
    context = {
        'products': products,
        'categories': categories,
        'user': request.user,
    }
    return render(request, 'pos_app/pos.html', context)


@login_required
@csrf_exempt
def process_sale(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    try:
        # Extract data from request
        product_ids = request.POST.getlist('product_ids[]')
        quantities = request.POST.getlist('quantities[]')
        
        if not product_ids or not quantities:
            return JsonResponse({'error': 'No products selected'}, status=400)
        
        if len(product_ids) != len(quantities):
            return JsonResponse({'error': 'Mismatched products and quantities'}, status=400)
        
        # Create a new transaction
        transaction_id = str(uuid.uuid4())
        user = request.user
        store = user.store if user.store else Store.objects.first()
        
        if not store:
            return JsonResponse({'error': 'No store assigned to user'}, status=400)
        
        total_amount = Decimal('0.00')
        transaction_items = []
        
        # Process each item in the cart
        for product_id, quantity in zip(product_ids, quantities):
            try:
                product = Product.objects.get(id=product_id)
                quantity = int(quantity)
                
                if quantity <= 0:
                    return JsonResponse({'error': f'Invalid quantity for {product.name}'}, status=400)
                
                # Check inventory
                inventory = Inventory.objects.get(product=product, store=store)
                if inventory.quantity < quantity:
                    return JsonResponse({
                        'error': f'Insufficient inventory for {product.name}. Available: {inventory.quantity}'
                    }, status=400)
                
                # Calculate subtotal
                item_subtotal = product.price * quantity
                total_amount += item_subtotal
                
                # Create transaction item
                transaction_items.append({
                    'product': product,
                    'quantity': quantity,
                    'unit_price': product.price,
                    'total_price': item_subtotal
                })
                
                # Update inventory
                inventory.quantity -= quantity
                inventory.save()
                
            except Product.DoesNotExist:
                return JsonResponse({'error': f'Product with ID {product_id} does not exist'}, status=400)
            except Inventory.DoesNotExist:
                return JsonResponse({'error': f'Inventory for product {product_id} does not exist at store {store.name}'}, status=400)
            except ValueError:
                return JsonResponse({'error': f'Invalid quantity value: {quantity}'}, status=400)
        
        # Calculate VAT (16% of subtotal)
        vat_rate = Decimal('0.16')
        vat_amount = total_amount * vat_rate
        
        # Calculate total amount (subtotal + VAT)
        total_amount_with_vat = total_amount + vat_amount
        
        # Calculate commission (5% of total sales for the user)
        commission = total_amount_with_vat * (user.commission_rate / 100)
        
        # Create transaction
        transaction = Transaction.objects.create(
            transaction_id=transaction_id,
            user=user,
            store=store,
            total_amount=total_amount_with_vat,
            commission=commission,
            vat_amount=vat_amount,
            subtotal=total_amount
        )
        
        # Create transaction items
        for item_data in transaction_items:
            TransactionItem.objects.create(
                transaction=transaction,
                product=item_data['product'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['total_price']
            )
        
        # Update user's total commission
        user.total_commission = user.total_commission + commission
        user.save(update_fields=['total_commission'])
        
        return JsonResponse({
            'success': True,
            'transaction_id': transaction_id,
            'subtotal': float(total_amount),
            'vat_amount': float(vat_amount),
            'total_amount': float(total_amount_with_vat),
            'commission': float(commission)
        })
    
    except Exception as e:
        print(f"ERROR in process_sale: {str(e)}")
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)


@login_required
def add_inventory(request):
    if request.method == 'POST':
        # Check permissions
        if request.user.role not in ['manager', 'director', 'admin']:
            messages.error(request, 'You do not have permission to add inventory.')
            return redirect('dashboard')
        
        try:
            product_id = request.POST.get('product_id')
            store_id = request.POST.get('store_id')
            quantity = int(request.POST.get('quantity', 0))
            reorder_level = int(request.POST.get('reorder_level', 10))
            
            # Managers can only add to their store
            if request.user.role == 'manager':
                if str(store_id) != str(request.user.store.id):
                    messages.error(request, 'You can only add inventory to your own store.')
                    return redirect('add_inventory')
            
            product = Product.objects.get(id=product_id)
            store = Store.objects.get(id=store_id)
            
            # Get or create inventory item
            inventory, created = Inventory.objects.get_or_create(
                product=product,
                store=store,
                defaults={'quantity': 0, 'reorder_level': reorder_level}
            )
            
            if not created:
                inventory.quantity += quantity
                inventory.reorder_level = reorder_level
                inventory.save()
            else:
                inventory.quantity = quantity
                inventory.save()
            
            messages.success(request, f'Successfully added {quantity} units of {product.name} to {store.name}.')
            return redirect('inventory')
            
        except Product.DoesNotExist:
            messages.error(request, 'Selected product does not exist.')
        except Store.DoesNotExist:
            messages.error(request, 'Selected store does not exist.')
        except ValueError:
            messages.error(request, 'Invalid quantity or reorder level value.')
        except Exception as e:
            messages.error(request, f'Error adding inventory: {str(e)}')
    
    # For GET request, show the form
    user = request.user
    
    if user.role not in ['manager', 'director', 'admin']:
        messages.error(request, 'You do not have permission to add inventory.')
        return redirect('dashboard')
    
    # Get products and stores based on permissions
    products = Product.objects.all()
    
    if user.role == 'manager' and user.store:
        stores = [user.store]
    else:
        stores = Store.objects.all()
    
    context = {
        'products': products,
        'stores': stores,
        'user': user
    }
    
    return render(request, 'pos_app/add_inventory.html', context)


@login_required
def create_user(request):
    if request.method == 'POST':
        # Check permissions
        if request.user.role not in ['director', 'admin']:
            messages.error(request, 'Only directors and admins can create users.')
            return redirect('dashboard')
        
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            role = request.POST.get('role')
            store_id = request.POST.get('store')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            
            # Validate required fields
            if not all([username, email, first_name, last_name, role, password]):
                messages.error(request, 'All fields are required.')
                return redirect('create_user')
            
            # Validate passwords match
            if password != password_confirm:
                messages.error(request, 'Passwords do not match.')
                return redirect('create_user')
            
            # Validate password length
            if len(password) < 6:
                messages.error(request, 'Password must be at least 6 characters long.')
                return redirect('create_user')
            
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return redirect('create_user')
            
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
                return redirect('create_user')
            
            # Validate role
            valid_roles = ['manager', 'staff']
            if role not in valid_roles:
                messages.error(request, 'Invalid role selected.')
                return redirect('create_user')
            
            # Get store if role requires it
            store = None
            if role in ['manager', 'staff'] and store_id:
                store = Store.objects.get(id=store_id)
            
            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role,
                store=store,
                password=password
            )
            
            messages.success(request, f'User {username} created successfully.')
            return redirect('create_user')
            
        except Store.DoesNotExist:
            messages.error(request, 'Selected store does not exist.')
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
    
    # For GET request, show the form
    if request.user.role not in ['director', 'admin']:
        messages.error(request, 'Only directors and admins can create users.')
        return redirect('dashboard')
    
    stores = Store.objects.all()
    
    context = {
        'stores': stores,
        'user': request.user
    }
    
    return render(request, 'pos_app/create_user.html', context)


@login_required
def add_product(request):
    if request.method == 'POST':
        # Check permissions
        if request.user.role not in ['director', 'admin', 'manager']:
            messages.error(request, 'You do not have permission to add products.')
            return redirect('dashboard')
        
        try:
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            category_id = request.POST.get('category')
            price = request.POST.get('price')
            photo = request.FILES.get('photo')  # Optional photo
            
            # Validate required fields
            if not all([name, category_id, price]):
                messages.error(request, 'Name, category, and price are required.')
                return redirect('add_product')
            
            # Validate price
            try:
                price = Decimal(price)
                if price <= 0:
                    messages.error(request, 'Price must be greater than 0.')
                    return redirect('add_product')
            except:
                messages.error(request, 'Invalid price format.')
                return redirect('add_product')
            
            # Get category
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                messages.error(request, 'Selected category does not exist.')
                return redirect('add_product')
            
            # Create product
            product = Product.objects.create(
                name=name,
                description=description,
                category=category,
                price=price,
                photo=photo  # This can be None if no photo was uploaded
            )
            
            messages.success(request, f'Product "{name}" created successfully.')
            return redirect('add_product')
            
        except Exception as e:
            messages.error(request, f'Error creating product: {str(e)}')
            return redirect('add_product')
    
    # For GET request, show the form
    if request.user.role not in ['director', 'admin', 'manager']:
        messages.error(request, 'You do not have permission to add products.')
        return redirect('dashboard')
    
    categories = Category.objects.all()
    
    context = {
        'categories': categories,
        'user': request.user
    }
    
    return render(request, 'pos_app/add_product.html', context)


@login_required
def stock_take(request):
    if request.method == 'POST':
        # Check permissions
        if request.user.role not in ['manager', 'director', 'admin']:
            messages.error(request, 'You do not have permission to perform stock take.')
            return redirect('dashboard')
        
        try:
            # Get all the submitted stock counts
            product_ids = request.POST.getlist('product_id')
            counted_quantities = request.POST.getlist('counted_quantity')
            
            # Managers can only do stock take for their store
            store = request.user.store if request.user.role == 'manager' else None
            
            if request.user.role == 'manager' and not store:
                messages.error(request, 'You are not assigned to a store.')
                return redirect('stock_take')
            
            updated_count = 0
            
            # Process each product update
            for product_id, counted_str in zip(product_ids, counted_quantities):
                try:
                    product_id = int(product_id)
                    counted_quantity = int(counted_str)
                    
                    if counted_quantity < 0:
                        messages.error(request, f'Counted quantity cannot be negative for product ID {product_id}.')
                        continue
                    
                    # Get the inventory item
                    if store:
                        inventory = Inventory.objects.get(product_id=product_id, store=store)
                    else:
                        # For directors/admins, they might want to specify which store
                        # We'll need to get store_id from POST data as well
                        store_id = request.POST.get(f'store_id_{product_id}')
                        if store_id:
                            store_obj = Store.objects.get(id=store_id)
                            inventory = Inventory.objects.get(product_id=product_id, store=store_obj)
                        else:
                            # If no store specified but role is admin/director, show error
                            messages.error(request, f'Store must be specified for product ID {product_id}.')
                            continue
                            
                    # Record the difference for tracking purposes
                    difference = counted_quantity - inventory.quantity
                    
                    # Update the quantity
                    inventory.quantity = counted_quantity
                    inventory.save()
                    
                    updated_count += 1
                    
                    # Optionally, we could create a stock take record for audit trail
                    # This could be extended to create a StockTake model to track changes
                    
                except ValueError:
                    messages.error(request, f'Invalid product ID or quantity: {product_id}, {counted_str}.')
                    continue
                except Inventory.DoesNotExist:
                    messages.error(request, f'Inventory item not found for product ID {product_id}.')
                    continue
                except Store.DoesNotExist:
                    messages.error(request, f'Store not found for product ID {product_id}.')
                    continue
                except Exception as e:
                    messages.error(request, f'Error updating inventory for product ID {product_id}: {str(e)}')
                    continue
            
            if updated_count > 0:
                messages.success(request, f'Stock take completed successfully. {updated_count} products updated.')
            else:
                messages.warning(request, 'No products were updated during stock take.')
                
            return redirect('stock_take')
            
        except Exception as e:
            messages.error(request, f'Error during stock take: {str(e)}')
    
    # For GET request, show the stock take form
    if request.user.role not in ['manager', 'director', 'admin']:
        messages.error(request, 'You do not have permission to perform stock take.')
        return redirect('dashboard')
    
    # Get inventory based on permissions
    if request.user.role == 'manager' and request.user.store:
        inventory_items = Inventory.objects.filter(store=request.user.store).select_related('product', 'product__category')
        stores = [request.user.store]  # Manager can only see their own store
    else:
        # Directors and admins can see all stores or select one
        store_id = request.GET.get('store')
        if store_id:
            try:
                selected_store = Store.objects.get(id=store_id)
                inventory_items = Inventory.objects.filter(store=selected_store).select_related('product', 'product__category')
            except Store.DoesNotExist:
                inventory_items = Inventory.objects.none()
        else:
            # By default, show first store or let them select
            inventory_items = Inventory.objects.filter(store=request.user.store if request.user.store else Store.objects.first()).select_related('product', 'product__category')
        
        stores = Store.objects.all()
    
    context = {
        'inventory_items': inventory_items,
        'stores': stores,
        'selected_store_id': request.GET.get('store'),
        'user': request.user
    }
    
    return render(request, 'pos_app/stock_take.html', context)


@login_required
def inventory_view(request):
    user = request.user
    
    if not can_manage_inventory(user):
        messages.error(request, 'You do not have permission to access inventory.')
        return redirect('dashboard')
    
    # For manager, only show inventory for their store
    if user.role == 'manager' and user.store:
        inventory_items = Inventory.objects.filter(store=user.store)
        stores = [user.store]
    else:
        inventory_items = Inventory.objects.all()
        stores = Store.objects.all()
    
    # Filter by store if selected
    store_filter = request.GET.get('store')
    if store_filter:
        inventory_items = inventory_items.filter(store_id=store_filter)
    
    # Pagination
    paginator = Paginator(inventory_items, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'inventory_items': page_obj,
        'stores': stores,
        'selected_store': store_filter,
        'user': user,
    }
    return render(request, 'pos_app/inventory.html', context)


@login_required
def inventory_transfer(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        from_store_id = request.POST.get('from_store_id')
        to_store_id = request.POST.get('to_store_id')
        quantity = request.POST.get('quantity')
        
        try:
            product = Product.objects.get(id=product_id)
            from_store = Store.objects.get(id=from_store_id)
            to_store = Store.objects.get(id=to_store_id)
            quantity = int(quantity)
            
            # Check permissions for initiating transfer
            if not can_transfer_inventory(request.user, from_store, to_store):
                messages.error(request, 'You do not have permission to initiate this transfer.')
                return redirect('inventory_transfer')
            
            # Check if from_store has enough inventory
            from_inventory = Inventory.objects.get(product=product, store=from_store)
            if from_inventory.quantity < quantity:
                messages.error(request, f'Insufficient inventory in {from_store.name}. Available: {from_inventory.quantity}')
                return redirect('inventory_transfer')
            
            # Check if item exists in destination store inventory, otherwise create it
            to_inventory, created = Inventory.objects.get_or_create(
                product=product, 
                store=to_store,
                defaults={'quantity': 0}
            )
            
            # Create transfer request
            transfer = InventoryTransfer.objects.create(
                product=product,
                from_store=from_store,
                to_store=to_store,
                quantity=quantity,
                requested_by=request.user
            )
            
            messages.success(request, 'Transfer request created successfully. Awaiting director approval.')
            return redirect('inventory_transfer')
            
        except (Product.DoesNotExist, Store.DoesNotExist, Inventory.DoesNotExist, ValueError):
            messages.error(request, 'Invalid data provided for transfer.')
            return redirect('inventory_transfer')
    
    # For GET request, show transfer form
    user = request.user
    
    # Check basic permission to access transfer page
    if not (user.role in ['manager', 'director', 'admin']):
        messages.error(request, 'You do not have permission to initiate inventory transfers.')
        return redirect('dashboard')
    
    # Managers can only transfer from their store
    if user.role == 'manager':
        available_products = Inventory.objects.filter(store=user.store, quantity__gt=0).select_related('product')
        from_stores = [user.store]
        to_stores = Store.objects.exclude(id=user.store.id) if user.store else Store.objects.all()
    else:
        available_products = Inventory.objects.filter(quantity__gt=0).select_related('product', 'store')
        from_stores = Store.objects.all()
        to_stores = Store.objects.all()
    
    # Show pending transfers for approval if user is director/admin
    pending_transfers = []
    if user.role in ['director', 'admin']:
        pending_transfers = InventoryTransfer.objects.filter(status='pending').select_related(
            'product', 'from_store', 'to_store', 'requested_by'
        )
    
    context = {
        'available_products': available_products,
        'from_stores': from_stores,
        'to_stores': to_stores,
        'pending_transfers': pending_transfers,
        'user': user,
    }
    return render(request, 'pos_app/inventory_transfer.html', context)


@login_required
def approve_transfer(request, transfer_id):
    if not can_approve_transfers(request.user):
        messages.error(request, 'Only directors and admins can approve transfers.')
        return redirect('inventory_transfer')
    
    transfer = get_object_or_404(InventoryTransfer, id=transfer_id)
    
    if transfer.status != 'pending':
        messages.error(request, 'Transfer is not pending.')
        return redirect('inventory_transfer')
    
    # Check inventory in source store
    try:
        from_inventory = Inventory.objects.get(product=transfer.product, store=transfer.from_store)
        if from_inventory.quantity < transfer.quantity:
            messages.error(request, f'Insufficient inventory in source store. Available: {from_inventory.quantity}')
            return redirect('inventory_transfer')
    except Inventory.DoesNotExist:
        messages.error(request, 'Source inventory not found.')
        return redirect('inventory_transfer')
    
    # Process the transfer
    from_inventory.quantity -= transfer.quantity
    from_inventory.save()
    
    to_inventory, created = Inventory.objects.get_or_create(
        product=transfer.product,
        store=transfer.to_store,
        defaults={'quantity': 0}
    )
    to_inventory.quantity += transfer.quantity
    to_inventory.save()
    
    # Update transfer status
    transfer.status = 'approved'
    transfer.approved_by = request.user
    transfer.approval_date = timezone.now()
    transfer.save()
    
    messages.success(request, f'Transfer of {transfer.quantity} {transfer.product.name} from {transfer.from_store.name} to {transfer.to_store.name} approved and processed.')
    return redirect('inventory_transfer')


@login_required
def reject_transfer(request, transfer_id):
    if not can_approve_transfers(request.user):
        messages.error(request, 'Only directors and admins can reject transfers.')
        return redirect('inventory_transfer')
    
    transfer = get_object_or_404(InventoryTransfer, id=transfer_id)
    
    if transfer.status != 'pending':
        messages.error(request, 'Transfer is not pending.')
        return redirect('inventory_transfer')
    
    transfer.status = 'rejected'
    transfer.approved_by = request.user
    transfer.approval_date = timezone.now()
    transfer.save()
    
    messages.success(request, 'Transfer request rejected.')
    return redirect('inventory_transfer')


@login_required
def sales_report(request):
    user = request.user
    
    if not can_view_reports(user):
        messages.error(request, 'You do not have permission to view reports.')
        return redirect('dashboard')
    
    # Date range filter
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to last 30 days
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include end date
    
    # Base query for transactions
    transactions = Transaction.objects.filter(
        transaction_type='sale',
        created_at__gte=start_date_obj,
        created_at__lt=end_date_obj
    )
    
    # Apply store filter based on user role
    if user.role == 'manager' and user.store:
        transactions = transactions.filter(store=user.store)
    elif user.role in ['director', 'admin']:
        # For directors/admins, filter by store if provided in request
        store_filter = request.GET.get('store')
        if store_filter:
            try:
                store_filter = int(store_filter)
                transactions = transactions.filter(store_id=store_filter)
            except ValueError:
                pass
    
    # Calculate summary statistics
    total_sales = transactions.aggregate(total=Sum('total_amount'))['total'] or 0
    total_transactions = transactions.count()
    avg_transaction_value = total_sales / total_transactions if total_transactions > 0 else 0
    
    # Group by date for daily sales chart
    daily_sales = transactions.extra(select={'date': 'date(created_at)'}).values('date').annotate(
        daily_total=Sum('total_amount'),
        transaction_count=Count('id')
    ).order_by('date')
    
    # Get all stores for filter dropdown (for directors/admins)
    available_stores = []
    if user.role in ['director', 'admin']:
        available_stores = Store.objects.all()
    
    # Top selling products (only for director/admin)
    top_products = []
    if user.role in ['director', 'admin']:
        top_products = TransactionItem.objects.filter(
            transaction__transaction_type='sale',
            transaction__created_at__gte=start_date_obj,
            transaction__created_at__lt=end_date_obj
        ).values('product__name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('total_price')
        ).order_by('-total_quantity')[:10]
    
    # Sales by store (only for director/admin)
    sales_by_store = []
    if user.role in ['director', 'admin']:
        sales_by_store = Transaction.objects.filter(
            transaction_type='sale',
            created_at__gte=start_date_obj,
            created_at__lt=end_date_obj
        ).values('store__name').annotate(
            total_sales=Sum('total_amount'),
            transaction_count=Count('id')
        )
    
    context = {
        'user': user,
        'total_sales': total_sales,
        'total_transactions': total_transactions,
        'avg_transaction_value': avg_transaction_value,
        'daily_sales': daily_sales,
        'top_products': top_products,
        'start_date': start_date,
        'end_date': end_date,
        'available_stores': available_stores,
        'sales_by_store': sales_by_store,
    }
    
    return render(request, 'pos_app/sales_report.html', context)


@login_required
def my_commissions(request):
    """View for staff to see their commission history"""
    if request.user.role != 'staff':
        messages.error(request, 'You do not have permission to view commissions.')
        return redirect('dashboard')
    
    # Get all transactions by this user
    transactions = Transaction.objects.filter(
        user=request.user,
        transaction_type='sale'
    ).order_by('-created_at')
    
    # Get recent commission transactions (last 30 days)
    recent_transactions = transactions.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    )
    
    # Calculate total commission from all transactions
    total_commission = transactions.aggregate(total=Sum('commission'))['total'] or Decimal('0.00')
    
    # Update user's total commission field if it's different from calculated value
    user = request.user
    if user.total_commission != total_commission:
        user.total_commission = total_commission
        user.save(update_fields=['total_commission'])
    
    context = {
        'user': request.user,
        'transactions': recent_transactions,
        'total_commission': total_commission,
    }
    
    return render(request, 'pos_app/commissions.html', context)


@login_required
def generate_receipt(request, transaction_id):
    """Generate a receipt for a specific transaction"""
    transaction = get_object_or_404(Transaction, transaction_id=transaction_id)
    
    # Check permission - user must be staff, manager of the store, or director/admin
    if (request.user.role != 'staff' or request.user != transaction.user) and \
       not (request.user.role == 'manager' and request.user.store == transaction.store) and \
       request.user.role not in ['director', 'admin']:
        messages.error(request, 'You do not have permission to view this receipt.')
        return redirect('dashboard')
    
    # Get transaction items
    items = transaction.items.all()
    
    context = {
        'transaction': transaction,
        'items': items,
        'total_items': items.count(),
    }
    
    # Render the receipt HTML template
    html_string = render_to_string('pos_app/receipt.html', context)
    
    # Generate PDF
    html = HTML(string=html_string)
    css = CSS(string='''
        @page {
            size: A4;
            margin: 1cm;
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
        }
        .receipt-header {
            text-align: center;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .receipt-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .receipt-info {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
        }
        th, td {
            border: 1px solid #333;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f0f0f0;
        }
        .total-section {
            text-align: right;
            margin-top: 15px;
        }
        .footer {
            margin-top: 20px;
            text-align: center;
            border-top: 1px solid #333;
            padding-top: 10px;
            font-size: 10px;
        }
    ''')
    
    pdf = html.write_pdf(stylesheets=[css])
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{transaction.transaction_id}.pdf"'
    return response


@login_required
def view_receipts(request):
    """View list of receipts for the user"""
    # Get transactions based on user role
    if request.user.role == 'staff':
        # Staff can only see their own transactions
        transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    elif request.user.role == 'manager':
        # Managers can see transactions from their store
        transactions = Transaction.objects.filter(store=request.user.store).order_by('-created_at')
    elif request.user.role in ['director', 'admin']:
        # Directors and admins can see all transactions
        transactions = Transaction.objects.all().order_by('-created_at')
    else:
        messages.error(request, 'You do not have permission to view receipts.')
        return redirect('dashboard')
    
    # Pagination
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'transactions': page_obj,
        'user': request.user
    }
    
    return render(request, 'pos_app/receipts.html', context)


@login_required
def view_receipt(request, transaction_id):
    """View receipt as HTML page"""
    transaction = get_object_or_404(Transaction, transaction_id=transaction_id)
    
    # Check permission
    if (request.user.role != 'staff' or request.user != transaction.user) and \
       not (request.user.role == 'manager' and request.user.store == transaction.store) and \
       request.user.role not in ['director', 'admin']:
        messages.error(request, 'You do not have permission to view this receipt.')
        return redirect('dashboard')
    
    # Get transaction items
    items = transaction.items.all()
    
    context = {
        'transaction': transaction,
        'items': items,
        'total_items': items.count(),
    }
    
    return render(request, 'pos_app/receipt.html', context)