from django.shortcuts import render

from core.utils import get_landing_data


# Create your views here.
def index(request):
    return render(request, "landing/index.html", context={"data": get_landing_data()})
