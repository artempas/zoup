from django.contrib.auth import logout, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse

from .models import *
from django.views.generic import ListView, CreateView


class ItemList(LoginRequiredMixin, ListView):
    login_url = "/admin"
    model = Product
    template_name = "index.html"

    def get_queryset(self):
        return self.model.objects.filter(family=self.request.user.profile.family)


def login_user(request):
    return HttpResponseRedirect(reverse("admin"))


class RegisterUser(CreateView):
    form_class = UserCreationForm
    template_name = "items/register.html"
    success_url = ""

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect("index")
