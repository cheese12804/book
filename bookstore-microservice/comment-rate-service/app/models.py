from django.db import models


class CommentRate(models.Model):
    customer_id = models.IntegerField()
    book_id = models.IntegerField()
    rating = models.IntegerField()
    comment = models.TextField(blank=True, null=True)
