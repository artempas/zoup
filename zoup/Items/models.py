from django.contrib.auth.models import User
from django.db import models


# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=70)

    def __str__(self):
        return self.name


class Keyword(models.Model):
    category = models.ForeignKey(to=Category, on_delete=models.CASCADE)
    keyword = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.keyword} ([{self.category}]{self.category.name}"


class Family(models.Model):
    created_by = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=50)
    def __str__(self):
        return f"{self.name} created by {self.created_by.name}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    chat_id = models.PositiveBigIntegerField()
    family = models.ForeignKey(to=Family, on_delete=models.SET_NULL, null=True)
    def __str__(self):
        return f"{self.user} has {self.chat_id} belongs to {self.family.name}"


class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(to=Category, on_delete=models.SET_NULL, null=True)
    created_date = models.DateTimeField()
    created_by = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True)
    family = models.ForeignKey(to=Family, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.name} ({self.category}) was created by {self.created_by} at {self.created_date} for {self.family}'
