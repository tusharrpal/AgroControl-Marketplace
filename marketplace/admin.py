from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "category",
        "farmer",
        "price",
        "quantity",
        "unit",
        "is_available",
    )

    list_filter = (
        "category",
        "unit",
        "is_available",
        "is_organic",
    )

    search_fields = (
        "name",
        "location",
    )