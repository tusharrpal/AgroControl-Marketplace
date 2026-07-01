from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "farmer", "quantity", "price_at_purchase")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "buyer", "status", "total_amount", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("buyer__username", "buyer__email")
    readonly_fields = ("buyer", "total_amount", "created_at", "updated_at")
    inlines = (OrderItemInline,)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "product",
        "farmer",
        "quantity",
        "price_at_purchase",
    )
    list_select_related = ("order", "product", "farmer")
    readonly_fields = (
        "order",
        "product",
        "farmer",
        "quantity",
        "price_at_purchase",
    )
