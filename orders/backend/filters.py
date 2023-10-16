from django_filters import rest_framework as filters
from backend.models import ProductInfo


class ProductFilter(filters.FilterSet):
    shop_id = filters.NumberFilter(field_name="shop__id")
    category_id = filters.NumberFilter(field_name="product__category_id")

    class Meta:
        model = ProductInfo
        fields = ["shop__id", "product__category_id"]