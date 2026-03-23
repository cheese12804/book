import requests
from rest_framework import generics, status
from rest_framework.response import Response

from .models import Customer
from .serializers import CustomerSerializer


class CustomerListCreateView(generics.ListCreateAPIView):
    queryset = Customer.objects.all().order_by('id')
    serializer_class = CustomerSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = serializer.save()
        response_data = CustomerSerializer(customer).data
        warning = None
        try:
            cart_response = requests.post(
                'http://cart-service:8000/carts/',
                json={'customer_id': customer.id},
                timeout=5,
            )
            if cart_response.status_code not in (200, 201):
                warning = {
                    'message': 'Customer created but cart creation failed.',
                    'cart_service_response': cart_response.text,
                }
        except requests.RequestException as exc:
            warning = {
                'message': 'Customer created but cart-service is unavailable.',
                'detail': str(exc),
            }

        if warning:
            return Response({'customer': response_data, 'warning': warning}, status=status.HTTP_201_CREATED)
        return Response(response_data, status=status.HTTP_201_CREATED)


class CustomerDetailView(generics.RetrieveAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
