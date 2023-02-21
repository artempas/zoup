from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from Items.api.serializers import *
from Items.models import *
from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest, HttpResponseNotFound


class Products(GenericAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    def get(self, request: Request, pk: int):
        if pk:
            products = get_object_or_404(Product, id=pk)
            serialized_objects = self.serializer_class(products)
        else:
            if "chat_id" not in request.data:
                return HttpResponseBadRequest("chat_id")
            family = Profile.objects.get(chat_id=request.query_params.get("chat_id")).family
            products = Product.objects.filter(family=family)
            serialized_objects = self.serializer_class(products, many=True)
        return Response(serialized_objects.data)

    def post(self, request: Request, pk=None):
        if pk:
            return HttpResponseBadRequest("Create method is not implemented for slug url")
        if "chat_id" not in request.data:
            return HttpResponseBadRequest("chat_id")
        data = request.data
        usr = get_object_or_404(User, profile__chat_id=request.data["chat_id"])
        data["created_by"] = usr.id
        if not usr.profile.family:
            return HttpResponseNotFound("Family not found")
        data["family"] = usr.profile.family.id
        del data["chat_id"]
        serialized = self.serializer_class(data=request.data)
        serialized.is_valid(raise_exception=True)
        serialized.save()
        return Response(serialized.data)

    def delete(self, request: Request, pk):
        if pk:
            Product.objects.get(id=pk).delete()
            return Response({"success": True})
        if "chat_id" not in request.data:
            return HttpResponseBadRequest("chat_id")
        filter_by = request.data
        filter_by["family"] = Profile.objects.get(chat_id=filter_by["chat_id"]).family
        del filter_by["chat_id"]
        objects_to_delete = Product.objects.filter(**filter_by)
        deleted = len(objects_to_delete)
        objects_to_delete.delete()
        return Response({"deleted": deleted})

    def put(self, request: Request, pk: int):
        if not pk:
            return HttpResponseBadRequest("Update without slug is not implemented")
        instance = Product.objects.get(id=pk)
        serialized = self.serializer_class(data=request.data, instance=instance, partial=True)
        serialized.is_valid(raise_exception=True)
        serialized.save()
        return Response(serialized.data)
