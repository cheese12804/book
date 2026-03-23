from django.urls import path

from .views import CatalogBookView, CatalogDetailView, CatalogListCreateView

urlpatterns = [
    path('catalogs/', CatalogListCreateView.as_view(), name='catalog-list-create'),
    path('catalogs/<int:pk>/', CatalogDetailView.as_view(), name='catalog-detail'),
    path('catalogs/<int:pk>/books/', CatalogBookView.as_view(), name='catalog-books'),
]
