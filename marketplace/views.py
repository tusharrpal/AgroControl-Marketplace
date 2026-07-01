from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Category, Product


def home(request):
    categories = Category.objects.all()
    products = (
        Product.objects.filter(is_available=True, quantity__gt=0)
        .select_related("category")
        .order_by("-created_at")[:8]
    )

    return render(request, "home.html", {
        "categories": categories,
        "products": products,
    })


def product_list(request):
    query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category", "").strip()
    products = (
        Product.objects.filter(is_available=True, quantity__gt=0)
        .select_related("category", "farmer")
        .order_by("-created_at")
    )

    if query:
        products = products.filter(name__icontains=query)

    if selected_category:
        products = products.filter(category_id=selected_category)

    paginator = Paginator(products, 9)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "marketplace/product_list.html", {
        "categories": Category.objects.all(),
        "page_obj": page_obj,
        "query": query,
        "selected_category": selected_category,
    })


def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.select_related("category", "farmer"),
        pk=pk,
        is_available=True,
    )
    return render(request, "marketplace/product_detail.html", {
        "product": product,
    })
