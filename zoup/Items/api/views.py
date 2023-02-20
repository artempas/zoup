from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from Items.api.serializers import *
from Items.models import *
from django.http import HttpResponseBadRequest


class Products(APIView):
    def get(self, request: Request):
        family = Profile.objects.get(chat_id=request.query_params.get("chat_id")).family
        products = Product.objects.filter(family=family)
        serialized_objects = ProductSerializer(products, many=True)
        return Response(serialized_objects.data)

    def post(self, request: Request):
        if "chat_id" not in request.data:
            return HttpResponseBadRequest("chat_id")
        request.data["created_by"] = User.objects.filter(profile__chat_id=request.data["chat_id"])
        serialized = ProductSerializer(data=request.data)
        if serialized.is_valid():
            serialized.save()
            return Response(serialized.data)
        else:
            return HttpResponseBadRequest("Bad request")

    def delete(self, request: Request):
        pass
