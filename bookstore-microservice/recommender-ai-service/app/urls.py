from django.urls import path

from .views import RecommendationByCustomerView, RecommendationView

urlpatterns = [
    path('recommendations/', RecommendationView.as_view(), name='recommendations'),
    path('recommendations/customer/<int:customer_id>/', RecommendationByCustomerView.as_view(), name='recommendations-customer'),
]
