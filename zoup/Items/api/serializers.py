from rest_framework import viewsets
from Items.models import Product,Category



class ProductSerializer(viewsets.ViewSet):

    class Meta:
        model=Product
        fields='__all__'
