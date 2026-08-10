import json
import os
import uuid as uuid_pkg
from urllib.parse import urlencode

import mercadopago
import requests
import requests.exceptions as req_execept
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db import transaction, IntegrityError
from django.forms import RadioSelect
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from mercadopago.webhook import WebhookSignatureValidator, InvalidWebhookSignatureError

from chat.models import Message
from core.notifications import send_notification_to_artist, send_notification_to_client
from core.utils import get_landing_data, decrease_comms_slots
from . import forms
from . import models
from . import price_calculator
from .forms import CommissionForm
from .models import Commission, ProgressImage

CALCULATORS = {"character": price_calculator.calculate_character_price,
               "landscape": price_calculator.calculate_landscape_price,
               "object": price_calculator.calculate_object_price
               }


def set_required_fields_based_on_category(form: CommissionForm, category: str) -> CommissionForm:
    required_fields = {
        "character": ["character_type", "count", "art_type", "clothing", "body_type", "background"],
        "landscape": ["complexity"],
        "object": ["complexity", "count", "art_type", "background"]
    }

    for field_name, field_obj in zip(form.fields, form.fields.values()):
        if field_name in required_fields[category]:
            field_obj.required = True
    return form


def get_paypal_auth_data():
    auth_url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
    try:
        auth_response = requests.post(auth_url, headers={"Content-Type": "application/x-www-form-urlencoded"},
                                      auth=(os.getenv("PayPal_ClientId"), os.getenv("PayPal_ClientSecret")),
                                      data={"grant_type": "client_credentials"},
                                      timeout=10)
        auth_response.raise_for_status()
    except req_execept.ConnectTimeout, req_execept.ConnectionError, req_execept.HTTPError:
        return None

    return auth_response.json()


# Create your views here.

def terms_of_service(request, read_again) -> HttpResponseRedirect | HttpResponse:
    tos_already_seen = request.session.get("tos_already_seen", False)

    if read_again:
        pass
    elif tos_already_seen:
        return redirect("comms_choice")
    else:
        request.session["tos_already_seen"] = True

    return render(request, "commissions/terms_of_service.html",
                  context={"landing_data": get_landing_data(), "read_again": read_again})


def paypal_capture_order(request) -> JsonResponse:
    auth_data = get_paypal_auth_data()
    if not auth_data:
        return JsonResponse(json.dumps({"auth_error": "auth request failed."}))

    data = json.loads(request.body)
    order_id = data["orderId"]

    url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture"
    headers = {
        "Content-Type": "application/json",
        "PayPal-Request-Id": f"{uuid_pkg.uuid4()}",
        "Authorization": f"{auth_data.get("token_type")} {auth_data.get("access_token")}",
    }

    try:
        response = requests.post(url, headers=headers, timeout=10)
    except req_execept.ConnectTimeout, req_execept.ConnectionError:
        return JsonResponse(json.dumps({"capture_error": "capture order request failed."}))

    return JsonResponse(response.json())


def paypal_create_order(request) -> JsonResponse:
    comm_uuid = json.loads(request.body).get("comm_uuid", "")
    try:
        commission: Commission = request.user.commissions.get(uuid=comm_uuid)
    except Commission.DoesNotExist:
        return JsonResponse(json.dumps({"comm_error": "commission uuid not found"}))

    amount = round(commission.price_usd / 2, 2)

    if not commission.stage in ["waiting_deposit_payment", "waiting_full_payment"]:
        return JsonResponse(json.dumps({"stage_error": "comm not in any payment stage."}))

    auth_data = get_paypal_auth_data()
    if not auth_data:
        return JsonResponse(json.dumps({"auth_error": "auth request failed."}))

    url = "https://api-m.sandbox.paypal.com/v2/checkout/orders"

    invoice_prefix = "deposit" if commission.stage == "waiting_deposit_payment" else "full"
    body = {
        "intent": "CAPTURE",
        "payment_source": {
            "paypal": {
                "experience_context": {
                    "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
                    "landing_page": "NO_PREFERENCE",
                    "shipping_preference": "NO_SHIPPING",
                    "user_action": "PAY_NOW",
                    "return_url": "http://localhost:8000/accounts/profile",
                    "cancel_url": "https://example.com/returnUrl"
                }
            }
        },
        "purchase_units": [
            {"invoice_id": f"{invoice_prefix}-{commission.uuid}",
             "amount": {
                 "currency_code": "USD",
                 "value": f"{amount}",
                 "breakdown": {
                     "item_total": {
                         "currency_code": "USD",
                         "value": f"{amount}"
                     },
                 }
             },
             }
        ]
    }
    headers = {
        "Content-Type": "application/json",
        "PayPal-Request-Id": f"{uuid_pkg.uuid4()}",
        "Prefer": "return=representation",
        "Authorization": f"{auth_data.get("token_type")} {auth_data.get("access_token")}",
    }

    try:
        response = requests.request("POST", url, data=json.dumps(body), headers=headers, timeout=10)
    except req_execept.ConnectTimeout, req_execept.ConnectionError:
        return JsonResponse(json.dumps({"create_error": "create order request failed."}))

    return JsonResponse(response.json())


