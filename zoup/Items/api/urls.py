from django.urls import path
from Items.api.views import Products
from rest_framework.authtoken.views import obtain_auth_token

from . import views

urlpatterns = [
    path("products", Products.as_view()),
    path("get_token", obtain_auth_token)
]
