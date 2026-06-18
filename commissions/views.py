from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import View

from core.utils import get_landing_data


# Create your views here.
@login_required(login_url="login")
def commission_choice(request):
    return render(request, "commissions/comms_choice.html", context={"landing_data": get_landing_data()})


class CommissionFormView(LoginRequiredMixin, View):
    def get(self, request, _type):
        context = {
            "type": _type,
            "landing_data": get_landing_data()
        }
        return render(request, "commissions/comms_form_base.html", context=context)
