from django.db import models


class Order(models.Model):
    customer_id = models.IntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default='PENDING')
    pay_method = models.CharField(max_length=50)
    ship_method = models.CharField(max_length=50)
    shipping_address = models.CharField(max_length=255)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    book_id = models.IntegerField()
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
