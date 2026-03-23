from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('books/', views.books_view, name='books'),
    path('books/<int:book_id>/', views.book_detail_view, name='book-detail'),
    path('cart/add/', views.cart_add_view, name='cart-add'),
    path('cart/<int:customer_id>/', views.cart_view, name='cart'),
    path('cart/item/<int:item_id>/update/', views.cart_item_update_view, name='cart-item-update'),
    path('cart/item/<int:item_id>/delete/', views.cart_item_delete_view, name='cart-item-delete'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/create/', views.checkout_view, name='order-create'),
    path('orders/result/', views.order_result_view, name='order-result'),
    path('reviews/book/<int:book_id>/', views.reviews_view, name='reviews'),
    path('recommendations/', views.recommendations_view, name='recommendations'),
    path('admin-lite/', views.admin_lite_view, name='admin-lite'),
]
