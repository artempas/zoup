from django.urls import path
from Items.api.views import Products, Users, bot_webhook

urlpatterns = [
    path("products/", Products.as_view()),
    path("products/<int:pk>", Products.as_view()),
    path("users/", Products.as_view()),
    path("users", Users.as_view()),
    path("bot_updates", bot_webhook),
]
