import requests
from rest_framework import generics, status
from rest_framework.response import Response

from .models import CommentRate
from .serializers import CommentRateSerializer


class ReviewListCreateView(generics.ListCreateAPIView):
    queryset = CommentRate.objects.all().order_by('id')
    serializer_class = CommentRateSerializer

    def create(self, request, *args, **kwargs):
        customer_id = request.data.get('customer_id')
        book_id = request.data.get('book_id')
        if not customer_id or not book_id:
            return Response({'error': 'customer_id and book_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            customer_response = requests.get(f'http://customer-service:8000/customers/{customer_id}/', timeout=5)
            book_response = requests.get(f'http://book-service:8000/books/{book_id}/', timeout=5)
            if customer_response.status_code != 200 or book_response.status_code != 200:
                return Response({'error': 'Invalid customer or book'}, status=status.HTTP_400_BAD_REQUEST)
        except requests.RequestException as exc:
            return Response({'error': 'Dependency unavailable', 'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return super().create(request, *args, **kwargs)


class ReviewByBookView(generics.ListAPIView):
    serializer_class = CommentRateSerializer

    def get_queryset(self):
        return CommentRate.objects.filter(book_id=self.kwargs['book_id']).order_by('-id')


class ReviewByCustomerView(generics.ListAPIView):
    serializer_class = CommentRateSerializer

    def get_queryset(self):
        return CommentRate.objects.filter(customer_id=self.kwargs['customer_id']).order_by('-id')
