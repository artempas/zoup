from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField
from Items.models import Product, Family, User


class ProductSerializer(ModelSerializer):
    family = PrimaryKeyRelatedField(queryset=Family.objects.all())
    created_by = PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = [
            "created_date",
            "created_by",
            "family",
        ]
