from django.shortcuts import redirect


def redirect_if_logged(func):
    """Redirect to 'landing-page' route if user is logged."""

    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("landing-page")
        return func(request, *args, **kwargs)

    return wrapper
