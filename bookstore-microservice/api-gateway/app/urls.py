from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('books/', views.books_view, name='books'),
    path('books/<int:book_id>/', views.book_detail_view, name='book-detail'),

    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.cart_add_view, name='cart-add'),
    path('cart/item/<int:item_id>/update/', views.cart_item_update_view, name='cart-item-update'),
    path('cart/item/<int:item_id>/delete/', views.cart_item_delete_view, name='cart-item-delete'),

    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/create/', views.checkout_view, name='order-create'),
    path('orders/result/', views.order_result_view, name='order-result'),
    path('my-orders/', views.my_orders_view, name='my-orders'),

    path('reviews/book/<int:book_id>/', views.reviews_view, name='reviews'),
    path('recommendations/', views.recommendations_view, name='recommendations'),

    path('staff/dashboard/', views.staff_dashboard_view, name='staff-dashboard'),
    path('staff/books/<int:book_id>/edit/', views.staff_book_edit_view, name='staff-book-edit'),
    path('staff/books/<int:book_id>/delete/', views.staff_book_delete_view, name='staff-book-delete'),
]
