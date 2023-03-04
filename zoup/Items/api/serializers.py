from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField
from Items.models import Product, Family, User, Profile


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


class ProfileSerializer(ModelSerializer):
    class Meta:
        model = Profile
        exclude = ["user", "id"]
        depth = 1


class UserSerializer(ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ["id", "username", "profile"]
