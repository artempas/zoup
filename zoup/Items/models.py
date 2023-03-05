from django.contrib.auth.models import User
from django.db import models
from django.http import Http404
from django.db.models.signals import post_save, post_delete
from django.shortcuts import get_object_or_404
from jwt import encode, decode
from jwt.exceptions import InvalidTokenError
from os import environ
from pymorphy2 import MorphAnalyzer


# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=70, unique=True)

    def __str__(self):
        return self.name


class Keyword(models.Model):
    category = models.ForeignKey(to=Category, on_delete=models.CASCADE, related_name="keywords")
    keyword = models.CharField(max_length=50)

    def __repr__(self):
        return f"{self.keyword} ({self.category.name})"

    def __str__(self):
        return f"{self.keyword}"


class Family(models.Model):
    creator = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True, related_name="creator")
    name = models.CharField(max_length=50)

    def create_invite_token(self) -> str:
        return encode(
            {"id": self.id, "name": self.name, "creator_id": self.creator_id},
            algorithm="HS256",
            key=environ["settings_token"],
        )

    @staticmethod
    def get_family_by_token(token: str) -> "Family":
        try:
            params = decode(token, environ["settings_token"], algorithms="HS256")
        except InvalidTokenError:
            raise PermissionError("Token is invalid")
        return get_object_or_404(Family, **params)

    def __repr__(self):
        if self.creator.username:
            return f"{self.name} created by {self.creator.username}"
        else:
            return f"{self.name} (creator was deleted)"

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    chat_id = models.PositiveBigIntegerField(blank=True, null=True)
    telegram_name = models.CharField(blank=True, max_length=255, null=True)  # telegram name contains
    _family = models.ForeignKey(to=Family, on_delete=models.SET_NULL, null=True, blank=True, related_name="members")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__old_family = None

    @property
    def family(self):
        return self._family

    @family.setter
    def family(self, value: Family):
        if self.__old_family is None:
            self.__old_family = self._family
        self._family = value

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.__old_family:
            if not Profile.objects.filter(_family=self.__old_family).count():
                self.__old_family.delete()
        self.__old_family = None

    def __str__(self):
        return f"Profile of user {self.user}"

    def __repr__(self):
        if self.family:
            return f"{self.user} has {self.chat_id} belongs to {self.family.name}"
        else:
            return f"{self.user} has {self.chat_id} doesn't belong to any family"


# noinspection PyUnusedLocal
def delete_if_no_members_left(sender, instance: Profile, *args, **kwargs):
    if not Profile.objects.filter(family=instance.family).count():
        instance.family.delete()


post_delete.connect(delete_if_no_members_left, Profile)


# noinspection PyUnusedLocal
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


post_save.connect(create_user_profile, sender=User)


class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        to=Category,
        to_field="name",
        on_delete=models.SET_DEFAULT,
        null=False,
        default="Другое",
        related_name="get_products",
    )
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="get_created_products",
    )
    family = models.ForeignKey(to=Family, on_delete=models.CASCADE, related_name="get_products")
    to_notify = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name}"

    @staticmethod
    def determine_category(name) -> Category:
        morph = MorphAnalyzer()
        for word in name.split():
            parsed = morph.parse(word)
            if not parsed:
                continue
            try:
                normalized = parsed[0].normal_form.lower()
            except Exception as e:
                print(e)  # TODO Logging
                continue
            else:
                try:
                    return Keyword.objects.get(keyword__iexact=normalized).category
                except Keyword.DoesNotExist:
                    continue
        return Category.objects.get(name="Другое")

    def __repr__(self):
        if self.created_by:
            return f"{self.name} ({self.category}) was created by {self.created_by} at {self.created_date} for {self.family}"
        else:
            return f"{self.name} ({self.category}) was created by (creator deleted) at {self.created_date} for {self.family}"
