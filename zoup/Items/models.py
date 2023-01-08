from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save


# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=70, unique=True)

    def __str__(self):
        return self.name


class Keyword(models.Model):
    category = models.ForeignKey(to=Category, on_delete=models.CASCADE, related_name="get_keywords")
    keyword = models.CharField(max_length=50)

    def __repr__(self):
        return f"{self.keyword} ({self.category.name})"

    def __str__(self):
        return f"{self.keyword}"


class Family(models.Model):
    creator = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True, related_name="creator")
    name = models.CharField(max_length=50)

    def __repr__(self):
        if self.creator.username:
            return f"{self.name} created by {self.creator.username}"
        else:
            return f"{self.name} (creator was deleted)"

    def __str__(self):
        return self.name

    def delete_if_no_members_left(self):
        pass  # todo

    def get_members(self):
        pass  # todo


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    chat_id = models.PositiveBigIntegerField(null=True)
    family = models.ForeignKey(to=Family, on_delete=models.SET_NULL, null=True, related_name="get_members")

    def __str__(self):
        return f"Profile of user {self.user}"

    def __repr__(self):
        if self.family:
            return f"{self.user} has {self.chat_id} belongs to {self.family.name}"
        else:
            return f"{self.user} has {self.chat_id} doesn't belong to any family"


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


post_save.connect(create_user_profile, sender=User)


class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        to=Category, to_field="name", on_delete=models.SET_DEFAULT, null=False, default="Другое", related_name="get_products"
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

    def __repr__(self):
        if self.created_by:
            return f"{self.name} ({self.category}) was created by {self.created_by} at {self.created_date} for {self.family}"
        else:
            return f"{self.name} ({self.category}) was created by (creator deleted) at {self.created_date} for {self.family}"
