from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField
from Items.models import Product, Family, User, Profile


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


class ProductSerializer(ModelSerializer):
    family = PrimaryKeyRelatedField(queryset=Family.objects.all())
    created_by = UserSerializer(read_only=True)
    user_id = PrimaryKeyRelatedField(source="created_by", write_only=True, queryset=User.objects.all())

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = [
            "created_date",
            "created_by",
            "family",
        ]
