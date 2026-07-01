from django.urls import path

from . import views


urlpatterns = [
    path("", views.cart_detail, name="cart_detail"),
    path("add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("remove/<int:item_id>/", views.remove_item, name="remove_cart_item"),
    path("increase/<int:item_id>/", views.increase_quantity, name="increase_cart_item"),
    path("decrease/<int:item_id>/", views.decrease_quantity, name="decrease_cart_item"),
    path("clear/", views.clear_cart, name="clear_cart"),
]
