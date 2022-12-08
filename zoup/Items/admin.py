from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from Items.models import Product, Category, Family, Profile, Keyword


# Register your models here.
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "created_by", "family", "created_date")


admin.site.register(Product, ProductAdmin)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)


admin.site.register(Category, CategoryAdmin)


class FamilyAdmin(admin.ModelAdmin):
    list_display = ("name", "creator")


admin.site.register(Family, FamilyAdmin)


# which acts a bit like a singleton
class EmployeeInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "employee"


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (EmployeeInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class KeywordAdmin(admin.ModelAdmin):
    list_display = ("keyword", "category")


admin.site.register(Keyword, KeywordAdmin)
