from django.urls import path

from . import views


urlpatterns = [
    path("register/buyer/", views.register, {"role": "buyer"}, name="buyer_register"),
    path("register/farmer/", views.register, {"role": "farmer"}, name="farmer_register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("redirect/", views.role_redirect, name="role_redirect"),
    path("farmer/dashboard/", views.farmer_dashboard, name="farmer_dashboard"),
]
