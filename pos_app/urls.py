from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('pos/', views.pos_view, name='pos'),
    path('process_sale/', views.process_sale, name='process_sale'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('inventory_transfer/', views.inventory_transfer, name='inventory_transfer'),
    path('approve_transfer/<int:transfer_id>/', views.approve_transfer, name='approve_transfer'),
    path('reject_transfer/<int:transfer_id>/', views.reject_transfer, name='reject_transfer'),
    path('sales_report/', views.sales_report, name='sales_report'),
    path('my_commissions/', views.my_commissions, name='my_commissions'),
    path('receipts/', views.view_receipts, name='view_receipts'),
    path('receipt/<str:transaction_id>/', views.view_receipt, name='view_receipt'),
    path('receipt/<str:transaction_id>/download/', views.generate_receipt, name='generate_receipt'),
    path('add_inventory/', views.add_inventory, name='add_inventory'),
    path('create_user/', views.create_user, name='create_user'),
    path('add_product/', views.add_product, name='add_product'),
    path('stock_take/', views.stock_take, name='stock_take'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
]