from threading import Thread
from django.db.utils import IntegrityError
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponseRedirect, HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from urllib.parse import quote_plus

from telebot.apihelper import ApiTelegramException

from .forms import RegistrationForm, LoginUserForm, ChangeUsernameForm
from .main import bot
from .models import *
from django.views.generic import ListView, CreateView, UpdateView, TemplateView


class ItemList(LoginRequiredMixin, ListView):
    login_url = reverse_lazy("login")
    model = Product
    template_name = "Items/index.html"

    def get_queryset(self):
        try:
            return self.model.objects.filter(family=self.request.user.profile.family)
        except Profile.DoesNotExist:
            self.request.user.profile = Profile()
            self.request.user.profile.save()
            return self.model.objects.filter(family=self.request.user.profile.family)

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
                context["invite_url"] = (
                    self.request.build_absolute_uri(reverse_lazy("invite"))
                    + "?token="
                    + quote_plus(self.request.user.profile.family.create_invite_token())
                )
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
        return super().form_invalid(form)


@login_required(login_url=reverse_lazy("login"))
def leave_family(request: HttpRequest):
    if request.user.profile.family:
        request.user.profile.family = None
        request.user.profile.save()
    return HttpResponseRedirect(reverse_lazy("profile"))


class InviteLink(LoginRequiredMixin, TemplateView):
    template_name = "Items/invite.html"

    def get(self, request: HttpRequest, *args, **kwargs):
        if "token" not in request.GET:
            return HttpResponse("No token provided", status=403)
        try:
            self.extra_context = {
                "family": Family.get_family_by_token(request.GET.get("token", default=None)),
                "user": request.user,
            }
        except PermissionError:
            return HttpResponse("Your invite link must be corrupted", status=403)
        return super().get(request, *args, **kwargs)

    def post(self, request):
        if "token" not in request.GET:
            return HttpResponse("No token provided", status=403)
        try:
            family = Family.get_family_by_token(request.GET.get("token", default=None))
            if int(self.request.POST.get("id")) != family.id:
                return HttpResponse("Form is invalid", status=403)
            request.user.profile.family = family
            request.user.profile.save()
        except PermissionError:
            return HttpResponse("Your invite link must be corrupted", status=403)
        return HttpResponseRedirect(reverse_lazy("profile"))


@login_required()
def link_telegram(request: WSGIRequest):
    if not request.GET.get("token"):
        return HttpResponse(f"Token is required, you can get one at t.me/{bot.user.username}")
    # try:
    request.user.profile.connect_telegram_by_token(request.GET.get("token"))
    try:
        request.user.profile.save()
    except IntegrityError:
        return HttpResponse("Ошибка сохранения. Возможно telegram привязан к другому аккаунту", status=400)
    return HttpResponse("OK")


def start_pooling():
    bot.remove_webhook()
    try:
        print(f"Pooling {bot.user.username}")
        bot.polling()
    except ApiTelegramException:
        return


def pooling(request):
    print(type(request))
    th = Thread(target=start_pooling)
    th.start()
    return HttpResponse("OK")
