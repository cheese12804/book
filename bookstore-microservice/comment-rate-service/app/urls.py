from django.urls import path

from .views import ReviewByBookView, ReviewByCustomerView, ReviewListCreateView

urlpatterns = [
    path('reviews/', ReviewListCreateView.as_view(), name='review-list-create'),
    path('reviews/book/<int:book_id>/', ReviewByBookView.as_view(), name='review-by-book'),
    path('reviews/customer/<int:customer_id>/', ReviewByCustomerView.as_view(), name='review-by-customer'),
]
