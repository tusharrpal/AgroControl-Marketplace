from django.urls import path

from . import views


urlpatterns = [
    path("", views.farmer_dashboard, name="farmer_dashboard"),
    path("buyer/", views.buyer_dashboard, name="buyer_dashboard"),
    path("my-crops/", views.my_crops, name="my_crops"),
    path("add/", views.add_crop, name="add_crop"),
    path("edit/<int:pk>/", views.edit_crop, name="edit_crop"),
    path("delete/<int:pk>/", views.delete_crop, name="delete_crop"),
]
