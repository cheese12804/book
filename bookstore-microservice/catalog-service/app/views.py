import requests
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Catalog, CatalogBook
from .serializers import CatalogBookSerializer, CatalogSerializer


class CatalogListCreateView(generics.ListCreateAPIView):
    queryset = Catalog.objects.all().order_by('id')
    serializer_class = CatalogSerializer


class CatalogDetailView(generics.RetrieveAPIView):
    queryset = Catalog.objects.all()
    serializer_class = CatalogSerializer


class CatalogBookView(APIView):
    def post(self, request, pk):
        catalog = get_object_or_404(Catalog, pk=pk)
        book_id = request.data.get('book_id')
        if not book_id:
            return Response({'error': 'book_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            book_response = requests.get(f'http://book-service:8000/books/{book_id}/', timeout=5)
            if book_response.status_code != 200:
                return Response({'error': 'Book does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        except requests.RequestException as exc:
            return Response({'error': 'book-service unavailable', 'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        catalog_book, created = CatalogBook.objects.get_or_create(catalog=catalog, book_id=book_id)
        serializer = CatalogBookSerializer(catalog_book)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def get(self, request, pk):
        catalog = get_object_or_404(Catalog, pk=pk)
        serializer = CatalogBookSerializer(catalog.catalog_books.all().order_by('id'), many=True)
        return Response(serializer.data)
