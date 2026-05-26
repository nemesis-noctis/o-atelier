from django.shortcuts import render


# Create your views here.
def index(request):
    return render(request, "landing/index.html")


def login(request):
    return render(request, "landing/login.html")


def register(request):
    return render(request, "landing/register.html")
