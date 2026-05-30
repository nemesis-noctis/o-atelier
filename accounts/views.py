import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as login_user
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordResetDoneView, \
    PasswordResetCompleteView
from django.shortcuts import render, redirect
from dotenv import load_dotenv

from core.utils import redirect_if_logged, get_landing_data
from .forms import RegisterForm, LoginForm, RecoverPasswordEmailForm, NewPasswordForm

load_dotenv(settings.BASE_DIR / ".env")


# Create your views here.

def user_profile(request, username):
    return render(request, "accounts/client_profile.html")


@redirect_if_logged
def login(request):
    if request.method == "POST":
        form = LoginForm(request, request.POST)
        if form.is_valid():
            login_user(request, form.get_user())
            return redirect("landing-page")

        else:
            messages.error(request, "Email ou senha inválidos.")
            return render(request, "accounts/login.html", context={"form": form, "landing_data": get_landing_data()})

    form = LoginForm(request)
    return render(request, "accounts/login.html", context={"form": form, "landing_data": get_landing_data()})


@redirect_if_logged
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Sua conta foi criada com sucesso, prossiga com o login.")
            return redirect("login")
        else:
            return render(request, "accounts/register.html", context={"form": form, "landing_data": get_landing_data()})

    form = RegisterForm()
    return render(request, "accounts/register.html", context={"form": form, "landing_data": get_landing_data()})


class PasswordRecoverView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/emails/password_reset_email.txt"
    from_email = os.getenv("EMAIL_HOST")
    form_class = RecoverPasswordEmailForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["landing_data"] = get_landing_data()
        return context


class PasswordRecoveryConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    form_class = NewPasswordForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["landing_data"] = get_landing_data()
        return context


class PasswordRecoveryDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["landing_data"] = get_landing_data()
        return context


class PasswordRecoveryCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["landing_data"] = get_landing_data()
        return context
