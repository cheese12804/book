from django.urls import path

from .views import ShipmentDetailView, ShipmentListCreateView

urlpatterns = [
    path('shipments/', ShipmentListCreateView.as_view(), name='shipment-list-create'),
    path('shipments/<int:pk>/', ShipmentDetailView.as_view(), name='shipment-detail'),
]
