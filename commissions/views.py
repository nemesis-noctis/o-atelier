from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import RadioSelect
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import View

from core.notifications import send_notification_to_artist, send_notification_to_client
from core.utils import get_landing_data, decrease_comms_slots
from . import forms
from . import models
from . import price_calculator

CALCULATORS = {"character": price_calculator.calculate_character_price,
               "landscape": price_calculator.calculate_landscape_price,
               "object": price_calculator.calculate_object_price
               }


def redirect_if_invalid_category(category):
    if category not in ["character", "landscape", "object"]:
        return redirect("comms_choice")


def set_required_fields_based_on_category(form, category):
    required_fields = {
        "character": ["character_type", "count", "art_type", "clothing", "body_type", "background"],
        "landscape": ["complexity"],
        "object": ["complexity", "count", "art_type", "background"]
    }

    for field_name, field_obj in zip(form.fields, form.fields.values()):
        if field_name in required_fields[category]:
            field_obj.required = True
    return form


# Create your views here.
def commission_choice(request):
    return render(request, "commissions/comms_choice.html", context={"landing_data": get_landing_data()})


class CommissionFormView(View):
    def comms_form_details_required_inverter(self, form, set_status):
        for field_name, field_obj in zip(form.fields, form.fields.values()):
            if field_name in ["description", "reference_images", "contact_social", "contact_username"]:
                field_obj.required = set_status
        return form

    def get(self, request):
        form = forms.CommissionForm()
        form_data = request.session.pop("form_data", None)
        category = request.GET.get("category", "")
        form = set_required_fields_based_on_category(form, category)

        redirect_if_invalid_category(category)
        form["category"].initial = category

        context = {
            "category": category,
            "landing_data": get_landing_data(),
        }

        if form_data:
            if form_data["category"] == category:
                form = forms.CommissionForm(form_data)
                required_details_form = self.comms_form_details_required_inverter(form, True)
                context["form"] = required_details_form
                context["calculated_price"] = request.session.pop("calculated_price", None)

        context["form"] = form

        return render(request, "commissions/comms_form_base.html", context=context)

    def post(self, request):
        form = forms.CommissionForm(request.POST, request.FILES)
        category = request.POST.get("category", None)
        redirect_if_invalid_category(category)

        optional_details_form = self.comms_form_details_required_inverter(form, False)
        form = optional_details_form
        form = set_required_fields_based_on_category(form, category)

        context = {
            "landing_data": get_landing_data(),
            "form": form,
        }

        if form.is_valid():
            form_data = form.cleaned_data

            price = CALCULATORS[category](form_data)
            request.session["calculated_price"] = price

            required_details_form = self.comms_form_details_required_inverter(form, True)
            form = required_details_form
            context["calculated_price"] = price
            context["category"] = category
            context["form"] = form

            return render(request, "commissions/comms_form_base.html", context=context)

        else:
            context["category"] = form.cleaned_data["category"]
            messages.error(request,
                           _("Ocorreu um erro com a sua solicitação, por favor verifique os campos do formulário e tente novamente"))
            return render(request, "commissions/comms_form_base.html", context=context)


@login_required()
def commission_confirmation(request):
    def get_human_readable_names(fields, form_data):
        readable_names = {}
        for field, data in zip(form.fields.values(), form_data):
            if isinstance(field.widget, RadioSelect):
                readable_names[data] = dict(field.choices).get(form_data[data])
            else:
                readable_names[data] = form_data[data]
        return readable_names

    if request.method == "POST" and get_landing_data().comms_status == True:
        form = forms.CommissionForm(request.POST, request.FILES)
        category = request.POST.get("category", None)
        redirect_if_invalid_category(category)

        form = set_required_fields_based_on_category(form, category)
        request.session["form_data"] = request.POST.dict()

        context = {
            "landing_data": get_landing_data()
        }

        if form.is_valid():
            form_data = form.cleaned_data

            form_readable_names = get_human_readable_names(form.fields.values(), form_data)

            price = CALCULATORS[category](form_data)
            context["calculated_price"] = price
            request.session.delete("calculated_price")

            images = request.FILES.getlist("reference_images", [])
            images_uuids = []
            if images != []:
                for image in images:
                    temp_image = models.ReferenceImage(image=image, is_temp=True)
                    images_uuids.append(str(temp_image.uuid))
                    temp_image.save()

            context["form_readable_names"] = form_readable_names
            context["reference_images_uuids"] = request.session["reference_images_uuids"] = images_uuids
            context["category"] = category
            return render(request, "commissions/comms_confirmation.html", context=context)

        else:
            message = _(
                "Ocorreu um erro com a sua solicitação, por favor verifique os campos do formulário e tente novamente"
            )

            messages.error(request, message)
            return redirect(f"{reverse_lazy("comms_form")}?{urlencode({"category": category})}")
    else:
        return redirect("comms_choice")


@login_required
def commission_success(request):
    if request.method == "POST" and get_landing_data().comms_status == True and (
            request.session.get("form_data", None) is not None):

        form = forms.CommissionForm(request.session.pop("form_data"))
        reference_images_uuids = request.session.pop("reference_images_uuids", [])

        if form.is_valid():
            form_data = form.cleaned_data
            prices = CALCULATORS[form_data["category"]](form_data)

            commission = form.save(commit=False)
            commission.user = request.user
            commission.stage = "waiting_confirmation"
            commission.price_brl = prices["brl"]
            commission.price_usd = prices["usd"]
            commission.save()

            if reference_images_uuids != []:
                for uuid in reference_images_uuids:
                    image = models.ReferenceImage.objects.get(uuid=uuid)
                    image.commission = commission
                    image.is_temp = False
                    image.save()

            artist_notification_context = {"client_name": request.user.username,
                                           "price_brl": commission.price_brl,
                                           "price_usd": commission.price_usd}

            send_notification_to_client(client=request.user, key="order_success", level="MESSAGE", context={})
            send_notification_to_artist(key="new_order", level="MESSAGE", context=artist_notification_context)
            decrease_comms_slots()

            return render(request, "commissions/comms_success.html", context={"landing_data": get_landing_data()})

        else:
            return redirect("comms_choice")
    else:
        return redirect("comms_choice")
