from django.contrib.auth.models import User
from django.db import models


# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=70)


class Keyword(models.Model):
    category = models.ForeignKey(to=Category, on_delete=models.CASCADE)
    keyword = models.CharField(max_length=50)


class Family(models.Model):
    created_by = models.ForeignKey(to=User, on_delete=models.SET_NULL)
    name = models.CharField(max_length=50)


class Profile(models.Model):
    chat_id = models.PositiveBigIntegerField()
    family = models.ForeignKey(to=Family, on_delete=models.SET_NULL)


class Product(models.Model):
    name = models.CharField()
    created_date = models.DateTimeField()
    created_by = models.ForeignKey(to=User, on_delete=models.SET_NULL)
    family = models.ForeignKey(to=Family, on_delete=models.CASCADE)