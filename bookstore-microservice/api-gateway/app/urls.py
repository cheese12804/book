from django.urls import path

from .views import (
    books_view,
    cart_view,
    order_create_view,
    order_result_view,
    recommendations_view,
    reviews_by_book_view,
)

urlpatterns = [
    path('', books_view, name='home'),
    path('books/', books_view, name='books-page'),
    path('cart/<int:customer_id>/', cart_view, name='cart-page'),
    path('orders/create/', order_create_view, name='order-create-page'),
    path('orders/result/', order_result_view, name='order-result-page'),
    path('reviews/book/<int:book_id>/', reviews_by_book_view, name='reviews-page'),
    path('recommendations/', recommendations_view, name='recommendations-page'),
]
