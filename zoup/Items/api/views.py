from django.core.exceptions import ObjectDoesNotExist
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from Items.api.serializers import *
from Items.models import *
from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest, HttpResponseNotFound


class Products(GenericAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.all().order_by("category__name", "name")
    pagination_class = PageNumberPagination

    def get(self, request: Request, pk: int = None):
        if pk:
            products = get_object_or_404(Product, id=pk)
            serialized_objects = self.serializer_class(products)
        else:
            if "chat_id" not in request.query_params:
                return HttpResponseBadRequest("chat_id")
            family = Profile.objects.get(chat_id=request.query_params.get("chat_id")).family
            products = self.queryset.filter(family=family)
            if "page" in request.query_params:
                products = self.paginate_queryset(products)
            if request.query_params.get("category"):
                products = products.filter(category__name=request.query_params.get("category"))
            serialized_objects = self.serializer_class(products, many=True)
        if "page" in request.query_params:
            return self.get_paginated_response(serialized_objects.data)
        else:
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
        serialized = self.serializer_class(data=data)
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
        instance = self.queryset.get(id=pk)
        serialized = self.serializer_class(data=request.data, instance=instance, partial=True)
        serialized.is_valid(raise_exception=True)
        serialized.save()
        return Response(serialized.data)


class Users(GenericAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get(self, request: Request):
        try:
            user = self.queryset.get(profile__chat_id=request.query_params.get("chat_id"))
            return Response(self.serializer_class(user).data)
        except ObjectDoesNotExist:
            return Http404("No user found matching query")
