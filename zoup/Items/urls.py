from os import environ
from dotenv import load_dotenv
from django.urls import path, include
from django.contrib.auth.views import LogoutView, PasswordChangeView
from django.urls import path
from . import views

urlpatterns = [
    path("", views.ItemList.as_view(), name="index"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("login/", views.LoginUser.as_view(), name="login"),
    path("register/", views.RegisterUser.as_view(), name="register"),
    path("check_item/", views.RegisterUser.as_view()),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("create_family/", views.CreateFamily.as_view(), name="create_family"),
    path("leave_family/", views.leave_family, name="leave_family"),
    path(
        "reset_password/", PasswordChangeView.as_view(template_name="Items/change_password.html"), name="reset_password"
    ),
    path("invite/", views.InviteLink.as_view(), name="invite"),
    path("api/", include("Items.api.urls")),
    path("link_telegram/", views.link_telegram, name='link_telegram'),
]
load_dotenv()
if environ.get("TEST_ENV"):
    urlpatterns.append(path("start_pooling", views.pooling))
