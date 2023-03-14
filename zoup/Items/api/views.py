import re

import telebot.types
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from Items.api.serializers import *
from Items.main import bot
from Items.models import *
from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest, HttpResponseNotFound, HttpRequest, HttpResponse, Http404


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
            family = get_object_or_404(Profile, chat_id=request.query_params["chat_id"]).family
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
        if "chat_id" not in request.query_params:
            return HttpResponseBadRequest("chat_id")
        data = request.data
        if "category" not in data:
            data["category"] = Product.determine_category(data.get("name"))
        if "to_notify" not in data:
            try:
                data["to_notify"] = "срочно" in data["name"]
                data["name"] = re.compile("срочно", re.IGNORECASE | re.UNICODE).sub("", data["name"])
            except KeyError:  # if name is not in data serializer is responsible to send error
                pass
        usr = get_object_or_404(User, profile__chat_id=request.query_params["chat_id"])
        data["user_id"] = usr.id
        if not usr.profile.family:
            return HttpResponseNotFound("Family not found")
        data["family"] = usr.profile.family.id
        print(data)
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
        filter_by["family"] = get_object_or_404(Profile, request.data["chat_id"])
        del filter_by["chat_id"]
        objects_to_delete = Product.objects.filter(**filter_by)
        deleted = len(objects_to_delete)
        objects_to_delete.delete()
        return Response({"deleted": deleted})

    def put(self, request: Request, pk: int):
        if not pk:
            return HttpResponseBadRequest("Update without slug is not implemented")
        instance = self.queryset.get(id=pk)
        data = request.data
        if "category" not in data:
            data["category"] = Product.determine_category(data.get("name"))
        serialized = self.serializer_class(data=data, instance=instance, partial=True)
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


@csrf_exempt
def bot_webhook(request: WSGIRequest):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != environ.get("WEBHOOK_SECRET_KEY"):
        return HttpResponse("Unauthorized", status=403)
    update = telebot.types.Update.de_json(request.body.decode())
    bot.process_new_updates([update])
    return HttpResponse("OK")
