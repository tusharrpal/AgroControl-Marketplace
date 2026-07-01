from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from marketplace.models import Product
from users.decorators import role_required
from users.models import User

from .models import Cart, CartItem


def _buyer_cart(buyer):
    cart, _ = Cart.objects.get_or_create(buyer=buyer)
    return cart


@role_required(User.Role.BUYER)
def cart_detail(request):
    cart = _buyer_cart(request.user)
    items = cart.items.select_related("product", "product__category", "product__farmer")
    return render(request, "cart/cart_detail.html", {
        "cart": cart,
        "cart_items": items,
    })


@require_POST
@role_required(User.Role.BUYER)
@transaction.atomic
def add_to_cart(request, product_id):
    product = get_object_or_404(
        Product.objects.select_for_update(),
        pk=product_id,
        is_available=True,
    )
    if product.farmer_id == request.user.id:
        messages.error(request, "You cannot add your own product to the cart.")
        return redirect("product_detail", pk=product.pk)

    cart = _buyer_cart(request.user)
    item = CartItem.objects.select_for_update().filter(
        cart=cart,
        product=product,
    ).first()
    new_quantity = (item.quantity if item else 0) + 1
    if new_quantity > product.quantity:
        messages.error(request, "Requested quantity exceeds available stock.")
        return redirect("product_detail", pk=product.pk)

    if item:
        item.quantity = new_quantity
        item.save(update_fields=["quantity"])
    else:
        CartItem.objects.create(cart=cart, product=product, quantity=1)
    messages.success(request, "Added to cart.")
    return redirect("cart_detail")


@require_POST
@role_required(User.Role.BUYER)
def remove_item(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__buyer=request.user)
    item.delete()
    messages.success(request, "Removed from cart.")
    return redirect("cart_detail")


@require_POST
@role_required(User.Role.BUYER)
@transaction.atomic
def increase_quantity(request, item_id):
    item = get_object_or_404(
        CartItem.objects.select_for_update().select_related("product"),
        pk=item_id,
        cart__buyer=request.user,
    )
    product = Product.objects.select_for_update().get(pk=item.product_id)
    if not product.is_available or item.quantity + 1 > product.quantity:
        messages.error(request, "Requested quantity exceeds available stock.")
    else:
        item.quantity += 1
        item.save(update_fields=["quantity"])
        messages.success(request, "Quantity updated.")
    return redirect("cart_detail")


@require_POST
@role_required(User.Role.BUYER)
def decrease_quantity(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__buyer=request.user)
    if item.quantity == 1:
        item.delete()
        messages.success(request, "Removed from cart.")
    else:
        item.quantity -= 1
        item.save(update_fields=["quantity"])
        messages.success(request, "Quantity updated.")
    return redirect("cart_detail")


@require_POST
@role_required(User.Role.BUYER)
def clear_cart(request):
    cart = _buyer_cart(request.user)
    cart.items.all().delete()
    messages.success(request, "Cart cleared.")
    return redirect("cart_detail")
