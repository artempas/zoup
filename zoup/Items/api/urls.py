from django.urls import path
from Items.api.views import Products, Users
from rest_framework.authtoken.views import obtain_auth_token

from . import views

urlpatterns = [
    path("products/", Products.as_view()),
    path("products/<int:pk>", Products.as_view()),
    path("users/", Products.as_view()),
    path("users", Users.as_view()),
]
