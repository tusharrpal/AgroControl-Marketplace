from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .decorators import role_required
from .forms import LoginForm, RegistrationForm
from .models import User


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


@role_required(User.Role.FARMER)
def farmer_dashboard(request):
    return render(request, "users/farmer_dashboard_placeholder.html")
