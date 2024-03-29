from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.contrib.auth.models import User
from django import forms


class RegistrationForm(UserCreationForm):
    username = forms.CharField(
        label="Имя пользователя",
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg"}),
    )
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-lg"}),
    )
    password2 = forms.CharField(
        label="Повтор пароля",
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-lg"}),
    )

    class Meta:
        model = User
        fields = ("username", "password1", "password2")


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label="Логин", widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={"class": "form-control"}))


class ChangeUsernameForm(UserChangeForm):
    class Meta:
        model = User
        fields = ["username"]


# class CreateFamilyForm(forms.ModelForm)
