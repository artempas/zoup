from django.contrib.auth import logout, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView, LoginView
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy

from .forms import RegistrationForm, LoginUserForm
from .models import *
from django.views.generic import ListView, CreateView, DeleteView, UpdateView


class ItemList(LoginRequiredMixin, ListView):
    login_url = "/admin"
    model = Product
    template_name = "index.html"

    def get_queryset(self):
        try:
            return self.model.objects.filter(family=self.request.user.profile.family)
        except Profile.DoesNotExist:
            self.request.user.profile=Profile()
            self.request.user.profile.save()
            self.request.user.save()
            return self.model.objects.filter(family=self.request.user.profile.family)
    def get_context_data(self, **kwargs):
        context = super(ItemList, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


def login_user(request):
    return HttpResponseRedirect(reverse("admin"))


class RegisterUser(CreateView):
    form_class = RegistrationForm
    template_name = "Items/register.html"
    success_url = ""

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect("index")


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = "Items/login.html"

    def get_success_url(self):
        return reverse_lazy("index")


class ProfileView(UpdateView):
    pass