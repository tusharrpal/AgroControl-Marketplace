from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("marketplace/", views.product_list, name="product_list"),
    path("marketplace/<int:pk>/", views.product_detail, name="product_detail"),
]
