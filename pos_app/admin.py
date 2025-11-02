from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Store, Category, Product, Inventory, Transaction, TransactionItem, InventoryTransfer


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'role', 'store', 'commission_rate', 'is_staff', 'is_active')
    list_filter = ('role', 'store', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('POS Info', {'fields': ('role', 'store', 'commission_rate')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'store', 'commission_rate', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'created_at')
    search_fields = ('name', 'address')
    list_filter = ('created_at',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'display_photo', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('category', 'created_at')
    list_per_page = 20
    
    def display_photo(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.photo.url)
        return "No Photo"
    display_photo.short_description = 'Photo'


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'store', 'quantity', 'reorder_level', 'updated_at')
    list_filter = ('store', 'product__category', 'updated_at')
    search_fields = ('product__name', 'store__name')
    list_editable = ('quantity', 'reorder_level')
    list_per_page = 20


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'store', 'transaction_type', 'total_amount', 'commission', 'created_at')
    list_filter = ('transaction_type', 'store', 'created_at', 'user')
    search_fields = ('transaction_id', 'user__username', 'store__name')
    readonly_fields = ('transaction_id', 'created_at')
    list_per_page = 20


@admin.register(TransactionItem)
class TransactionItemAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'product', 'quantity', 'unit_price', 'total_price')
    list_filter = ('transaction__created_at', 'product')
    search_fields = ('transaction__transaction_id', 'product__name')
    list_per_page = 20


@admin.register(InventoryTransfer)
class InventoryTransferAdmin(admin.ModelAdmin):
    list_display = ('product', 'from_store', 'to_store', 'quantity', 'status', 'requested_by', 'request_date')
    list_filter = ('status', 'request_date', 'from_store', 'to_store', 'requested_by')
    search_fields = ('product__name', 'from_store__name', 'to_store__name', 'requested_by__username')
    list_per_page = 20
    readonly_fields = ('request_date', 'approval_date')


admin.site.register(User, CustomUserAdmin)