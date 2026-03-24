from django.db import models


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    created_by_staff_id = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.title
