from django.urls import path

from .views import StaffDetailView, StaffListCreateView

urlpatterns = [
    path('staffs/', StaffListCreateView.as_view(), name='staff-list-create'),
    path('staffs/<int:pk>/', StaffDetailView.as_view(), name='staff-detail'),
]
