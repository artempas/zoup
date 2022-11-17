from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("", views.ItemList.as_view(), name="index"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("login", views.login, name="login"),
]
