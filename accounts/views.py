import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as login_user, logout as logout_user
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordResetDoneView, \
    PasswordResetCompleteView
from django.shortcuts import render, redirect
from dotenv import load_dotenv

import accounts.forms as forms
from core.utils import redirect_if_logged, get_landing_data

load_dotenv(settings.BASE_DIR / ".env")


# Create your views here.

@login_required
def user_profile(request):
    return render(request, "accounts/clients/client_profile.html", context={"landing_data": get_landing_data()})


def change_account_data_view(request):
    if request.method == "POST":
        form = forms.EditAccountInfoForm(request, request.POST)
        if form.is_valid():
            ...

        else:
            return render(request, "accounts/clients/partials/change_account_data.html", context={"form": form})

    form = forms.EditAccountInfoForm(user=request.user,
                                     initial={"username": request.user.username, "email": request.user.email})
    return render(request, "accounts/clients/partials/change_account_data.html", context={"form": form})


@redirect_if_logged
def login(request):
    if request.method == "POST":
        form = forms.LoginForm(request, request.POST)
        if form.is_valid():
            login_user(request, form.get_user())
            return redirect("landing-page")

        else:
            messages.error(request, "Email ou senha inválidos.")
            return render(request, "accounts/login.html", context={"form": form, "landing_data": get_landing_data()})

    form = forms.LoginForm(request)
    return render(request, "accounts/login.html", context={"form": form, "landing_data": get_landing_data()})


@redirect_if_logged
def register(request):
    if request.method == "POST":
        form = forms.RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Sua conta foi criada com sucesso, prossiga com o login.")
            return redirect("login")
        else:
            return render(request, "accounts/register.html", context={"form": form, "landing_data": get_landing_data()})

    form = forms.RegisterForm()
    return render(request, "accounts/register.html", context={"form": form, "landing_data": get_landing_data()})


def logout(request):
    logout_user(request)
    return redirect("landing-page")


class PasswordRecoverView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/emails/password_reset_email.txt"
    from_email = os.getenv("EMAIL_HOST")
    form_class = forms.RecoverPasswordEmailForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["landing_data"] = get_landing_data()
        return context


class PasswordRecoveryConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    form_class = forms.NewPasswordForm

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
