import requests
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItem
from .serializers import CartItemSerializer, CartSerializer


class CartCreateView(generics.CreateAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    def create(self, request, *args, **kwargs):
        customer_id = request.data.get('customer_id')
        if not customer_id:
            return Response({'error': 'customer_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        cart, created = Cart.objects.get_or_create(customer_id=customer_id)
        serializer = self.get_serializer(cart)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class CartByCustomerView(APIView):
    def get(self, request, customer_id):
        cart = get_object_or_404(Cart, customer_id=customer_id)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class CartItemCreateView(APIView):
    def post(self, request):
        customer_id = request.data.get('customer_id')
        book_id = request.data.get('book_id')
        quantity = int(request.data.get('quantity', 1))

        if not customer_id or not book_id:
            return Response({'error': 'customer_id and book_id are required'}, status=status.HTTP_400_BAD_REQUEST)
        if quantity <= 0:
            return Response({'error': 'quantity must be positive'}, status=status.HTTP_400_BAD_REQUEST)

        cart = get_object_or_404(Cart, customer_id=customer_id)
        try:
            book_response = requests.get(f'http://book-service:8000/books/{book_id}/', timeout=5)
            if book_response.status_code != 200:
                return Response({'error': 'Book not found'}, status=status.HTTP_400_BAD_REQUEST)
        except requests.RequestException as exc:
            return Response({'error': 'book-service unavailable', 'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        item, created = CartItem.objects.get_or_create(cart=cart, book_id=book_id, defaults={'quantity': quantity})
        if not created:
            item.quantity += quantity
            item.save()

        serializer = CartItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class CartItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
