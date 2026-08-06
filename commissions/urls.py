from django.urls import path

from . import views

urlpatterns = [
    path("choice", views.commission_choice, name="comms_choice"),
    path("form", views.CommissionFormView.as_view(), name="comms_form"),
    path("confirmation", views.commission_confirmation, name="comms_confirmation"),
    path("success", views.commission_success, name="comms_success"),
    path("payment-webhook-receiver", views.payment_webhook_receiver, name="payment_webhook_receiver"),
    path("paypal-create-order", views.paypal_create_order, name="paypal_create_order"),
    path("paypal-capture-order", views.paypal_capture_order, name="paypal_capture_order"),
]
