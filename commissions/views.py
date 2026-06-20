from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import HiddenInput, RadioSelect
from django.shortcuts import render
from django.views.generic import View

from core.utils import get_landing_data
from . import forms
from . import price_calculator


# Create your views here.
@login_required(login_url="login")
def commission_choice(request):
    return render(request, "commissions/comms_choice.html", context={"landing_data": get_landing_data()})


class CommissionFormView(LoginRequiredMixin, View):
    def get(self, request, _type):
        form = forms.CommissionForm()
        context = {
            "type": _type,
            "landing_data": get_landing_data(),
            "form": form
        }
        return render(request, "commissions/comms_form_base.html", context=context)

    def post(self, request, _type):
        form = forms.CommissionForm(request.POST, request.FILES)
        context = {
            "type": _type,
            "landing_data": get_landing_data(),
            "form": form
        }
        if form.is_valid():
            form_data = form.cleaned_data
            calculators = {
                "character": price_calculator.calculate_character_price,
                "landscape": price_calculator.calculate_landscape_price,
                "object": price_calculator.calculate_object_price
            }
            if _type in calculators:
                price = calculators[_type](form_data)
                context["calculated_price"] = price
            return render(request, "commissions/comms_form_base.html", context=context)

        else:
            return render(request, "commissions/comms_form_base.html", context=context)


def commission_confirmation(request, _type):
    if request.method == "POST":
        form = forms.CommissionForm(request.POST, request.FILES)
        if form.is_valid():
            form_data = form.cleaned_data
            form_labels = {}
            for field, data in zip(form.fields.values(), form_data):
                if isinstance(field.widget, RadioSelect):
                    form_labels[data] = dict(field.choices).get(form_data[data])
                else:
                    form_labels[data] = form_data[data]

                field.widget = HiddenInput()
                field.initial = form_data[data]

            context = {
                "landing_data": get_landing_data(),
                "form": form,
                "form_labels": form_labels,
                "type": _type
            }
            return render(request, "commissions/comms_confirmation.html", context=context)
