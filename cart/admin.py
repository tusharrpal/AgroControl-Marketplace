from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("buyer", "created_at", "updated_at")
    search_fields = ("buyer__username", "buyer__email")
    inlines = (CartItemInline,)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("product", "cart", "quantity", "created_at")
    list_select_related = ("cart__buyer", "product")
