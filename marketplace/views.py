from django.shortcuts import render
from .models import Category, Product


def home(request):
    categories = Category.objects.all()
    products = Product.objects.filter(is_available=True).order_by("-created_at")[:8]

    return render(request, "home.html", {
        "categories": categories,
        "products": products,
    })