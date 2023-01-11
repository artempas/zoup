from django.contrib.auth.views import LogoutView
from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.helloworld),
]
