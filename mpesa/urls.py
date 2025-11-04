from django.urls import path
from . import views

urlpatterns = [
    path('initiate-payment/', views.initiate_stk_push, name='initiate_stk_push'),
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
    path('check-status/<str:checkout_request_id>/', views.check_payment_status, name='check_payment_status'),
]