@csrf_exempt
def payment_webhook_receiver(request) -> HttpResponse:
    headers = request.headers
    body = json.loads(request.body)
    print("webhook received")

    if headers.get("User-Agent").startswith("PayPal"):
        url = "https://api-m.sandbox.paypal.com/v1/notifications/verify-webhook-signature"
        auth_data = get_paypal_auth_data()
        if not auth_data:
            return JsonResponse(json.dumps({"auth_error": "auth request failed."}))

        webhook_auth_body = {
            "auth_algo": headers.get("PAYPAL-AUTH-ALGO"),
            "cert_url": headers.get("PAYPAL-CERT-URL"),
            "transmission_id": headers.get("PAYPAL-TRANSMISSION-ID"),
            "transmission_sig": headers.get("PAYPAL-TRANSMISSION-SIG"),
            "transmission_time": headers.get("PAYPAL-TRANSMISSION-TIME"),
            "webhook_id": os.getenv("PayPal_Webhook_Id"),
            "webhook_event": {}
        }

        try:
            response = requests.request("POST", url, data=json.dumps(webhook_auth_body), timeout=10, headers={
                "Content-Type": "application/json",
                "Authorization": f"{auth_data.get("token_type")} {auth_data.get("access_token")}"
            })

        except req_execept.ConnectTimeout, req_execept.ConnectionError:
            print("Failed")
            return HttpResponse("", 500)

        if not response.json().get("verification_status") == "SUCCESS":
            print("Failed")
            return HttpResponse("", 401)

        payment = body
        status: str = payment.get("resource", {}).get("status")

        raw_comm_id: str = payment.get("resource", {}).get("invoice_id")
        comm_id: str = raw_comm_id.removeprefix("deposit").removeprefix("full")

    elif headers.get("X-Meli-Trace-Bu").startswith("mercadopago"):
        try:
            secret = os.getenv("WEBHOOK_SECRET_KEY")
            WebhookSignatureValidator.validate(
                headers.get("x-signature"),
                headers.get("x-request-id"),
                body.get("data").get("id"),
                secret,
            )
        except InvalidWebhookSignatureError:
            print("Failed")
            return HttpResponse("", 401)

        payment_id = body.get("data", {}).get("id")
        sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
        request_options = mercadopago.config.RequestOptions()

        payment = sdk.payment().get(payment_id, request_options)
        status = payment.get("response", {}).get("status")

        raw_comm_id: str = payment.get("response", {}).get("external_reference")
        comm_id: str = raw_comm_id.removeprefix("comm-").removesuffix("-deposit").removesuffix("-full")

    else:
        print("Failed")
        return HttpResponse("", 401)

    if status in {"approved", "COMPLETED"}:
        try:
            commission = Commission.objects.get(uuid=comm_id)
        except Commission.DoesNotExist:
            print("Failed")
            return HttpResponse("", 404)

        if commission.stage not in ["waiting_deposit_payment", "waiting_full_payment"]:
            return HttpResponse("", 200)

        prev_comm_stage = commission.stage
        commission.stage = "sketch" if prev_comm_stage == "waiting_deposit_payment" else "finished"
        try:
            with transaction.atomic():
                if prev_comm_stage == "waiting_full_payment":
                    commission.finished_at = timezone.now()
                    final_image_object = commission.progress_image.get(stage=commission.final_stage)
                    final_image = ContentFile(final_image_object.image.read(), final_image_object.image.name)
                    commission.progress_image.all().delete()
                    commission.messages.all().delete()
                    commission.reference_images.all().delete()
                    ProgressImage(commission=commission, image=final_image, stage=commission.final_stage).save()

                commission.save()

                if prev_comm_stage == "waiting_deposit_payment":
                    sys_message = Message(content=_(commission.get_stage_display()), commission=commission).save()

                artist_key = "deposit_confirmation_artist" if prev_comm_stage == "waiting_deposit_payment" else "full_confirmation_artist"
                client_key = "deposit_confirmation" if prev_comm_stage == "waiting_deposit_payment" else "full_confirmation"

                send_notification_to_artist(key=artist_key, level="SUCCESS", context={"uuid": str(commission.uuid)})
                send_notification_to_client(commission.user, client_key, "SUCCESS",
                                            context={"uuid": str(commission.uuid)})
        except IntegrityError:
            print("Failed")
            return HttpResponse("", 500)

    print("Success")
    return HttpResponse("", 200)


def commission_choice(request) -> HttpResponse:
    return render(request, "commissions/comms_choice.html", context={"landing_data": get_landing_data()})


