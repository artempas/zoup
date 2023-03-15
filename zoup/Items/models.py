import io
import re
from traceback import print_exc

from django.contrib.auth.models import User
from django.db import models
from .main import bot, notify
from django.db.models.signals import post_save, post_delete
from django.shortcuts import get_object_or_404
from jwt import encode, decode
from jwt.exceptions import InvalidTokenError
from telebot.types import InlineKeyboardButton
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
    chat_id = models.PositiveBigIntegerField(blank=True, null=True, unique=True)
    telegram_name = models.CharField(blank=True, max_length=255, null=True)  # telegram username contains @
    _family = models.ForeignKey(to=Family, on_delete=models.SET_NULL, null=True, blank=True, related_name="members")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__old_family = None

    @property
    def telegram_link(self):
        return self.chat_id

    @telegram_link.setter
    def telegram_link(self, value):
        bot.send_message(value, f"Telegram привязан к аккаунту {self.user.username}")
        self.chat_id = value

    @staticmethod
    def create_login_token(chat_id: int, username: str) -> str:
        """
        Generate token for url log in
        @param chat_id:
        @param username: with @ if username
        @return:
        """
        return encode(
            {"chat_id": chat_id, "username": username},
            algorithm="HS256",
            key=environ["settings_token"],
        )

    def connect_telegram_by_token(self, token) -> None | int:
        try:
            params = decode(token, environ["settings_token"], algorithms="HS256")
        except InvalidTokenError:
            raise PermissionError("Token is invalid")
        self.telegram_link = params.get("chat_id")
        self.telegram_name = params.get("username")
        return self.telegram_link

    @property
    def family(self):
        return self._family

    @family.setter
    def family(self, value: Family):
        if self.__old_family is None:
            self.__old_family = self._family
        self._family = value
        notify(
            f"{self.user.username} присоединяется к семье",
            [i.chat_id for i in self.family.members.all() if i.chat_id and i.chat_id != self.chat_id],
        )
        if self.chat_id:
            bot.send_message(self.chat_id, f"Теперь вы в семье {self.family.name}")

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
    message_id = models.IntegerField(blank=True)

    @classmethod
    def from_message(cls, name: str, created_by: User, message_id: int):
        to_notify = "срочно" in name.lower()
        if to_notify:
            name = re.compile("срочно", re.IGNORECASE | re.UNICODE).sub("", name)
        return cls(
            name=name,
            category=cls.determine_category(name),
            created_by=created_by,
            family=created_by.profile.family,
            to_notify=to_notify,
            message_id=message_id,
        )

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
                print_exc()
                continue
            else:
                try:
                    return Keyword.objects.get(keyword__iexact=normalized).category
                except Keyword.DoesNotExist:
                    continue
        return Category.objects.get_or_create(name="Другое")[0]

    def to_button(self, page: int):
        return InlineKeyboardButton(
            f"✅❗️{self.name}❗️" if self.to_notify else f"✅{self.name}", callback_data=f"p&{self.id}&{page}"
        )

    def __repr__(self):
        if self.created_by:
            return f"{self.name} ({self.category}) was created by {self.created_by} at {self.created_date} for {self.family}"
        else:
            return f"{self.name} ({self.category}) was created by (creator deleted) at {self.created_date} for {self.family}"

    def to_string(self) -> str:
        if self.to_notify:
            if self.created_by:
                if self.created_by.profile.chat_id:
                    return f'❗️ {self.name} (<a href="tg://user?id={self.created_by.profile.chat_id}">{self.created_by.username}</a>)'
                else:
                    return f"❗️ {self.name} ({self.created_by.username})"
            else:
                return f"❗️ {self.name}"
        else:
            if self.created_by:
                if self.created_by.profile.chat_id:
                    return f'🔘 {self.name} (<a href="tg://user?id={self.created_by.profile.chat_id}">{self.created_by.username}</a>)'
                else:
                    return f"🔘 {self.name} ({self.created_by.username})"
            else:
                return f"🔘 {self.name}"

    def delete(self, using=None, keep_parents=False):
        if self.to_notify:
            morph = MorphAnalyzer()
            first_noun = None
            text = ""
            for word in self.name.split():
                if morph.parse(word)[0].tag.POS == "NOUN":
                    first_noun = word
                    break
            if first_noun is None:
                text = f"{self.name} удален(a) из списка"
            else:
                parsed = morph.parse(first_noun)[0]
                inflect_to = {"plur"} if parsed.tag.number == "plur" else {parsed.tag.gender}
                if parsed.tag.gender is None:
                    text = f"{self.name} удален(a) из списка"
                else:
                    text = f"{self.name} {morph.parse('куплено')[0].inflect(inflect_to).word}"
            notify(text, [i.chat_id for i in self.family.members.all()])
        return super().delete(using, keep_parents)


def notify_if_needed(sender, instance, created, **kwargs):
    if instance.to_notify and created:
        morph = MorphAnalyzer()
        name = io.StringIO()
        for word in instance.name.split():
            if morph.parse(word)[0].tag.POS == "NOUN":
                name.write(morph.parse(word)[0].inflect({"accs"}).word)
        if instance.created_by.profile.chat_id:
            text = f'<a href="tg://user?id={instance.created_by.profile.chat_id}">{instance.created_by.username}</a> срочно просит купить {name.getvalue()}'
        else:
            text = f"{instance.created_by.username} срочно просит купить {name.getvalue()}"
        notify(text, [i.chat_id for i in instance.family.members.all() if i.chat_id and i != instance.created_by.profile])


post_save.connect(notify_if_needed, sender=Product)
