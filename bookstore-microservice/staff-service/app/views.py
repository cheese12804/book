from rest_framework import generics

from .models import Staff
from .serializers import StaffSerializer


class StaffListCreateView(generics.ListCreateAPIView):
    queryset = Staff.objects.all().order_by('id')
    serializer_class = StaffSerializer


class StaffDetailView(generics.RetrieveAPIView):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
