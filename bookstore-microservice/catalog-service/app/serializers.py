from rest_framework import serializers

from .models import Catalog, CatalogBook


class CatalogBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogBook
        fields = '__all__'


class CatalogSerializer(serializers.ModelSerializer):
    catalog_books = CatalogBookSerializer(many=True, read_only=True)

    class Meta:
        model = Catalog
        fields = '__all__'
