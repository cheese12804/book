from django.db import models


class Catalog(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)


class CatalogBook(models.Model):
    catalog = models.ForeignKey(Catalog, on_delete=models.CASCADE, related_name='catalog_books')
    book_id = models.IntegerField()

    class Meta:
        unique_together = ('catalog', 'book_id')
