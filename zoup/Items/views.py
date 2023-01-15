from django.contrib.auth import logout, login
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView, LoginView
from django.http import HttpResponseRedirect, HttpRequest
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy

from .forms import RegistrationForm, LoginUserForm, ChangeUsernameForm
from .models import *
from django.views.generic import ListView, CreateView, UpdateView


class ItemList(LoginRequiredMixin, ListView):
    login_url = reverse_lazy("login")
    model = Product
    template_name = "index.html"

    # def get_queryset(self):
    #     try:
    #         return self.model.objects.filter(family=self.request.user.profile.family)
    #     except Profile.DoesNotExist:
    #         self.request.user.profile = Profile()
    #         self.request.user.profile.save()
    #         return self.model.objects.filter(family=self.request.user.profile.family)

    def get_context_data(self, **kwargs):
        context = super(ItemList, self).get_context_data(**kwargs)
        context["user"] = self.request.user
        return context


class RegisterUser(CreateView):
    form_class = RegistrationForm
    template_name = "Items/register.html"
    success_url = ""

    def form_valid(self, form):
        user = form.save()
        user.profile = Profile()
        user.profile.save()
        login(self.request, user)
        return redirect("index")


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = "Items/login.html"

    def get_success_url(self):
        return reverse_lazy("profile")


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    login_url = reverse_lazy("login")
    template_name = "Items/profile.html"
    form_class = ChangeUsernameForm
    success_url = reverse_lazy("profile")

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        if self.request.user.profile.family:
            if self.request.user.profile.family.creator == self.request.user:
                context["invite_url"] = self.request.user.profile.family.create_invite_url()
        return context


class CreateFamily(LoginRequiredMixin, CreateView):
    template_name = "Items/create_family.html"
    model = Family
    fields = ["name"]

    def get_success_url(self):
        return reverse_lazy("profile")

    def form_valid(self, form):
        form.instance.creator = self.request.user
        family = form.save()
        self.request.user.profile.family = family
        self.request.user.profile.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)


@login_required(login_url=reverse_lazy("login"))
def leave_family(request: HttpRequest):
    if request.user.profile.family:
        request.user.profile.family = None
        request.user.profile.save()
    return HttpResponseRedirect(reverse_lazy("profile"))
