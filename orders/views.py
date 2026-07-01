from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cart.models import Cart
from marketplace.models import Product
from users.decorators import role_required
from users.models import User

from .models import Order, OrderItem


@require_POST
@role_required(User.Role.BUYER)
@transaction.atomic
def checkout(request):
    cart = (
        Cart.objects.select_for_update()
        .filter(buyer=request.user)
        .first()
    )
    if cart is None:
        messages.error(request, "Your cart is empty.")
        return redirect("cart_detail")

    cart_items = list(
        cart.items.select_for_update()
        .select_related("product", "product__farmer")
        .order_by("product_id")
    )
    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect("cart_detail")

    product_ids = [item.product_id for item in cart_items]
    products = {
        product.pk: product
        for product in Product.objects.select_for_update()
        .filter(pk__in=product_ids)
        .order_by("pk")
    }

    for item in cart_items:
        product = products.get(item.product_id)
        if (
            product is None
            or not product.is_available
            or item.quantity > product.quantity
        ):
            messages.error(
                request,
                f"{item.product.name} is out of stock or has insufficient quantity.",
            )
            return redirect("cart_detail")

    total = sum(
        (products[item.product_id].price * item.quantity for item in cart_items),
        Decimal("0.00"),
    )
    order = Order.objects.create(buyer=request.user, total_amount=total)
    OrderItem.objects.bulk_create([
        OrderItem(
            order=order,
            product=products[item.product_id],
            farmer=products[item.product_id].farmer,
            quantity=item.quantity,
            price_at_purchase=products[item.product_id].price,
        )
        for item in cart_items
    ])

    for item in cart_items:
        product = products[item.product_id]
        product.quantity -= item.quantity
        if product.quantity == 0:
            product.is_available = False
        product.save(update_fields=["quantity", "is_available", "updated_at"])

    cart.items.all().delete()
    messages.success(request, "Order placed successfully.")
    return redirect("order_detail", pk=order.pk)


@role_required(User.Role.BUYER)
def my_orders(request):
    orders = (
        Order.objects.filter(buyer=request.user)
        .prefetch_related("items", "items__product")
    )
    return render(request, "orders/my_orders.html", {"orders": orders})


@role_required(User.Role.BUYER)
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items",
            "items__product",
            "items__farmer",
        ),
        pk=pk,
        buyer=request.user,
    )
    return render(request, "orders/order_detail.html", {"order": order})


@role_required(User.Role.FARMER)
def orders_received(request):
    received_items = (
        OrderItem.objects.filter(farmer=request.user)
        .select_related("order", "order__buyer", "product")
        .order_by("-order__created_at", "pk")
    )
    return render(request, "orders/orders_received.html", {
        "received_items": received_items,
    })


@require_POST
@role_required(User.Role.BUYER)
@transaction.atomic
def cancel_order(request, pk):
    order = get_object_or_404(
        Order.objects.select_for_update().prefetch_related("items"),
        pk=pk,
        buyer=request.user,
    )
    if order.status != Order.Status.PENDING:
        messages.error(request, "Only pending orders can be cancelled.")
        return redirect("order_detail", pk=order.pk)

    items = list(order.items.all())
    product_ids = [item.product_id for item in items if item.product_id is not None]
    products = {
        product.pk: product
        for product in Product.objects.select_for_update()
        .filter(pk__in=product_ids)
        .order_by("pk")
    }
    for item in items:
        if item.product_id is None:
            continue
        product = products[item.product_id]
        product.quantity += item.quantity
        product.is_available = True
        product.save(update_fields=["quantity", "is_available", "updated_at"])

    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status", "updated_at"])
    messages.success(request, "Order cancelled.")
    return redirect("order_detail", pk=order.pk)

# Create your views here.
