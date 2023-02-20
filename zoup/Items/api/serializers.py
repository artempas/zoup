from rest_framework.serializers import ModelSerializer
from Items.models import Product


class ProductSerializer(ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = [
            "created_date",
            "created_by",
            "family",
        ]