class CommissionFormView(View):
    def comms_form_details_required_inverter(self, form: CommissionForm, set_status: bool) -> CommissionForm:
        for field_name, field_obj in zip(form.fields, form.fields.values()):
            if field_name in ["description", "reference_images", "contact_social", "contact_username"]:
                field_obj.required = set_status
        return form

    def get(self, request) -> HttpResponse:
        form = forms.CommissionForm()
        form_data: dict = request.session.pop("form_data", None)
        category = request.GET.get("category", "")
        if category not in ["character", "landscape", "object"]:
            return redirect("comms_choice")

        form = set_required_fields_based_on_category(form, category)
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

    def post(self, request) -> HttpResponse:
        form = forms.CommissionForm(request.POST, request.FILES)
        category = request.POST.get("category", None)
        if category not in ["character", "landscape", "object"]:
            return redirect("comms_choice")

        optional_details_form = self.comms_form_details_required_inverter(form, False)
        form = optional_details_form
        form = set_required_fields_based_on_category(form, category)

        context = {
            "landing_data": get_landing_data(),
            "form": form,
        }

        if form.is_valid():
            form_data: dict = form.cleaned_data

            prices: dict = CALCULATORS[category](form_data)
            if not prices:
                context["category"] = form.cleaned_data["category"]
                messages.error(request,
                               _("Ocorreu um erro com a sua solicitação, por favor verifique os campos do formulário e tente novamente"))
                return render(request, "commissions/comms_form_base.html", context=context)

            request.session["calculated_prices"] = prices

            required_details_form = self.comms_form_details_required_inverter(form, True)
            form = required_details_form
            context["calculated_prices"] = prices
            context["category"] = category
            context["form"] = form

            return render(request, "commissions/comms_form_base.html", context=context)

        else:
            context["category"] = form.cleaned_data["category"]
            messages.error(request,
                           _("Ocorreu um erro com a sua solicitação, por favor verifique os campos do formulário e tente novamente"))
            return render(request, "commissions/comms_form_base.html", context=context)


@login_required()
def commission_confirmation(request) -> HttpResponse | HttpResponseRedirect:
    def get_human_readable_names(fields, form_data: dict) -> dict[str, str]:
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
        if category not in ["character", "landscape", "object"]:
            return redirect("comms_choice")

        form = set_required_fields_based_on_category(form, category)
        request.session["form_data"] = request.POST.dict()

        context = {
            "landing_data": get_landing_data()
        }

        if form.is_valid():
            form_data = form.cleaned_data
            form_readable_names = get_human_readable_names(form.fields.values(), form_data)

            prices: dict = CALCULATORS[category](form_data)
            if not prices:
                context["category"] = form.cleaned_data["category"]
                messages.error(request,
                               _("Ocorreu um erro com a sua solicitação, por favor verifique os campos do formulário e tente novamente"))
                return render(request, "commissions/comms_form_base.html", context=context)

            context["calculated_prices"] = prices
            request.session.delete("calculated_prices")

            images = request.FILES.getlist("reference_images", [])
            images_uuids: list[str] = []
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
def commission_success(request) -> HttpResponse | HttpResponseRedirect:
    if request.method == "POST" and get_landing_data().comms_status == True and (
            request.session.get("form_data", None) is not None):

        form = forms.CommissionForm(request.session.pop("form_data"))
        reference_images_uuids: list[str] = request.session.pop("reference_images_uuids", [])

        if form.is_valid():
            form_data = form.cleaned_data
            prices: dict = CALCULATORS[form_data["category"]](form_data)
            if not prices:
                message = _(
                    "Ocorreu um erro com a sua solicitação, por favor verifique os campos do formulário e tente novamente"
                )

                messages.error(request, message)
                return redirect(f"{reverse_lazy("comms_form")}?{urlencode({"category": form_data.get("category")})}")

            try:
                with transaction.atomic():
                    commission: Commission = form.save(commit=False)
                    commission.user = request.user
                    commission.stage = "waiting_confirmation"
                    commission.price_brl = prices["brl"]
                    commission.price_usd = prices["usd"]
                    commission.save()

                    if reference_images_uuids:
                        for uuid in reference_images_uuids:
                            image = models.ReferenceImage.objects.get(uuid=uuid)
                            image.commission = commission
                            image.is_temp = False
                            image.save()

                    artist_notification_context = {"client_name": request.user.username,
                                                   "price_brl": commission.price_brl,
                                                   "price_usd": commission.price_usd}

                    send_notification_to_client(client=request.user, key="order_success", level="SUCCESS", context={})
                    send_notification_to_artist(key="new_order", level="MESSAGE", context=artist_notification_context)
                    decrease_comms_slots()
            except IntegrityError:
                message = _(
                    "Ocorreu um erro com a sua solicitação, por favor tente novamente"
                )

                messages.error(request, message)
                return redirect(f"{reverse_lazy("comms_form")}?{urlencode({"category": form_data.get("category")})}")

            return render(request, "commissions/comms_success.html", context={"landing_data": get_landing_data()})

        else:
            return redirect("comms_choice")
    else:
        return redirect("comms_choice")
