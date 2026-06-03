import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as login_user, logout as logout_user, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordResetDoneView, \
    PasswordResetCompleteView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from dotenv import load_dotenv

import accounts.forms as forms
from core.utils import redirect_if_logged, get_landing_data

load_dotenv(settings.BASE_DIR / ".env")


# Create your views here.

@login_required
def user_profile(request):
    if request.user.is_superuser == True:
        return render(request, "accounts/artist/artist_profile.html", context={"landing_data": get_landing_data()})

    else:
        return render(request, "accounts/clients/client_profile.html", context={"landing_data": get_landing_data()})


class ChangeAccountDataView(LoginRequiredMixin, View):
    login_url = reverse_lazy("login")

    def post(self, request):
        post_data = request.POST.copy()

        user_current_info = {
            "username": request.user.username,
            "email": request.user.email,
            "new_password1": post_data["old_password"],
        }

        for key, value in user_current_info.items():
            if post_data[key] == "":
                post_data[key] = value

        post_data["new_password2"] = post_data.get("new_password1", "")

        form = forms.EditAccountDataForm(request.user, post_data)
        if form.is_valid():
            data = form.cleaned_data
            request.user.username = data["username"]
            request.user.email = data["email"]
            request.user.save()
            form.save()

            user = authenticate(request, username=data["username"], password=data["new_password1"])
            login_user(request, user)

            messages.success(request, "Dados alterados com sucesso.")
            return render(request, "accounts/partials/change_account_data.html",
                          context={"form": form})

        else:
            print(form.cleaned_data)
            return render(request, "accounts/partials/change_account_data.html",
                          context={"form": form})

    def get(self, request):
        form = forms.EditAccountDataForm(user=request.user,
                                         initial={"username": request.user.username, "email": request.user.email})
        return render(request, "accounts/partials/change_account_data.html",
                      context={"form": form})


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
