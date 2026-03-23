from rest_framework import generics

from .models import Manager
from .serializers import ManagerSerializer


class ManagerListCreateView(generics.ListCreateAPIView):
    queryset = Manager.objects.all().order_by('id')
    serializer_class = ManagerSerializer


class ManagerDetailView(generics.RetrieveAPIView):
    queryset = Manager.objects.all()
    serializer_class = ManagerSerializer
