from django.shortcuts import redirect

from landing.models import LandingPage


def redirect_if_logged(func):
    """Redirect to 'landing-page' route if user is logged."""

    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("landing-page")
        return func(request, *args, **kwargs)

    return wrapper


def get_landing_data():
    data = LandingPage.objects.all()[0]
    return data
