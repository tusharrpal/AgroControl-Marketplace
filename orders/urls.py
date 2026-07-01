from django.urls import path

from . import views


urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("", views.my_orders, name="my_orders"),
    path("received/", views.orders_received, name="orders_received"),
    path("<int:pk>/", views.order_detail, name="order_detail"),
    path("<int:pk>/cancel/", views.cancel_order, name="cancel_order"),
]
