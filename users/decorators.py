from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(*roles):
    """Require authentication and membership in one of the supplied user roles."""

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if request.user.role not in roles:
                messages.error(request, "You do not have permission to access that page.")
                return redirect("product_list")
            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator
