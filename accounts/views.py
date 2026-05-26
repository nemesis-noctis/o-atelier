from django.contrib import messages
from django.contrib.auth import login as login_user
from django.shortcuts import render, redirect

from .forms import RegisterForm, LoginForm


# Create your views here.
def login(request):
    if request.method == "POST":
        form = LoginForm(request, request.POST)
        if form.is_valid():
            login_user(request, form.get_user())
            return redirect("landing-page")

        else:
            messages.error(request, "Email ou senha inválidos.")
            return render(request, "accounts/login.html", context={"form": form})

    form = LoginForm(request)
    return render(request, "accounts/login.html", context={"form": form})


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Sua conta foi criada com sucesso, prossiga com o login.")
            return redirect("login")
        else:
            return render(request, "accounts/register.html", context={"form": form})

    form = RegisterForm()
    return render(request, "accounts/register.html", context={"form": form})
