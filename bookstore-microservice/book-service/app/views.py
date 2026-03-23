import requests
from rest_framework import generics, status
from rest_framework.response import Response

from .models import Book
from .serializers import BookSerializer


class BookListCreateView(generics.ListCreateAPIView):
    queryset = Book.objects.all().order_by('id')
    serializer_class = BookSerializer

    def create(self, request, *args, **kwargs):
        staff_id = request.data.get('created_by_staff_id')
        if staff_id:
            try:
                staff_response = requests.get(f'http://staff-service:8000/staffs/{staff_id}/', timeout=5)
                if staff_response.status_code != 200:
                    return Response({'error': 'Staff not found'}, status=status.HTTP_400_BAD_REQUEST)
            except requests.RequestException as exc:
                return Response({'error': 'staff-service unavailable', 'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return super().create(request, *args, **kwargs)


class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
