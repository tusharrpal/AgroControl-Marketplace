from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class AgroControlUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("AgroControl", {"fields": ("role", "phone_number", "profile_photo")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("AgroControl", {"fields": ("role", "phone_number", "profile_photo")}),
    )
    list_display = UserAdmin.list_display + ("role",)
