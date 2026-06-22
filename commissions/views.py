from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import HiddenInput, RadioSelect
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import View

from core.utils import get_landing_data
from . import forms
from . import price_calculator


# Create your views here.
def commission_choice(request):
    return render(request, "commissions/comms_choice.html", context={"landing_data": get_landing_data()})


def redirect_if_invalid_category(category):
    if category not in ["character", "landscape", "object"]:
        return redirect("comms_choice")


class CommissionFormView(View):
    def get(self, request):
        form = forms.CommissionForm()
        form_data = request.session.pop("form_data", None)
        if form_data:
            form = forms.CommissionForm(form_data)

        category = request.GET.get("category", "")
        redirect_if_invalid_category(category)

        form["category"].initial = category
        context = {
            "type": category,
            "landing_data": get_landing_data(),
            "form": form
        }
        return render(request, "commissions/comms_form_base.html", context=context)

    def post(self, request):
        form = forms.CommissionForm(request.POST, request.FILES)
        category = request.POST.get("category", "none")

        redirect_if_invalid_category(category)

        context = {
            "type": category,
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

            if category in calculators:
                price = calculators[category](form_data)
                context["calculated_price"] = price

            return render(request, "commissions/comms_form_base.html", context=context)

        else:
            messages.error(request,
                           _("Ocorreu um erro com a sua solicitação, por favor verifique os campos do formulário e tente novamente"))
            return render(request, "commissions/comms_form_base.html", context=context)


@login_required()
def commission_confirmation(request):
    if request.method == "POST" and get_landing_data().comms_status == True:
        form = forms.CommissionForm(request.POST, request.FILES)
        category = request.POST.get("category", "none")

        redirect_if_invalid_category(category)

        context = {
            "landing_data": get_landing_data(),
            "form": form,
        }

        if form.is_valid():
            form_data = form.cleaned_data
            form_readable_names = {}
            for field, data in zip(form.fields.values(), form_data):
                if isinstance(field.widget, RadioSelect):
                    form_readable_names[data] = dict(field.choices).get(form_data[data])
                else:
                    form_readable_names[data] = form_data[data]

                field.widget = HiddenInput()
                field.initial = form_data[data]

            calculators = {
                "character": price_calculator.calculate_character_price,
                "landscape": price_calculator.calculate_landscape_price,
                "object": price_calculator.calculate_object_price
            }

            if category in calculators:
                price = calculators[form_data["category"]](form_data)
                context["calculated_price"] = price

            context["form_readable_names"] = form_readable_names
            context["type"] = category

            return render(request, "commissions/comms_confirmation.html", context=context)

        else:
            form_data = form.cleaned_data
            request.session["form_data"] = request.POST.dict()
            message = _(
                "Ocorreu um erro com a sua solicitação, por favor verifique os campos do formulário e tente novamente"
            )

            messages.error(request, message)
            return redirect(f"{reverse_lazy("comms_form")}?{urlencode({"category": category})}")
    else:
        return redirect("comms_choice")
