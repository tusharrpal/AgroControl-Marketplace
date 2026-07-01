from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from .decorators import role_required
from .forms import (
    CropForm,
    LoginForm,
    ProfileForm,
    ProfilePasswordChangeForm,
    RegistrationForm,
)
from .models import User
from cart.models import Cart, CartItem
from marketplace.models import Product
from orders.models import Order, OrderItem


def _destination_for(user):
    if user.is_superuser or user.role == User.Role.ADMIN:
        return reverse("admin:index")
    if user.role == User.Role.FARMER:
        return reverse("farmer_dashboard")
    return reverse("product_list")


def register(request, role):
    if request.user.is_authenticated:
        return redirect("role_redirect")

    role_map = {
        "buyer": User.Role.BUYER,
        "farmer": User.Role.FARMER,
    }
    selected_role = role_map.get(role)
    if selected_role is None:
        return redirect("buyer_register")

    if request.method == "POST":
        form = RegistrationForm(request.POST, role=selected_role)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to AgroControl, {user.first_name or user.username}!")
            return redirect(_destination_for(user))
    else:
        form = RegistrationForm(role=selected_role)

    return render(request, "users/register.html", {
        "form": form,
        "account_type": selected_role.label,
        "role": role,
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect("role_redirect")

    next_url = request.POST.get("next") or request.GET.get("next")
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect(_destination_for(user))
    else:
        form = LoginForm(request)

    return render(request, "users/login.html", {"form": form, "next": next_url})


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("home")


@login_required
def role_redirect(request):
    return redirect(_destination_for(request.user))


@login_required
def profile(request):
    context = {}
    if request.user.role == User.Role.BUYER:
        context.update({
            "orders_count": Order.objects.filter(buyer=request.user).count(),
            "cart_items_count": (
                CartItem.objects.filter(cart__buyer=request.user)
                .aggregate(total=Sum("quantity"))["total"]
                or 0
            ),
        })
    elif request.user.role == User.Role.FARMER:
        received_items = OrderItem.objects.filter(farmer=request.user).exclude(
            order__status=Order.Status.CANCELLED,
        )
        context.update({
            "products_count": Product.objects.filter(farmer=request.user).count(),
            "orders_received_count": received_items.values("order_id").distinct().count(),
            "products_sold": received_items.aggregate(total=Sum("quantity"))["total"] or 0,
        })
    return render(request, "users/profile.html", context)


@login_required
def edit_profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile was updated successfully.")
            return redirect("profile")
        messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password(request):
    if request.method == "POST":
        form = ProfilePasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was changed successfully.")
            return redirect("profile")
        messages.error(request, "Please correct the password errors below.")
    else:
        form = ProfilePasswordChangeForm(request.user)
    return render(request, "users/change_password.html", {"form": form})


@role_required(User.Role.FARMER)
def farmer_dashboard(request):
    crops = Product.objects.filter(farmer=request.user)
    received_items = OrderItem.objects.filter(farmer=request.user).exclude(
        order__status=Order.Status.CANCELLED,
    )
    return render(request, "users/dashboard.html", {
        "total_crops": crops.count(),
        "available_crops": crops.filter(is_available=True, quantity__gt=0).count(),
        "out_of_stock_crops": crops.filter(quantity=0).count(),
        "orders_received_count": received_items.values("order_id").distinct().count(),
        "products_sold": received_items.aggregate(total=Sum("quantity"))["total"] or 0,
        "recent_products": crops.select_related("category").order_by("-created_at")[:5],
        "recent_orders": received_items.select_related(
            "order",
            "order__buyer",
            "product",
        ).order_by("-order__created_at")[:5],
    })


@role_required(User.Role.BUYER)
def buyer_dashboard(request):
    cart = (
        Cart.objects.filter(buyer=request.user)
        .prefetch_related("items", "items__product")
        .first()
    )
    return render(request, "users/buyer_dashboard.html", {
        "recent_orders": Order.objects.filter(buyer=request.user).prefetch_related("items")[:5],
        "orders_count": Order.objects.filter(buyer=request.user).count(),
        "cart_items_count": (
            CartItem.objects.filter(cart__buyer=request.user)
            .aggregate(total=Sum("quantity"))["total"]
            or 0
        ),
        "cart_total": cart.grand_total if cart else 0,
    })


@role_required(User.Role.FARMER)
def my_crops(request):
    crops = (
        Product.objects.filter(farmer=request.user)
        .select_related("category")
        .order_by("-created_at")
    )
    return render(request, "users/my_crops.html", {"crops": crops})


@role_required(User.Role.FARMER)
def add_crop(request):
    if request.method == "POST":
        form = CropForm(request.POST, request.FILES)
        if form.is_valid():
            crop = form.save(commit=False)
            crop.farmer = request.user
            crop.save()
            messages.success(request, f"{crop.name} was added successfully.")
            return redirect("my_crops")
    else:
        form = CropForm()
    return render(request, "users/add_crop.html", {"form": form})


@role_required(User.Role.FARMER)
def edit_crop(request, pk):
    crop = get_object_or_404(Product, pk=pk, farmer=request.user)
    if request.method == "POST":
        form = CropForm(request.POST, request.FILES, instance=crop)
        if form.is_valid():
            form.save()
            messages.success(request, f"{crop.name} was updated successfully.")
            return redirect("my_crops")
    else:
        form = CropForm(instance=crop)
    return render(request, "users/edit_crop.html", {"form": form, "crop": crop})


@role_required(User.Role.FARMER)
@require_http_methods(["GET", "POST"])
def delete_crop(request, pk):
    crop = get_object_or_404(Product, pk=pk, farmer=request.user)
    if request.method == "POST":
        name = crop.name
        crop.delete()
        messages.success(request, f"{name} was deleted successfully.")
        return redirect("my_crops")
    return render(request, "users/delete_crop.html", {"crop": crop})
