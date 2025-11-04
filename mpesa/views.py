import requests
import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import datetime
from requests.auth import HTTPBasicAuth
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from decimal import Decimal
from .models import MpesaPayment
from pos_app.models import Transaction
import base64
from django.utils import timezone


class MpesaConfiguration:
    """
    Configuration for Safaricom M-Pesa API
    """
    # You would typically get these from your .env file in production
    consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', 'your_consumer_key_here')
    consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', 'your_consumer_secret_here')
    shortcode = getattr(settings, 'MPESA_SHORTCODE', 'your_shortcode_here')
    passkey = getattr(settings, 'MPESA_PASSKEY', 'your_passkey_here')
    callback_url = getattr(settings, 'MPESA_CALLBACK_URL', f'{settings.ALLOWED_HOSTS[0]}/mpesa/callback/')
    
    # URLs for sandbox environment
    base_url = 'https://sandbox.safaricom.co.ke'
    access_token_url = f'{base_url}/oauth/v1/generate?grant_type=client_credentials'
    stk_push_url = f'{base_url}/mpesa/stkpush/v1/processrequest'
    stk_callback_url = f'{base_url}/mpesa/stkpushquery/v1/query'


def get_access_token():
    """
    Get access token from Safaricom OAuth
    """
    try:
        response = requests.get(
            MpesaConfiguration.access_token_url,
            auth=HTTPBasicAuth(
                MpesaConfiguration.consumer_key,
                MpesaConfiguration.consumer_secret
            )
        )
        response_data = response.json()
        return response_data['access_token']
    except Exception as e:
        print(f"Error getting access token: {str(e)}")
        return None


def generate_password():
    """
    Generate password for M-Pesa API request
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = MpesaConfiguration.shortcode + MpesaConfiguration.passkey + timestamp
    encoded = base64.b64encode(password.encode('utf-8'))
    return encoded.decode('utf-8'), timestamp


@login_required
@require_http_methods(["POST"])
def initiate_stk_push(request):
    """
    Initiate M-Pesa STK Push request
    """
    try:
        # Get data from request
        transaction_id = request.POST.get('transaction_id')
        phone_number = request.POST.get('phone_number')
        amount = request.POST.get('amount')
        
        if not all([transaction_id, phone_number, amount]):
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
        
        # Validate phone number format (should be 10-15 digits, starting with 254)
        if not phone_number.startswith('254') or len(phone_number) < 10 or len(phone_number) > 15:
            return JsonResponse({'error': 'Invalid phone number format. Use format: 2547XXXXXXXX'}, status=400)
        
        # Validate transaction exists and isn't already paid
        try:
            transaction = Transaction.objects.get(transaction_id=transaction_id)
        except Transaction.DoesNotExist:
            return JsonResponse({'error': 'Transaction not found'}, status=404)
        
        # Check if payment already exists
        existing_payment = MpesaPayment.objects.filter(transaction=transaction).first()
        if existing_payment:
            return JsonResponse({'error': 'Payment already initiated for this transaction'}, status=400)
        
        # Validate amount matches transaction
        if Decimal(amount) != transaction.total_amount:
            return JsonResponse({'error': 'Amount does not match transaction total'}, status=400)
        
        # Get access token
        access_token = get_access_token()
        if not access_token:
            return JsonResponse({'error': 'Failed to get access token'}, status=500)
        
        # Generate password and timestamp
        password, timestamp = generate_password()
        
        # Create STK push payload
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "BusinessShortCode": MpesaConfiguration.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": MpesaConfiguration.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": f"{settings.ALLOWED_HOSTS[0]}/mpesa/callback/",  # This should be properly configured
            "AccountReference": f"POS-{transaction.transaction_id[:10]}",
            "TransactionDesc": f"Payment for POS transaction {transaction.transaction_id}"
        }
        
        # Send STK push request
        response = requests.post(
            MpesaConfiguration.stk_push_url,
            json=payload,
            headers=headers
        )
        
        response_data = response.json()
        
        if response_data.get('ResponseCode') == '0':
            # Payment initiated successfully, create payment record
            checkout_request_id = response_data.get('CheckoutRequestID')
            merchant_request_id = response_data.get('MerchantRequestID')
            
            payment = MpesaPayment.objects.create(
                transaction=transaction,
                phone_number=phone_number,
                amount=Decimal(amount),
                checkout_request_id=checkout_request_id,
                merchant_request_id=merchant_request_id,
                status='pending'
            )
            
            return JsonResponse({
                'success': True,
                'CheckoutRequestID': checkout_request_id,
                'MerchantRequestID': merchant_request_id,
                'message': 'STK push sent successfully. Please complete payment on your phone.'
            })
        else:
            # Error occurred
            return JsonResponse({
                'error': response_data.get('errorMessage', 'Failed to initiate payment'),
                'details': response_data
            }, status=400)
    
    except Exception as e:
        print(f"Error in initiate_stk_push: {str(e)}")
        return JsonResponse({'error': 'An error occurred while initiating payment'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def mpesa_callback(request):
    """
    Handle M-Pesa callback
    """
    try:
        # Parse the callback data
        callback_data = json.loads(request.body)
        
        # Extract relevant information
        body = callback_data.get('Body', {})
        stk_callback = body.get('stkCallback', {})
        
        merchant_request_id = stk_callback.get('MerchantRequestID')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')
        
        # Update payment status based on result
        try:
            payment = MpesaPayment.objects.get(checkout_request_id=checkout_request_id)
            
            if result_code == 0:  # Success
                payment.status = 'completed'
                payment.completed_at = timezone.now()
                payment.save()
                
                # Update transaction status or perform other actions
                # For example, you could mark the transaction as paid
                print(f"Payment {checkout_request_id} completed successfully")
                
                return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
            else:
                payment.status = 'failed'
                payment.completed_at = timezone.now()
                payment.save()
                
                print(f"Payment {checkout_request_id} failed: {result_desc}")
                
                return JsonResponse({'ResultCode': result_code, 'ResultDesc': result_desc})
        
        except MpesaPayment.DoesNotExist:
            print(f"Payment with CheckoutRequestID {checkout_request_id} not found")
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Payment not found'})
    
    except Exception as e:
        print(f"Error in callback: {str(e)}")
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Error processing callback'})


def check_payment_status(request, checkout_request_id):
    """
    Check payment status for STK push query
    """
    try:
        access_token = get_access_token()
        if not access_token:
            return JsonResponse({'error': 'Failed to get access token'}, status=500)
        
        password, timestamp = generate_password()
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "BusinessShortCode": MpesaConfiguration.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }
        
        response = requests.post(
            MpesaConfiguration.stk_callback_url,
            json=payload,
            headers=headers
        )
        
        return JsonResponse(response.json())
    
    except Exception as e:
        print(f"Error checking payment status: {str(e)}")
        return JsonResponse({'error': 'Error checking payment status'}, status=500)
