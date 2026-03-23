from django.db import models


class Cart(models.Model):
    customer_id = models.IntegerField(unique=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    book_id = models.IntegerField()
    quantity = models.IntegerField()

    class Meta:
        unique_together = ('cart', 'book_id')
