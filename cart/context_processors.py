from django.db.models import Sum

from users.models import User

from .models import CartItem


def cart_summary(request):
    if not request.user.is_authenticated or request.user.role != User.Role.BUYER:
        return {"cart_item_count": 0}

    count = (
        CartItem.objects.filter(cart__buyer=request.user)
        .aggregate(total=Sum("quantity"))["total"]
        or 0
    )
    return {"cart_item_count": count}
