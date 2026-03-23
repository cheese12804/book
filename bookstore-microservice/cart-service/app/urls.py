from django.urls import path

from .views import CartByCustomerView, CartCreateView, CartItemCreateView, CartItemDetailView

urlpatterns = [
    path('carts/', CartCreateView.as_view(), name='cart-create'),
    path('carts/<int:customer_id>/', CartByCustomerView.as_view(), name='cart-by-customer'),
    path('cart-items/', CartItemCreateView.as_view(), name='cart-item-create'),
    path('cart-items/<int:pk>/', CartItemDetailView.as_view(), name='cart-item-detail'),
]
