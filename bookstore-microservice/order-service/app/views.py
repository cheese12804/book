from decimal import Decimal

import requests
from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response

from .models import Order, OrderItem
from .serializers import OrderSerializer


class OrderListCreateView(generics.ListCreateAPIView):
    queryset = Order.objects.all().order_by('id')
    serializer_class = OrderSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        customer_id = request.data.get('customer_id')
        pay_method = request.data.get('pay_method')
        ship_method = request.data.get('ship_method')
        shipping_address = request.data.get('shipping_address')

        if not all([customer_id, pay_method, ship_method, shipping_address]):
            return Response({'error': 'customer_id, pay_method, ship_method, shipping_address are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            customer_response = requests.get(f'http://customer-service:8000/customers/{customer_id}/', timeout=5)
            if customer_response.status_code != 200:
                return Response({'error': 'Customer not found'}, status=status.HTTP_400_BAD_REQUEST)

            cart_response = requests.get(f'http://cart-service:8000/carts/{customer_id}/', timeout=5)
            if cart_response.status_code != 200:
                return Response({'error': 'Cart not found'}, status=status.HTTP_400_BAD_REQUEST)
            cart_data = cart_response.json()
            cart_items = cart_data.get('items', [])
            if not cart_items:
                return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

            total_amount = Decimal('0.00')
            order = Order.objects.create(
                customer_id=customer_id,
                total_amount=Decimal('0.00'),
                status='PENDING',
                pay_method=pay_method,
                ship_method=ship_method,
                shipping_address=shipping_address,
            )

            for item in cart_items:
                book_id = item['book_id']
                quantity = int(item['quantity'])
                book_response = requests.get(f'http://book-service:8000/books/{book_id}/', timeout=5)
                if book_response.status_code != 200:
                    order.status = 'FAILED'
                    order.save()
                    return Response({'error': f'Book {book_id} not found'}, status=status.HTTP_400_BAD_REQUEST)
                price = Decimal(str(book_response.json()['price']))
                total_amount += price * quantity
                OrderItem.objects.create(order=order, book_id=book_id, quantity=quantity, price=price)

            order.total_amount = total_amount
            order.save()

            payment_response = requests.post(
                'http://pay-service:8000/payments/',
                json={'order_id': order.id, 'amount': str(total_amount), 'method': pay_method},
                timeout=5,
            )
            shipment_response = requests.post(
                'http://ship-service:8000/shipments/',
                json={'order_id': order.id, 'address': shipping_address, 'method': ship_method},
                timeout=5,
            )

            if payment_response.status_code in (200, 201) and shipment_response.status_code in (200, 201):
                order.status = 'CONFIRMED'
            else:
                order.status = 'FAILED'
            order.save()
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

        except requests.RequestException as exc:
            return Response({'error': 'Dependent service unavailable', 'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class OrderDetailView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
